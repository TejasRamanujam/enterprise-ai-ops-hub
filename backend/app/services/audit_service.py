from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timezone, timedelta
import structlog

from app.models.audit import AuditLog, AIApproval, TokenUsage

logger = structlog.get_logger()


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            status=status,
            error_message=error_message,
        )
        self.db.add(entry)
        await self.db.flush()
        logger.info("audit_log", action=action, resource=resource_type, user=user_id)
        return entry

    async def create_approval(
        self,
        agent_name: str,
        action_type: str,
        description: str,
        proposed_data: Optional[dict] = None,
        ai_reasoning: Optional[str] = None,
        confidence_score: Optional[float] = None,
        expires_in_hours: int = 24,
    ) -> AIApproval:
        approval = AIApproval(
            agent_name=agent_name,
            action_type=action_type,
            description=description,
            proposed_data=proposed_data,
            ai_reasoning=ai_reasoning,
            confidence_score=confidence_score,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        self.db.add(approval)
        await self.db.flush()
        return approval

    async def process_approval(
        self, approval_id: str, user_id: str, decision: str, notes: Optional[str] = None
    ) -> Optional[AIApproval]:
        result = await self.db.execute(
            select(AIApproval).where(AIApproval.id == approval_id)
        )
        approval = result.scalar_one_or_none()
        if not approval:
            return None
        approval.status = decision
        approval.approver_id = user_id
        approval.approver_notes = notes
        approval.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.log(
            action=f"ai_approval_{decision}",
            resource_type="ai_approval",
            resource_id=approval_id,
            user_id=user_id,
            details={"decision": decision, "agent": approval.agent_name},
        )
        return approval

    async def get_pending_approvals(self) -> list:
        result = await self.db.execute(
            select(AIApproval)
            .where(AIApproval.status == "pending")
            .order_by(AIApproval.created_at.desc())
        )
        return list(result.scalars().all())

    async def record_token_usage(
        self,
        agent_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        operation: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> TokenUsage:
        total = prompt_tokens + completion_tokens
        cost = self._estimate_cost(model, prompt_tokens, completion_tokens)
        usage = TokenUsage(
            agent_name=agent_name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            estimated_cost_usd=cost,
            operation=operation,
            project_id=project_id,
        )
        self.db.add(usage)
        await self.db.flush()
        return usage

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = {
            "gpt-4o": (0.0025, 0.01),
            "gpt-4o-mini": (0.00015, 0.0006),
            "claude-sonnet-4-6": (0.003, 0.015),
            "claude-haiku-4-5": (0.00025, 0.00125),
        }
        rates = pricing.get(model, (0.002, 0.008))
        return (prompt_tokens / 1000 * rates[0]) + (completion_tokens / 1000 * rates[1])
