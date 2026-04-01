from abc import ABC, abstractmethod
from typing import Any, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger()


class AgentState(TypedDict):
    project_id: Optional[str]
    user_id: Optional[str]
    messages: list
    context: dict
    results: dict
    errors: list
    current_step: str
    completed_steps: list


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    token_usage: dict = field(default_factory=dict)
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    name: str = "base_agent"
    description: str = ""

    def __init__(self):
        self.logger = structlog.get_logger().bind(agent=self.name)

    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        pass

    def log_start(self, project_id: Optional[str] = None):
        self.logger.info("agent_started", project_id=project_id)

    def log_complete(self, result_summary: str = ""):
        self.logger.info("agent_completed", summary=result_summary)

    def log_error(self, error: str):
        self.logger.error("agent_error", error=error)
