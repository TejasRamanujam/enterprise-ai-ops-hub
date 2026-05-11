"""
Seed script: Creates demo users, projects, sprints, risks, and knowledge sources.
Run: python -m scripts.seed_data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.project import Project, Sprint
from app.models.risk import Risk
from app.models.knowledge import KnowledgeSource, Integration
import uuid


USERS = [
    {"email": "admin@aiops.dev", "username": "admin", "full_name": "System Admin", "role": "admin", "password": "Admin123!"},
    {"email": "em@aiops.dev", "username": "eng_manager", "full_name": "Alex Chen", "role": "manager", "password": "Manager123!", "title": "Engineering Manager"},
    {"email": "pm@aiops.dev", "username": "proj_manager", "full_name": "Sarah Kim", "role": "manager", "password": "Manager123!", "title": "Project Manager"},
    {"email": "exec@aiops.dev", "username": "executive", "full_name": "Jordan Rivera", "role": "executive", "password": "Exec123!", "title": "VP Engineering"},
    {"email": "dev1@aiops.dev", "username": "alice_dev", "full_name": "Alice Johnson", "role": "engineer", "password": "Dev123!", "title": "Senior Software Engineer"},
    {"email": "dev2@aiops.dev", "username": "bob_dev", "full_name": "Bob Smith", "role": "engineer", "password": "Dev123!", "title": "Software Engineer"},
]

PROJECTS = [
    {
        "name": "Customer Identity Platform", "key": "CIP", "status": "active",
        "description": "Next-generation customer authentication and identity management platform",
        "health_score": "yellow", "health_score_value": 0.65, "confidence_score": 0.72,
        "jira_project_key": "CIP", "github_repo": "company/identity-platform",
        "team_size": 8, "budget": 500000.0, "budget_spent": 210000.0,
    },
    {
        "name": "Data Analytics Pipeline", "key": "DAP", "status": "active",
        "description": "Real-time data ingestion, transformation and analytics platform",
        "health_score": "green", "health_score_value": 0.88, "confidence_score": 0.91,
        "jira_project_key": "DAP", "github_repo": "company/analytics-pipeline",
        "team_size": 6, "budget": 300000.0, "budget_spent": 95000.0,
    },
    {
        "name": "Mobile App Rewrite", "key": "MAR", "status": "at_risk",
        "description": "Complete rewrite of mobile application using React Native",
        "health_score": "red", "health_score_value": 0.38, "confidence_score": 0.51,
        "jira_project_key": "MAR", "github_repo": "company/mobile-app",
        "team_size": 5, "budget": 250000.0, "budget_spent": 198000.0,
    },
    {
        "name": "Infrastructure Modernization", "key": "INFRA", "status": "active",
        "description": "Migration to Kubernetes and cloud-native architecture",
        "health_score": "green", "health_score_value": 0.82, "confidence_score": 0.85,
        "jira_project_key": "INFRA", "github_repo": "company/infrastructure",
        "team_size": 4,
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding users...")
        user_map = {}
        for u in USERS:
            user = User(
                id=str(uuid.uuid4()),
                email=u["email"],
                username=u["username"],
                full_name=u["full_name"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                title=u.get("title"),
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            user_map[u["username"]] = user
        await db.flush()
        print(f"  Created {len(USERS)} users")

        print("Seeding projects...")
        project_map = {}
        for p in PROJECTS:
            project = Project(
                id=str(uuid.uuid4()),
                owner_id=user_map["eng_manager"].id,
                **{k: v for k, v in p.items()},
            )
            db.add(project)
            project_map[p["key"]] = project
        await db.flush()
        print(f"  Created {len(PROJECTS)} projects")

        print("Seeding sprints...")
        for key, proj in project_map.items():
            for i in range(1, 4):
                sprint = Sprint(
                    id=str(uuid.uuid4()),
                    project_id=proj.id,
                    name=f"Sprint {i + 10}",
                    sprint_number=i + 10,
                    status="completed" if i < 3 else "active",
                    planned_points=34 + (i * 2),
                    completed_points=int((34 + i * 2) * (0.85 if i < 3 else 0.32)),
                    velocity=float(30 + i),
                    completion_rate=0.85 if i < 3 else 0.32,
                )
                db.add(sprint)
        await db.flush()
        print("  Created sprints")

        print("Seeding risks...")
        risk_templates = [
            ("Database migration dependency", "Technical dependency on DBA team approval causing sprint blocker", "technical", "high", 0.8, 0.7),
            ("Resource constraint on mobile team", "Key mobile developer out for 2 weeks reducing capacity by 40%", "resource", "high", 0.9, 0.65),
            ("Third-party API deprecation", "Payment provider deprecating v1 API in Q3, requires urgent migration", "external", "critical", 1.0, 0.9),
            ("Security audit scope expansion", "Compliance team added 12 new requirements to security audit", "scope", "medium", 0.7, 0.5),
            ("Code coverage below threshold", "Current 78% coverage insufficient for production deployment gate", "technical", "medium", 0.6, 0.4),
        ]
        for proj in project_map.values():
            for i, (title, desc, cat, sev, prob, imp) in enumerate(risk_templates[:3]):
                risk = Risk(
                    id=str(uuid.uuid4()),
                    project_id=proj.id,
                    title=title,
                    description=desc,
                    category=cat,
                    severity=sev,
                    probability=prob,
                    impact=imp,
                    risk_score=round(prob * imp * 10, 1),
                    status="open",
                    is_ai_generated=True,
                    ai_confidence=0.87,
                    mitigation=f"Immediate escalation and remediation plan for: {title}",
                )
                db.add(risk)
        await db.flush()
        print("  Created risks")

        print("Seeding knowledge sources...")
        sources = [
            KnowledgeSource(id=str(uuid.uuid4()), name="Jira Issues", source_type="jira", is_active=True, document_count=247),
            KnowledgeSource(id=str(uuid.uuid4()), name="GitHub PRs", source_type="github", is_active=True, document_count=183),
            KnowledgeSource(id=str(uuid.uuid4()), name="Confluence Docs", source_type="confluence", is_active=True, document_count=94),
            KnowledgeSource(id=str(uuid.uuid4()), name="Slack Messages", source_type="slack", is_active=True, document_count=1203),
        ]
        for s in sources:
            db.add(s)

        integrations = [
            Integration(id=str(uuid.uuid4()), name="Jira Cloud", integration_type="jira", is_enabled=False, sync_count=0),
            Integration(id=str(uuid.uuid4()), name="GitHub Enterprise", integration_type="github", is_enabled=False, sync_count=0),
            Integration(id=str(uuid.uuid4()), name="Confluence Cloud", integration_type="confluence", is_enabled=False, sync_count=0),
            Integration(id=str(uuid.uuid4()), name="Slack Workspace", integration_type="slack", is_enabled=False, sync_count=0),
        ]
        for i in integrations:
            db.add(i)

        await db.commit()
        print("  Created knowledge sources and integrations")
        print("\nSeed data complete!")
        print("\nDemo credentials:")
        for u in USERS:
            print(f"  {u['role']:12} {u['email']:30} password: {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
