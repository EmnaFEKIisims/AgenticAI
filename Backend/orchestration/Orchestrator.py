"""
orchestration/orchestrator.py
==============================
LangGraph orchestrator — updated to include the Pedagogical Agent.

Full pipeline:

  START
    │
    ▼
  [upload_data]            DataAgent: parse → LLM extract → validate → TempStorage
    │
    ▼
  [wait_for_hitl]          PAUSE — user approves or rejects the data
    │
    ├── rejected ─────────► END
    │
    ▼
  [ask_user_planning]      "Run Planning Agent? (Y/N)"
    │
    ├── N ────────────────► END
    │
    ▼
  [run_planning]           PlanningAgent: constraints + greedy scheduling
    │
    ▼
  [wait_for_validation]    PAUSE — user validates or rejects the schedule
    │
    ├── rejected ─────────► END
    │
    ▼
  [run_pedagogical_audit]  PedagogicalAgent (LangGraph): 6 validators + LLM
    │
    ▼
  [show_audit_report]      Prints audit score, grade, recommendations
    │
    ▼
  END
"""

import os
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from agents.Data_Manager   import DataAgent, UploadResult
from agents.planning_agent import PlanningAgent, PlanningResult
from agents.pedagogical_agent import PedagogicalAgent
from Services.PedagogicalAgent.Schemas.audit_schema  import AuditReport
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning
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
    data_status:       str           # "pending" | "approved" | "rejected"

    # User decision after HITL
    user_wants_planning: bool

    # PlanningAgent outputs
    planning_result:   Optional[PlanningResult]
    schedule_status:   str           # "pending" | "validated" | "rejected"

    # PedagogicalAgent outputs  ← NEW
    audit_report:      Optional[AuditReport]
    audit_status:      str           # "pending" | "done" | "skipped"

    # Error
    error:             str


# =============================================================================
#  NODE 1 — DataAgent
# =============================================================================

def node_upload_data(state: OrchestratorState) -> dict:
    print("\n[Orchestrator] Node: upload_data")

    storage = TempStorage()
    agent   = DataAgent(storage)
    result  = agent.process_file(
        filepath = state["filepath"],
        filename = state["filename"],
    )

    if not result.success:
        return {
            "upload_result": result,
            "data_status":   "rejected",
            "error":         result.error,
        }

    print(f"  → Upload ID: {result.upload_id}")
    print(f"  → {result.total_valid} valid | {result.total_invalid} issue(s)")
    return {
        "upload_result": result,
        "upload_id":     result.upload_id,
        "data_status":   "pending",
        "error":         "",
    }


# =============================================================================
#  NODE 2 — HITL: approve or reject data
# =============================================================================

def node_wait_for_hitl(state: OrchestratorState) -> dict:
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
    print("  [CANCELLED] Data rejected.")
    return {"data_status": "rejected"}


# =============================================================================
#  NODE 3 — Ask user about planning
# =============================================================================

def node_ask_user_planning(state: OrchestratorState) -> dict:
    print("\n[Orchestrator] Node: ask_user_planning")
    answer = input("  Data is in DB. Run the Planning Agent now? (Y/N): ").strip().upper()
    return {"user_wants_planning": answer == "Y"}


# =============================================================================
#  NODE 4 — PlanningAgent
# =============================================================================

def node_run_planning(state: OrchestratorState, db: Session) -> dict:
    print("\n[Orchestrator] Node: run_planning")

    agent  = PlanningAgent(db=db)
    result = agent.run(extra_constraints=state.get("extra_constraints", ""))

    if not result.success:
        return {
            "planning_result": result,
            "schedule_status": "rejected",
            "error":           result.error,
        }

    print(f"  → {result.total_sessions} session(s) generated.")
    return {
        "planning_result": result,
        "schedule_status": "pending",
        "error":           "",
    }


# =============================================================================
#  NODE 5 — HITL: validate or reject schedule
# =============================================================================

def node_wait_for_validation(state: OrchestratorState) -> dict:
    print("\n[Orchestrator] Node: wait_for_validation")

    result = state.get("planning_result")
    if not result:
        return {"schedule_status": "rejected"}

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
    print("  [CANCELLED] Schedule rejected.")
    return {"schedule_status": "rejected"}


# =============================================================================
#  NODE 6 — PedagogicalAgent  ← NEW
# =============================================================================

def node_run_pedagogical_audit(state: OrchestratorState) -> dict:
    """
    Runs the full Pedagogical Agent pipeline on the validated schedule.

    The PedagogicalAgent is itself a LangGraph graph (nested graph):
      load_rules → validate_workload → validate_breaks → validate_progression
      → validate_prerequisite → validate_teacher → validate_room
      → score → explain (LLM) → build_report
    """
    print("\n[Orchestrator] Node: run_pedagogical_audit")

    planning_result = state.get("planning_result")
    if not planning_result or not planning_result.schedule:
        print("  No schedule to audit.")
        return {"audit_report": None, "audit_status": "skipped"}

    try:
        ped_agent = PedagogicalAgent()
        report    = ped_agent.generate_report(
            schedule   = planning_result.schedule,
            group_name = "",
        )
        print(f"  → Audit done. Score={report.score_label} Grade={report.grade.value}")
        return {"audit_report": report, "audit_status": "done"}

    except Exception as e:
        print(f"  ❌ Pedagogical audit failed: {e}")
        return {"audit_report": None, "audit_status": "skipped", "error": str(e)}


# =============================================================================
#  NODE 7 — Display audit report  ← NEW
# =============================================================================

def node_show_audit_report(state: OrchestratorState) -> dict:
    """Prints the audit report summary in the terminal."""
    print("\n[Orchestrator] Node: show_audit_report")

    report = state.get("audit_report")
    if not report:
        print("  No audit report available.")
        return {}

    W = 60
    print(f"\n{'='*W}")
    print(f"  PEDAGOGICAL AUDIT REPORT")
    print(f"{'='*W}")
    print(f"  Score       : {report.score_label}")
    print(f"  Grade       : {report.grade.value}  ({_grade_label(report.grade.value)})")
    print(f"  Compliant   : {'✅ Yes' if report.is_compliant else '❌ No'}")
    print(f"  Criteria    : {report.passed_criteria}/{report.total_criteria} passed")
    print(f"  High risks  : {report.high_violations}")
    print(f"\n  Criteria detail:")
    for c in report.criteria:
        icon = "✅" if c.passed else "❌"
        print(f"    {icon} {c.rule:<40} {c.score:.0f}/{c.weight:.0f}")

    if report.recommendations:
        print(f"\n  Recommendations:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"    {i}. {rec[:100]}")

    print(f"{'='*W}\n")
    return {}


def _grade_label(grade: str) -> str:
    return {
        "A": "Excellent", "B": "Good", "C": "Acceptable",
        "D": "Needs Improvement", "F": "Non-Compliant",
    }.get(grade, grade)


# =============================================================================
#  ROUTING CONDITIONS
# =============================================================================

def route_after_hitl(
    state: OrchestratorState,
) -> Literal["ask_user_planning", "__end__"]:
    return "ask_user_planning" if state.get("data_status") == "approved" else "__end__"


def route_after_ask_planning(
    state: OrchestratorState,
) -> Literal["run_planning", "__end__"]:
    return "run_planning" if state.get("user_wants_planning") else "__end__"


def route_after_validation(
    state: OrchestratorState,
) -> Literal["run_pedagogical_audit", "__end__"]:
    """After schedule validation: if validated → audit, else → END."""
    return "run_pedagogical_audit" if state.get("schedule_status") == "validated" else "__end__"


# =============================================================================
#  BUILD GRAPH
# =============================================================================

def build_graph(db: Session) -> StateGraph:
    graph = StateGraph(OrchestratorState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    graph.add_node("upload_data",            node_upload_data)
    graph.add_node("wait_for_hitl",          node_wait_for_hitl)
    graph.add_node("ask_user_planning",      node_ask_user_planning)
    graph.add_node("run_planning",           lambda s: node_run_planning(s, db))
    graph.add_node("wait_for_validation",    node_wait_for_validation)
    graph.add_node("run_pedagogical_audit",  node_run_pedagogical_audit)   # ← NEW
    graph.add_node("show_audit_report",      node_show_audit_report)        # ← NEW

    # ── Entry point ──────────────────────────────────────────────────────────
    graph.set_entry_point("upload_data")

    # ── Edges ────────────────────────────────────────────────────────────────
    graph.add_edge("upload_data", "wait_for_hitl")

    graph.add_conditional_edges(
        "wait_for_hitl",
        route_after_hitl,
        {"ask_user_planning": "ask_user_planning", "__end__": END},
    )

    graph.add_conditional_edges(
        "ask_user_planning",
        route_after_ask_planning,
        {"run_planning": "run_planning", "__end__": END},
    )

    graph.add_edge("run_planning", "wait_for_validation")

    # ← CHANGED: was → END, now → run_pedagogical_audit (conditionally)
    graph.add_conditional_edges(
        "wait_for_validation",
        route_after_validation,
        {"run_pedagogical_audit": "run_pedagogical_audit", "__end__": END},
    )

    graph.add_edge("run_pedagogical_audit", "show_audit_report")   # ← NEW
    graph.add_edge("show_audit_report",     END)                    # ← NEW

    return graph.compile()


# =============================================================================
#  ORCHESTRATOR CLASS
# =============================================================================

class Orchestrator:
    """
    Full pipeline:
      DataAgent → HITL → PlanningAgent → HITL → PedagogicalAgent → Report

    Terminal usage:
        orchestrator = Orchestrator(db)
        orchestrator.run(filepath, filename, extra_constraints)

    API usage:
        Each HITL step is handled by the respective API endpoints.
        The PedagogicalAgent is triggered automatically after schedule validation.
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
        print("\n" + "=" * 60)
        print("  ORCHESTRATOR — DataAgent + PlanningAgent + PedagogicalAgent")
        print("=" * 60)

        initial: OrchestratorState = {
            "filepath":            filepath,
            "filename":            filename,
            "extra_constraints":   extra_constraints,
            "upload_result":       None,
            "upload_id":           None,
            "data_status":         "pending",
            "user_wants_planning": False,
            "planning_result":     None,
            "schedule_status":     "pending",
            "audit_report":        None,          # ← NEW
            "audit_status":        "pending",     # ← NEW
            "error":               "",
        }

        final = self.graph.invoke(initial)

        print("\n" + "=" * 60)
        print("  ORCHESTRATOR — Done")
        print(f"  Data status     : {final.get('data_status')}")
        print(f"  Schedule status : {final.get('schedule_status')}")
        print(f"  Audit status    : {final.get('audit_status')}")   # ← NEW
        if final.get("audit_report"):
            r = final["audit_report"]
            print(f"  Audit score     : {r.score_label} ({r.grade.value})")
        if final.get("error"):
            print(f"  Error           : {final['error']}")
        print("=" * 60)

        return final


# =============================================================================
#  TERMINAL ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    from db.DB import SessionLocal

    print("\n" + "=" * 60)
    print("  ORCHESTRATOR — Terminal Mode")
    print("=" * 60)

    filepath = input("\n  File path to upload (CSV / Excel / PDF): ").strip()
    filename = os.path.basename(filepath)

    print("\n  Extra planning constraints (Enter to skip):")
    extra = input("  → ").strip()

    db = SessionLocal()
    try:
        Orchestrator(db=db).run(
            filepath          = filepath,
            filename          = filename,
            extra_constraints = extra,
        )
    finally:
        db.close()