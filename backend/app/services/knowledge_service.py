from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)
from openai import AsyncOpenAI
from typing import Optional, List
import hashlib
import uuid
import time
import structlog

from app.models.knowledge import KnowledgeChunk, KnowledgeSource, KnowledgeQuery
from app.schemas.knowledge import KnowledgeQueryRequest, KnowledgeQueryResponse, CitationResponse
from app.core.config import settings

logger = structlog.get_logger()


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._qdrant: Optional[QdrantClient] = None
        self._openai: Optional[AsyncOpenAI] = None

    @property
    def qdrant(self) -> QdrantClient:
        if not self._qdrant:
            self._qdrant = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        return self._qdrant

    @property
    def openai(self) -> AsyncOpenAI:
        if not self._openai:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    async def ensure_collection(self) -> None:
        collections = self.qdrant.get_collections().collections
        names = [c.name for c in collections]
        if settings.QDRANT_COLLECTION_NAME not in names:
            self.qdrant.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("qdrant_collection_created", name=settings.QDRANT_COLLECTION_NAME)

    async def embed_text(self, text: str) -> List[float]:
        response = await self.openai.embeddings.create(
            input=text,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
        return response.data[0].embedding

    async def ingest_chunk(
        self,
        source_id: str,
        title: str,
        content: str,
        document_id: Optional[str] = None,
        document_url: Optional[str] = None,
        author: Optional[str] = None,
        project_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> KnowledgeChunk:
        await self.ensure_collection()

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing = await self.db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.content_hash == content_hash)
        )
        if existing.scalar_one_or_none():
            logger.debug("chunk_skipped_duplicate", content_hash=content_hash)
            return existing.scalar_one_or_none()

        embedding = await self.embed_text(f"{title}\n\n{content}")
        qdrant_id = str(uuid.uuid4())

        payload = {
            "source_id": source_id,
            "title": title,
            "content": content[:500],
            "document_id": document_id,
            "author": author,
            "project_key": project_key,
            "tags": tags or [],
        }
        if metadata:
            payload.update(metadata)

        self.qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[PointStruct(id=qdrant_id, vector=embedding, payload=payload)],
        )

        chunk = KnowledgeChunk(
            source_id=source_id,
            qdrant_id=qdrant_id,
            title=title,
            content=content,
            content_hash=content_hash,
            document_id=document_id,
            document_url=document_url,
            author=author,
            project_key=project_key,
            tags=tags,
            metadata_json=metadata,
            is_embedded=True,
        )
        self.db.add(chunk)
        await self.db.flush()
        return chunk

    async def query(
        self, request: KnowledgeQueryRequest, user_id: Optional[str] = None
    ) -> KnowledgeQueryResponse:
        await self.ensure_collection()
        start_ms = int(time.time() * 1000)

        query_embedding = await self.embed_text(request.query)

        search_filter = None
        if request.project_filter:
            search_filter = Filter(
                must=[FieldCondition(key="project_key", match=MatchValue(value=request.project_filter))]
            )

        results = self.qdrant.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=request.top_k,
            query_filter=search_filter,
            with_payload=True,
        )

        context_parts = []
        citations = []
        for r in results:
            payload = r.payload or {}
            chunk_result = await self.db.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.qdrant_id == str(r.id))
            )
            chunk = chunk_result.scalar_one_or_none()
            content = chunk.content if chunk else payload.get("content", "")
            url = chunk.document_url if chunk else None

            context_parts.append(
                f"[Source: {payload.get('title', 'Unknown')}]\n{content}"
            )
            if request.include_citations:
                citations.append(CitationResponse(
                    source_id=payload.get("source_id", ""),
                    source_type=payload.get("source_type", "unknown"),
                    title=payload.get("title", ""),
                    url=url,
                    relevance_score=r.score,
                    excerpt=content[:300],
                    author=payload.get("author"),
                    date=None,
                ))

        context = "\n\n---\n\n".join(context_parts)
        prompt = (
            f"Answer the following question using only the provided context. "
            f"Be specific and cite sources where relevant.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {request.query}\n\nAnswer:"
        )

        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.content[0].text
        total_tokens = response.usage.input_tokens + response.usage.output_tokens
        elapsed = int(time.time() * 1000) - start_ms

        query_record = KnowledgeQuery(
            user_id=user_id,
            query_text=request.query,
            answer=answer,
            sources_used=[c.source_id for c in citations],
            relevance_scores=[c.relevance_score for c in citations],
            token_count=total_tokens,
            response_time_ms=elapsed,
        )
        self.db.add(query_record)
        await self.db.flush()

        return KnowledgeQueryResponse(
            query_id=query_record.id,
            query=request.query,
            answer=answer,
            citations=citations,
            confidence=sum(c.relevance_score for c in citations) / max(len(citations), 1),
            response_time_ms=elapsed,
            token_count=total_tokens,
        )

    async def get_sources(self) -> List[KnowledgeSource]:
        result = await self.db.execute(select(KnowledgeSource).where(KnowledgeSource.is_active == True))
        return list(result.scalars().all())
