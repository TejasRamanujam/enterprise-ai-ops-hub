from abc import ABC, abstractmethod
from typing import Optional, Any
import structlog

logger = structlog.get_logger()


class BaseConnector(ABC):
    name: str = "base"
    integration_type: str = "base"

    def __init__(self):
        self.logger = structlog.get_logger().bind(connector=self.name)

    @abstractmethod
    async def test_connection(self) -> bool:
        pass

    @abstractmethod
    async def fetch_data(self, **kwargs) -> dict:
        pass

    async def sync(self, integration_id: str) -> dict:
        self.logger.info("sync_started", integration_id=integration_id)
        try:
            data = await self.fetch_data()
            self.logger.info("sync_completed", integration_id=integration_id, records=len(data))
            return {"status": "success", "data": data}
        except Exception as e:
            self.logger.error("sync_failed", integration_id=integration_id, error=str(e))
            return {"status": "error", "error": str(e)}
