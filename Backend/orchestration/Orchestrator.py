import os
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from agents.Data_Manager import DataAgent, UploadResult
from agents.planning_agent import PlanningAgent, PlanningResult
from Services.DataManager.Temp_storage import TempStorage


# =============================================================================
#  STATE — shared across all nodes
# =============================================================================

class OrchestratorState(TypedDict):
    # Input
    filepath:          str
    filename:          str
    extra_constraints: str

    # DataAgent outputs
    upload_result:     Optional[UploadResult]
    upload_id:         Optional[str]
    data_status:       str          # "pending" | "approved" | "rejected"

    # User decision after HITL
    user_wants_planning: bool

    # PlanningAgent outputs
    planning_result:   Optional[PlanningResult]
    schedule_status:   str           # "pending" | "validated" | "rejected"

    # Error
    error:             str


# =============================================================================
#  NODES
# =============================================================================

def node_upload_data(state: OrchestratorState) -> dict:
    """
    Node 1 — DataAgent processes the uploaded file.
    Runs steps: parse -> LLM extract -> transform -> validate -> temp storage.
    """
    print("\n[Orchestrator] Node: upload_data")

    storage = TempStorage()
    agent   = DataAgent(storage)

    result = agent.process_file(
        filepath = state["filepath"],
        filename = state["filename"],
    )

    if not result.success:
        return {
            "upload_result": result,
            "data_status":   "rejected",
            "error":         result.error,
        }

    print(f"  -> Upload ID: {result.upload_id}")
    print(f"  -> {result.total_valid} valid record(s), {result.total_invalid} issue(s).")

    return {
        "upload_result": result,
        "upload_id":     result.upload_id,
        "data_status":   "pending",
        "error":         "",
    }


def node_wait_for_hitl(state: OrchestratorState) -> dict:
    """
    Node 2 — HITL pause: user decides to approve or reject the data.
    In terminal mode: interactive input.
    In API mode: this node is skipped — the /validate endpoint handles it.
    """
    print("\n[Orchestrator] Node: wait_for_hitl")

    result = state.get("upload_result")
    if not result:
        return {"data_status": "rejected", "error": "No upload result found."}

    print(f"\n  Filename      : {result.filename}")
    print(f"  Valid records : {result.total_valid}")
    print(f"  Issues        : {result.total_invalid}")

    if result.issues:
        print("\n  ⚠️  Validation issues:")
        for issue in result.issues:
            print(f"    [{issue['entity_type']}] {issue['issues']}")

    print("\n  Preview (first 5 records):")
    for row in result.preview:
        print(f"    {row}")

    answer = input("\n  Approve this data and insert into DB? (Y/N): ").strip().upper()

    if answer == "Y":
        print("  [OK] Data approved.")
        return {"data_status": "approved"}
    else:
        print("  [CANCELLED] Data rejected.")
        return {"data_status": "rejected"}


def node_ask_user_planning(state: OrchestratorState) -> dict:
    """
    Node 3 — Ask user if they want to run the Planning Agent now.
    """
    print("\n[Orchestrator] Node: ask_user_planning")
    answer = input("  Data is in DB. Run the Planning Agent now? (Y/N): ").strip().upper()
    return {"user_wants_planning": answer == "Y"}


def node_run_planning(state: OrchestratorState, db: Session) -> dict:
    """
    Node 4 — PlanningAgent generates the schedule using DB data + constraints.
    """
    print("\n[Orchestrator] Node: run_planning")

    agent  = PlanningAgent(db=db)
    result = agent.run(extra_constraints=state.get("extra_constraints", ""))

    if not result.success:
        return {
            "planning_result": result,
            "schedule_status": "rejected",
            "error":           result.error,
        }

    print(f"  -> {result.total_sessions} session(s) generated.")
    return {
        "planning_result": result,
        "schedule_status": "pending",
        "error":           "",
    }


def node_wait_for_validation(state: OrchestratorState) -> dict:
    """
    Node 5 — User validates or rejects the generated schedule.
    """
    print("\n[Orchestrator] Node: wait_for_validation")

    result = state.get("planning_result")
    if not result:
        return {"schedule_status": "rejected"}

    # Print schedule summary
    print(f"\n  {result.total_sessions} session(s) generated.")
    for s in result.schedule[:5]:
        print(f"    #{s['session_number']} | {s['course_title']} | "
              f"{s['trainer_name']} | {s['suggested_day']} {s['suggested_time']}")
    if result.total_sessions > 5:
        print(f"    ... and {result.total_sessions - 5} more.")

    answer = input("\n  Validate this schedule? (Y/N): ").strip().upper()

    if answer == "Y":
        print("  [OK] Schedule validated.")
        return {"schedule_status": "validated"}
    else:
        print("  [CANCELLED] Schedule rejected.")
        return {"schedule_status": "rejected"}


# =============================================================================
#  ROUTING CONDITIONS
# =============================================================================

def route_after_hitl(state: OrchestratorState) -> Literal["ask_user_planning", "__end__"]:
    """After HITL: if approved -> ask about planning, else -> END."""
    if state.get("data_status") == "approved":
        return "ask_user_planning"
    return "__end__"


def route_after_ask_planning(state: OrchestratorState) -> Literal["run_planning", "__end__"]:
    """After asking: if yes -> run planning, else -> END."""
    if state.get("user_wants_planning"):
        return "run_planning"
    return "__end__"


# =============================================================================
#  BUILD THE GRAPH
# =============================================================================

def build_graph(db: Session) -> StateGraph:
    """
    Builds and compiles the LangGraph orchestration graph.

    Args:
        db: SQLAlchemy session (injected so PlanningAgent can query the DB)

    Returns:
        Compiled LangGraph app ready to invoke.
    """
    graph = StateGraph(OrchestratorState)

    # Register nodes
    graph.add_node("upload_data",         node_upload_data)
    graph.add_node("wait_for_hitl",       node_wait_for_hitl)
    graph.add_node("ask_user_planning",   node_ask_user_planning)
    graph.add_node("run_planning",        lambda s: node_run_planning(s, db))
    graph.add_node("wait_for_validation", node_wait_for_validation)

    # Entry point
    graph.set_entry_point("upload_data")

    # Edges
    graph.add_edge("upload_data", "wait_for_hitl")

    graph.add_conditional_edges(
        "wait_for_hitl",
        route_after_hitl,
        {
            "ask_user_planning": "ask_user_planning",
            "__end__":            END,
        }
    )

    graph.add_conditional_edges(
        "ask_user_planning",
        route_after_ask_planning,
        {
            "run_planning": "run_planning",
            "__end__":       END,
        }
    )

    graph.add_edge("run_planning",        "wait_for_validation")
    graph.add_edge("wait_for_validation", END)

    return graph.compile()


# =============================================================================
#  ORCHESTRATOR CLASS — clean interface for the API router
# =============================================================================

class Orchestrator:
    """
    Clean interface wrapping the LangGraph pipeline.

    Terminal usage:
        orchestrator = Orchestrator(db)
        orchestrator.run(filepath, filename, extra_constraints)

    API usage:
        Each step is triggered separately by endpoints.
        The orchestrator.run() is used only in terminal/test mode.
    """

    def __init__(self, db: Session):
        self.db    = db
        self.graph = build_graph(db)

    def run(
        self,
        filepath:          str,
        filename:          str,
        extra_constraints: str = "",
    ) -> OrchestratorState:
        """
        Runs the full pipeline interactively (terminal mode).
        Returns the final state.
        """
        print("\n" + "=" * 60)
        print("  ORCHESTRATOR — DataAgent + PlanningAgent")
        print("=" * 60)

        initial_state: OrchestratorState = {
            "filepath":            filepath,
            "filename":            filename,
            "extra_constraints":   extra_constraints,
            "upload_result":       None,
            "upload_id":           None,
            "data_status":         "pending",
            "user_wants_planning": False,
            "planning_result":     None,
            "schedule_status":     "pending",
            "error":               "",
        }

        final_state = self.graph.invoke(initial_state)

        print("\n" + "=" * 60)
        print("  ORCHESTRATOR — Done")
        print(f"  Data status    : {final_state.get('data_status')}")
        print(f"  Schedule status: {final_state.get('schedule_status')}")
        if final_state.get("error"):
            print(f"  Error          : {final_state['error']}")
        print("=" * 60)

        return final_state


# =============================================================================
#  TERMINAL ENTRY POINT  ->  python -m orchestration.orchestrator
# =============================================================================

if __name__ == "__main__":
    from db.DB import SessionLocal

    print("\n" + "=" * 60)
    print("  ORCHESTRATOR — Terminal Mode")
    print("=" * 60)

    filepath = input("\n  File path to upload (CSV / Excel / PDF): ").strip()
    filename = os.path.basename(filepath)

    print("\n  Extra planning constraints (Enter to skip):")
    extra = input("  -> ").strip()

    db = SessionLocal()
    try:
        orchestrator = Orchestrator(db=db)
        orchestrator.run(
            filepath          = filepath,
            filename          = filename,
            extra_constraints = extra,
        )
    finally:
        db.close()