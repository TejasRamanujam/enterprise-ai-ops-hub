from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    project_filter: Optional[str] = None
    source_types: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20)
    include_citations: bool = True


class CitationResponse(BaseModel):
    source_id: str
    source_type: str
    title: str
    url: Optional[str]
    relevance_score: float
    excerpt: str
    author: Optional[str]
    date: Optional[datetime]


class KnowledgeQueryResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    citations: List[CitationResponse]
    confidence: float
    response_time_ms: int
    token_count: int


class KnowledgeChunkResponse(BaseModel):
    id: str
    source_id: str
    title: str
    content: str
    document_url: Optional[str]
    author: Optional[str]
    project_key: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSourceResponse(BaseModel):
    id: str
    name: str
    source_type: str
    description: Optional[str]
    is_active: bool
    last_synced_at: Optional[datetime]
    document_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class IntegrationConfig(BaseModel):
    integration_type: str = Field(..., description="jira|github|confluence|slack|calendar")
    name: str
    config: Dict[str, Any] = {}
    credentials: Optional[Dict[str, str]] = None


class IntegrationResponse(BaseModel):
    id: str
    name: str
    integration_type: str
    is_enabled: bool
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    last_error: Optional[str]
    sync_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SyncTriggerResponse(BaseModel):
    task_id: str
    integration_id: str
    status: str
    message: str
