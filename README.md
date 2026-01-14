# Enterprise AI Operations Hub

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)

**A production-grade, full-stack AI platform that automates project intelligence, engineering reporting, and enterprise knowledge management through autonomous multi-agent workflows.**

[Quick Start](#quick-start) · [Architecture](#architecture) · [Features](#features) · [API Docs](#api-documentation) · [Demo](#demo-accounts)

</div>

---

## What This Builds

Enterprise engineering teams lose thousands of hours per year manually compiling sprint summaries, writing status reports, triaging risks, and searching for institutional knowledge spread across Jira, GitHub, Confluence, and Slack. This platform eliminates that toil by deploying autonomous AI agents that continuously monitor your engineering ecosystem and generate actionable intelligence.

**The platform connects to your existing tools → aggregates and embeds all data → runs a 5-agent LangGraph pipeline → produces executive reports, sprint summaries, risk assessments, and action items — all with human-in-the-loop approval gates.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    React 18 + TypeScript + Tailwind CSS                      │
│         TanStack Query v5 · Zustand · Recharts · Radix UI · Vite             │
│                                                                              │
│  Overview  │  Executive  │  Projects  │  Knowledge  │  Workflows  │  Reports  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ REST API (JWT + RBAC)
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                      FastAPI  ·  Pydantic v2  ·  asyncpg                     │
│                                                                              │
│  /auth  /projects  /reports  /knowledge  /agents  /analytics  /users        │
│  Rate limiting · GZip · Request timing · Global error handling               │
└──────┬──────────────────────────────────────────────────────────────────────┘
       │
       ├──── SQLAlchemy async ORM ────► PostgreSQL 16 (15 tables)
       │
       ├──── Redis async client ──────► Redis 7 (cache · rate-limit · pub/sub)
       │
       ├──── Qdrant client ──────────► Qdrant (knowledge embeddings · RAG)
       │
       └──── LangGraph Orchestrator ──────────────────────────────────────────┐
                                                                              │
          ┌─────────────────────────────────────────────────────────────────┐ │
          │                    5-Agent Pipeline                              │ │
          │                                                                  │ │
          │  [1] DataAggregation  ──►  Jira + GitHub + Confluence + Slack    │ │
          │         │                                                        │ │
          │         ▼                                                        │ │
          │  [2] ProjectHealth    ──►  Claude: velocity · debt · confidence  │ │
          │         │                                                        │ │
          │         ▼                                                        │ │
          │  [3] RiskDetection    ──►  Claude: threats · blockers · scoring  │ │
          │         │                                                        │ │
          │         ▼                                                        │ │
          │  [4] ExecutiveReporting ► Claude: audience-targeted Markdown     │ │
          │         │                                                        │ │
          │         ▼                                                        │ │
          │  [5] ActionItems      ──►  Claude: owners · deadlines · priority │ │
          └─────────────────────────────────────────────────────────────────┘ │
                                                                              │
       ┌──────────────────────────────────────────────────────────────────────┘
       │
       └──── Celery + Redis ──────────► Async task queue · beat scheduler
```

---

## Features

### AI Agent Pipeline
- **5-node LangGraph StateGraph** running agents sequentially with shared typed state
- **DataAggregationAgent** — concurrently fetches Jira tickets, GitHub PRs/commits, Confluence docs, and Slack messages using `asyncio.gather`; falls back to rich demo data when integrations aren't configured
- **ProjectHealthAgent** — sends structured prompts to Claude (claude-sonnet-4-6) to compute `health_score`, `confidence_score`, `velocity_trend`, `sprint_success_likelihood`, `delivery_forecast`, and `technical_debt_level`
- **RiskDetectionAgent** — identifies risks with `severity`, `probability`, `impact`, `risk_score`, `mitigation`, and `ai_reasoning` per item
- **ExecutiveReportingAgent** — three separate system prompts tailored for executive / manager / engineer audiences, generating 7-section Markdown reports
- **ActionItemAgent** — generates 4–8 prioritized action items with `owner_role`, `estimated_hours`, `due_date`, and `reasoning`

### RAG Knowledge Base
- Ingest documents from Jira, GitHub, Confluence, and Slack → chunk → embed with OpenAI `text-embedding-3-small` (1536 dims) → store in Qdrant with cosine similarity
- SHA-256 content deduplication prevents re-ingesting unchanged documents
- Query endpoint retrieves top-K relevant chunks → passes to Claude for grounded answer generation → returns answer + cited sources with relevance scores

### Enterprise Integrations
- **Jira REST v3** — fetch project tickets, sprint metadata, blocker counts
- **GitHub REST v3** — PRs, commits, issues, deployment events
- **Confluence REST** — space pages with HTML stripping and label filtering
- **Slack API** — conversation history, bot message posting
- **Plugin architecture** — `BaseConnector` ABC makes it trivial to add new integrations

### Security & Auth
- JWT access tokens (30 min) + refresh tokens (7 day) with automatic rotation
- **5 RBAC roles**: `admin` / `manager` / `engineer` / `executive` / `viewer`
- Per-endpoint permission guards via FastAPI dependency injection (`require_permission`, `require_role`)
- Redis-backed rate limiting with per-IP sliding window
- Full audit log on every state-changing API call

### Human-in-the-Loop
- `AIApproval` model routes high-stakes AI actions through a human review queue
- States: `pending` → `approved` / `rejected` / `expired`
- Frontend approval UI with approve/reject buttons on the Reports page

### Observability
- `TokenUsage` table tracks prompt tokens, completion tokens, and estimated USD cost per agent call
- `PromptVersion` table maintains a full history of LLM prompt changes
- Per-request timing middleware logs latency on every API call
- Celery Flower dashboard for task monitoring

### Automated Scheduling
- `sync-all-integrations` — hourly data sync from all configured integrations
- `generate-daily-health-reports` — nightly AI health report for every active project
- `cleanup-expired-approvals` — hourly expiry of stale approval requests

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | SPA with fast HMR |
| **Styling** | Tailwind CSS v3 + Radix UI | Dark theme design system |
| **Data fetching** | TanStack Query v5 | Caching, polling, optimistic updates |
| **State** | Zustand + persist | JWT auth with localStorage sync |
| **Charts** | Recharts | Area, Bar, Pie, Radar charts |
| **Backend** | FastAPI + asyncio | Async REST API |
| **ORM** | SQLAlchemy 2 async + asyncpg | Non-blocking PostgreSQL |
| **Migrations** | Alembic | Schema version control |
| **Validation** | Pydantic v2 | Request/response serialization |
| **AI Orchestration** | LangGraph + LangChain | Multi-agent state machine |
| **Primary LLM** | Anthropic Claude (claude-sonnet-4-6) | Reasoning, generation, analysis |
| **Embeddings** | OpenAI text-embedding-3-small | 1536-dim document embeddings |
| **Vector DB** | Qdrant | Cosine similarity search |
| **Cache / Queue** | Redis 7 | Rate limiting, Celery broker, pub/sub |
| **Task Queue** | Celery | Async AI tasks + scheduled jobs |
| **Database** | PostgreSQL 16 | Primary data store (15 tables) |
| **Containerization** | Docker + Docker Compose | One-command local stack |
| **Orchestration** | Kubernetes + Kustomize | Production deployment |
| **CI/CD** | GitHub Actions | Lint → test → build → push → deploy |

---

## Quick Start

### Option 1 — Docker Compose (recommended)

**Prerequisites**: Docker Desktop

```bash
git clone https://github.com/TejasRamanujam/enterprise-ai-ops-hub.git
cd enterprise-ai-ops-hub
cp .env.example .env
```

Edit `.env` and add at minimum:
```bash
ANTHROPIC_API_KEY=sk-ant-...    # Required for agent reasoning
OPENAI_API_KEY=sk-...           # Required for RAG embeddings
```

```bash
docker-compose up -d
```

The first boot runs Alembic migrations and seeds demo data automatically. Services:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Celery Flower | http://localhost:5555 |
| Qdrant UI | http://localhost:6333/dashboard |

---

### Option 2 — Local Development

**Prerequisites**: Python 3.11+, Node 20+, PostgreSQL 16, Redis 7, Qdrant

#### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Apply migrations and seed demo data
alembic upgrade head
python scripts/seed_data.py

# Start API server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev    # → http://localhost:5173
```

#### Background workers (optional — needed for scheduled reports)

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Demo Accounts

The seed script creates these users:

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Admin | admin@company.com | Admin123! | Full platform access |
| Manager | manager@company.com | Manager123! | Projects, reports, workflows |
| Executive | executive@company.com | Executive123! | Executive dashboard, reports |
| Engineer | engineer1@company.com | Engineer123! | Projects, knowledge base |
| Engineer | engineer2@company.com | Engineer123! | Projects, knowledge base |

---

## Demo Projects

Four pre-seeded projects with realistic sprint data, risks, and metrics:

| Key | Name | Description |
|-----|------|-------------|
| CIP | Customer Identity Platform | OAuth2 + MFA migration — 14 engineers |
| DAP | Data Analytics Pipeline | Real-time ML data platform — 8 engineers |
| MAR | Mobile App Rewrite | iOS/Android React Native — 11 engineers |
| INFRA | Infrastructure Modernization | K8s migration, IaC — 6 engineers |

---

## API Documentation

Interactive Swagger UI at `http://localhost:8000/docs`. Full OpenAPI spec at `/openapi.json`.

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "Admin123!"}'

# Returns: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Run AI Workflow

```bash
curl -X POST http://localhost:8000/api/v1/agents/workflow/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "<uuid>", "agents": ["data_aggregation", "project_health", "risk_detection", "executive_reporting", "action_items"]}'

# Returns: { "task_id": "...", "status": "queued" }
```

### Query Knowledge Base

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the current blockers for CIP?", "include_citations": true}'
```

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Authenticate, receive JWT |
| POST | `/api/v1/auth/refresh` | Rotate access token |
| GET | `/api/v1/projects/portfolio` | Portfolio-level analytics |
| GET | `/api/v1/projects/{id}/risks` | Project risk register |
| POST | `/api/v1/reports/generate` | Trigger AI report (async) |
| POST | `/api/v1/reports/meetings/analyze` | Extract insights from transcript |
| POST | `/api/v1/knowledge/query` | RAG-powered Q&A |
| POST | `/api/v1/agents/workflow/run` | Run LangGraph pipeline |
| GET | `/api/v1/agents/tasks/{task_id}` | Poll Celery task status |
| GET | `/api/v1/analytics/overview` | Platform-wide metrics |
| GET | `/api/v1/analytics/risk-heatmap` | Risk matrix data |
| GET | `/api/v1/agents/token-usage` | AI cost breakdown by agent |

---

## Database Schema

15 tables across 4 domains:

```
users                    # Auth + RBAC
├── audit_logs           # Immutable action log
├── ai_approvals         # Human-in-the-loop queue
├── token_usage          # Per-agent LLM cost tracking
└── prompt_versions      # LLM prompt change history

projects
├── sprints
├── tickets
├── project_metrics
└── risks

reports
└── meeting_transcripts

knowledge_sources
├── knowledge_chunks      # Qdrant-linked document chunks
├── knowledge_queries     # Query + answer audit trail
└── integrations          # Connector config per project
```

---

## LangGraph Agent Pipeline

Each workflow invocation creates an isolated `AgentState` TypedDict that flows through 5 nodes:

```python
AgentState = {
    "project_id": str,
    "user_id": str,
    "messages": list,
    "context": dict,      # Raw data from integrations
    "results": dict,      # Structured output from each agent
    "errors": list,
    "current_step": str,
    "completed_steps": list[str]
}
```

The orchestrator uses LangGraph's `StateGraph`:

```python
workflow = StateGraph(AgentState)
workflow.add_node("data_aggregation", data_agent.run)
workflow.add_node("project_health",   health_agent.run)
workflow.add_node("risk_detection",   risk_agent.run)
workflow.add_node("executive_reporting", report_agent.run)
workflow.add_node("action_items",     action_agent.run)

workflow.set_entry_point("data_aggregation")
workflow.add_edge("data_aggregation",    "project_health")
workflow.add_edge("project_health",      "risk_detection")
workflow.add_edge("risk_detection",      "executive_reporting")
workflow.add_edge("executive_reporting", "action_items")
workflow.add_edge("action_items", END)
```

Results are persisted to PostgreSQL (Report + Risk records) and pushed to Redis pub/sub for real-time frontend updates.

---

## Project Structure

```
enterprise-ai-ops-hub/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── base.py                      # AgentState, BaseAgent ABC
│   │   │   ├── data_aggregation/agent.py    # Integration data collector
│   │   │   ├── project_health/agent.py      # Claude health analyzer
│   │   │   ├── risk_detection/agent.py      # Claude risk identifier
│   │   │   ├── executive_reporting/agent.py # Audience-targeted reporter
│   │   │   ├── action_items/agent.py        # Prioritized task generator
│   │   │   └── orchestrator/workflow.py     # LangGraph StateGraph
│   │   │
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py          # JWT auth + registration
│   │   │   ├── projects.py      # Project CRUD + sprints + risks
│   │   │   ├── reports.py       # Report generation + approvals
│   │   │   ├── knowledge.py     # RAG query + sync
│   │   │   ├── agents.py        # Workflow execution + task polling
│   │   │   └── analytics.py     # Portfolio + audit metrics
│   │   │
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings + lru_cache
│   │   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   │   ├── security.py      # JWT, RBAC, dependency factories
│   │   │   └── redis_client.py  # Async Redis, rate limit, pub/sub
│   │   │
│   │   ├── integrations/
│   │   │   ├── base/connector.py     # BaseConnector ABC
│   │   │   ├── jira/connector.py     # Jira REST v3
│   │   │   ├── github/connector.py   # GitHub REST v3
│   │   │   ├── confluence/connector.py
│   │   │   └── slack/connector.py
│   │   │
│   │   ├── models/              # SQLAlchemy ORM (15 tables)
│   │   ├── schemas/             # Pydantic v2 request/response models
│   │   ├── services/            # Business logic layer
│   │   ├── tasks/               # Celery workers + beat schedule
│   │   └── main.py              # FastAPI app + middleware + lifespan
│   │
│   ├── migrations/              # Alembic DDL migrations
│   └── scripts/seed_data.py     # Demo users + projects + data
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── layout/AppLayout.tsx     # Sidebar + topbar shell
│       │   └── ui/                      # HealthBadge, StatCard
│       │
│       ├── pages/
│       │   ├── auth/LoginPage.tsx
│       │   ├── dashboard/OverviewDashboard.tsx
│       │   ├── dashboard/ExecutiveDashboard.tsx
│       │   ├── projects/ProjectsPage.tsx
│       │   ├── projects/ProjectDetailPage.tsx
│       │   ├── knowledge/KnowledgePage.tsx
│       │   ├── reports/ReportsPage.tsx
│       │   ├── workflows/WorkflowsPage.tsx
│       │   └── settings/SettingsPage.tsx
│       │
│       ├── services/api.ts      # Axios + JWT interceptor + all API modules
│       ├── store/auth.ts        # Zustand auth store with persistence
│       └── types/index.ts       # TypeScript interfaces for all domain objects
│
├── infrastructure/
│   └── kubernetes/
│       ├── base/                # Namespace, ConfigMap, Secrets, StatefulSets
│       └── overlays/production/ # Kustomize production patches
│
├── .github/workflows/ci.yml     # Lint → test → build → push → deploy
├── docker-compose.yml           # Full local stack (8 services)
└── .env.example                 # All required environment variables
```

---

## Kubernetes Deployment

```bash
# Apply base manifests
kubectl apply -k infrastructure/kubernetes/base/

# Production overlay (3 backend replicas, 4 Celery workers)
kubectl apply -k infrastructure/kubernetes/overlays/production/

# Monitor rollout
kubectl rollout status deployment/backend -n ai-workflow
kubectl rollout status deployment/frontend -n ai-workflow

# View logs
kubectl logs -f deployment/backend -n ai-workflow
kubectl logs -f deployment/celery-worker -n ai-workflow
```

Update the Ingress host in `infrastructure/kubernetes/base/frontend.yaml` to your domain before deploying.

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push to `main`:

1. **Backend lint** — `ruff check` + `mypy` type checking
2. **Backend tests** — pytest against real PostgreSQL + Redis (Docker services)
3. **Frontend lint** — TypeScript `tsc --noEmit`
4. **Frontend build** — Vite production build
5. **Docker build & push** — multi-stage builds for backend + frontend, pushed to GHCR
6. **Deploy to staging** — `kubectl kustomize` apply + rollout status check

---

## Environment Variables

See `.env.example` for full reference. Minimum required for AI features:

```bash
ANTHROPIC_API_KEY=sk-ant-...   # Claude reasoning in all 5 agents
OPENAI_API_KEY=sk-...          # text-embedding-3-small for RAG
```

The platform runs in **demo mode** without API keys — all agents return rich synthetic data that demonstrates the full UI and data model.

---

## Design Principles

- **Async-first** — every I/O operation (DB, Redis, HTTP, AI) is non-blocking
- **Graceful degradation** — all agents have fallback logic when external APIs are unavailable
- **Typed state** — LangGraph `AgentState` TypedDict enforces data contracts between agents
- **Deduplication** — SHA-256 content hashing prevents duplicate vector embeddings
- **Cost visibility** — every LLM call is logged with token counts and estimated USD
- **Auditability** — every state-changing API action is written to `audit_logs`

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built to demonstrate production-grade AI engineering for enterprise environments.

*Targeting roles at Motorola Solutions · Microsoft · Amazon · Salesforce · Cisco · ServiceNow · Atlassian*

</div>
