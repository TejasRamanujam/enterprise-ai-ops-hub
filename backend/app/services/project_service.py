from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
import structlog

from app.models.project import Project, Sprint, Ticket, ProjectMetric
from app.models.risk import Risk
from app.schemas.project import ProjectCreate, ProjectUpdate, SprintCreate, PortfolioSummary

logger = structlog.get_logger()


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.key == key))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 50) -> List[Project]:
        result = await self.db.execute(
            select(Project).order_by(Project.updated_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_active(self) -> List[Project]:
        result = await self.db.execute(
            select(Project).where(Project.status == "active").order_by(Project.name)
        )
        return list(result.scalars().all())

    async def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        logger.info("project_created", project_id=project.id, key=project.key)
        return project

    async def update(self, project_id: str, data: ProjectUpdate) -> Optional[Project]:
        project = await self.get_by_id(project_id)
        if not project:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update_health(
        self,
        project_id: str,
        health_score: str,
        health_value: float,
        confidence: float,
    ) -> None:
        project = await self.get_by_id(project_id)
        if project:
            project.health_score = health_score
            project.health_score_value = health_value
            project.confidence_score = confidence
            await self.db.flush()

    async def get_portfolio_summary(self) -> PortfolioSummary:
        projects = await self.get_all(limit=1000)
        risks_result = await self.db.execute(
            select(func.count(Risk.id)).where(Risk.status == "open")
        )
        critical_result = await self.db.execute(
            select(func.count(Risk.id)).where(
                and_(Risk.status == "open", Risk.severity == "critical")
            )
        )

        active = [p for p in projects if p.status == "active"]
        at_risk = [p for p in projects if p.status == "at_risk"]
        on_hold = [p for p in projects if p.status == "on_hold"]
        completed = [p for p in projects if p.status == "completed"]

        scores = [p.health_score_value for p in projects if p.health_score_value is not None]
        avg_health = sum(scores) / len(scores) if scores else 0.0

        confs = [p.confidence_score for p in projects if p.confidence_score is not None]
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        return PortfolioSummary(
            total_projects=len(projects),
            active_projects=len(active),
            at_risk_projects=len(at_risk),
            on_hold_projects=len(on_hold),
            completed_projects=len(completed),
            total_open_risks=risks_result.scalar() or 0,
            critical_risks=critical_result.scalar() or 0,
            avg_health_score=round(avg_health, 2),
            overall_confidence=round(avg_conf, 2),
            projects=projects[:10],
        )

    async def create_sprint(self, data: SprintCreate) -> Sprint:
        sprint = Sprint(**data.model_dump())
        self.db.add(sprint)
        await self.db.flush()
        await self.db.refresh(sprint)
        return sprint

    async def get_sprints(self, project_id: str) -> List[Sprint]:
        result = await self.db.execute(
            select(Sprint)
            .where(Sprint.project_id == project_id)
            .order_by(Sprint.sprint_number.desc())
        )
        return list(result.scalars().all())

    async def get_active_sprint(self, project_id: str) -> Optional[Sprint]:
        result = await self.db.execute(
            select(Sprint).where(
                and_(Sprint.project_id == project_id, Sprint.status == "active")
            )
        )
        return result.scalar_one_or_none()

    async def record_metric(
        self, project_id: str, metric_type: str, value: float, metadata: dict = None
    ) -> ProjectMetric:
        metric = ProjectMetric(
            project_id=project_id,
            metric_type=metric_type,
            metric_value=value,
            metric_metadata=metadata,
        )
        self.db.add(metric)
        await self.db.flush()
        return metric
