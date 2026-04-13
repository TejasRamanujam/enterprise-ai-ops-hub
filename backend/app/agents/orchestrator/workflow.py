from langgraph.graph import StateGraph, END
from typing import Optional, List
import time
import structlog

from app.agents.base import AgentState
from app.agents.data_aggregation.agent import DataAggregationAgent
from app.agents.project_health.agent import ProjectHealthAgent
from app.agents.risk_detection.agent import RiskDetectionAgent
from app.agents.executive_reporting.agent import ExecutiveReportingAgent
from app.agents.action_items.agent import ActionItemAgent

logger = structlog.get_logger()


def create_workflow(
    include_agents: Optional[List[str]] = None,
    audience: str = "manager",
    report_type: str = "weekly",
) -> StateGraph:
    agents_to_run = include_agents or [
        "data_aggregation", "project_health", "risk_detection",
        "executive_reporting", "action_items"
    ]

    data_agent = DataAggregationAgent()
    health_agent = ProjectHealthAgent()
    risk_agent = RiskDetectionAgent()
    report_agent = ExecutiveReportingAgent()
    action_agent = ActionItemAgent()

    graph = StateGraph(AgentState)

    async def run_data_aggregation(state: AgentState) -> AgentState:
        if "data_aggregation" not in agents_to_run:
            state["completed_steps"].append("data_aggregation")
            state["current_step"] = "project_health"
            return state
        return await data_agent.run(state)

    async def run_project_health(state: AgentState) -> AgentState:
        if "project_health" not in agents_to_run:
            state["completed_steps"].append("project_health")
            state["current_step"] = "risk_detection"
            return state
        return await health_agent.run(state)

    async def run_risk_detection(state: AgentState) -> AgentState:
        if "risk_detection" not in agents_to_run:
            state["completed_steps"].append("risk_detection")
            state["current_step"] = "executive_reporting"
            return state
        return await risk_agent.run(state)

    async def run_executive_reporting(state: AgentState) -> AgentState:
        if "executive_reporting" not in agents_to_run:
            state["completed_steps"].append("executive_reporting")
            state["current_step"] = "action_items"
            return state
        state["context"]["audience"] = audience
        state["context"]["report_type"] = report_type
        return await report_agent.run(state)

    async def run_action_items(state: AgentState) -> AgentState:
        if "action_items" not in agents_to_run:
            state["completed_steps"].append("action_items")
            state["current_step"] = "completed"
            return state
        return await action_agent.run(state)

    def route_after_data(state: AgentState) -> str:
        return "project_health"

    def route_after_health(state: AgentState) -> str:
        return "risk_detection"

    def route_after_risk(state: AgentState) -> str:
        return "executive_reporting"

    def route_after_report(state: AgentState) -> str:
        return "action_items"

    def route_after_actions(state: AgentState) -> str:
        return END

    graph.add_node("data_aggregation", run_data_aggregation)
    graph.add_node("project_health", run_project_health)
    graph.add_node("risk_detection", run_risk_detection)
    graph.add_node("executive_reporting", run_executive_reporting)
    graph.add_node("action_items", run_action_items)

    graph.set_entry_point("data_aggregation")
    graph.add_edge("data_aggregation", "project_health")
    graph.add_edge("project_health", "risk_detection")
    graph.add_edge("risk_detection", "executive_reporting")
    graph.add_edge("executive_reporting", "action_items")
    graph.add_edge("action_items", END)

    return graph.compile()


async def run_project_workflow(
    project_id: str,
    user_id: Optional[str] = None,
    include_agents: Optional[List[str]] = None,
    audience: str = "manager",
    report_type: str = "weekly",
    context: Optional[dict] = None,
) -> dict:
    start_time = time.time()
    logger.info("workflow_started", project_id=project_id)

    initial_state: AgentState = {
        "project_id": project_id,
        "user_id": user_id,
        "messages": [],
        "context": context or {},
        "results": {},
        "errors": [],
        "current_step": "data_aggregation",
        "completed_steps": [],
    }

    workflow = create_workflow(
        include_agents=include_agents,
        audience=audience,
        report_type=report_type,
    )

    final_state = await workflow.ainvoke(initial_state)
    elapsed = round((time.time() - start_time) * 1000)

    logger.info(
        "workflow_completed",
        project_id=project_id,
        elapsed_ms=elapsed,
        steps=final_state.get("completed_steps"),
        errors=len(final_state.get("errors", [])),
    )

    return {
        "project_id": project_id,
        "execution_time_ms": elapsed,
        "completed_steps": final_state.get("completed_steps", []),
        "errors": final_state.get("errors", []),
        "results": final_state.get("results", {}),
    }
