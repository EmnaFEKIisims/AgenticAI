"""
orchestration/orchestrator.py
==============================
LangGraph orchestrator — updated with RAG integration.

RAG is added at 5 key events:
  1. BEFORE planning → retrieve context (user preferences, past decisions)
  2. AFTER validation → store positive signal
  3. AFTER rejection  → extract and store negative feedback
  4. AFTER anomaly    → store conflict patterns
  5. AFTER move (API) → store DnD preference signal

Full pipeline:

  START
    │
    ▼
  [init_rag_user]          ensure User exists in DB for RAG memory
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
  [retrieve_rag_context]   RAG: get adaptive context from past experiences   ← NEW
    │
    ▼
  [run_planning]           PlanningAgent: constraints + RAG context + greedy scheduling
    │
    ▼
  [wait_for_validation]    PAUSE — user validates or rejects the schedule
    │
    ├── rejected → [store_rejection_memory] ──────────────────────────────► END
    │
    ▼
  [store_validation_memory]                                                  ← NEW
    │
    ▼
  [run_pedagogical_audit]  PedagogicalAgent (LangGraph): 6 validators + LLM
    │
    ▼
  [run_anomaly_detection]  AnomalyAgent: detect → classify → resolve → notify
    │
    ▼
  [store_anomaly_memory]                                                     ← NEW
    │
    ▼
  [wait_for_anomaly_hitl]  PAUSE — admin reviews anomalies
    │
    ▼
  [show_audit_report]      Prints audit score, grade, recommendations + anomalies
    │
    ▼
  END
"""

import os
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from agents.Data_Manager      import DataAgent, UploadResult
from agents.planning_agent    import PlanningAgent, PlanningResult
from agents.pedagogical_agent import PedagogicalAgent
from agents.Anomaly           import AnomalyAgent, AnomalyAgentResult

from Services.PedagogicalAgent.Schemas.audit_schema    import AuditReport
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning
from Services.DataManager.Temp_storage                 import TempStorage

# RAG integration
from Services.RAG.rag_service import RAGService

# Default user_id for terminal mode (no frontend UUID available)
DEFAULT_TERMINAL_USER_ID = "system-terminal-orchestrator"


# =============================================================================
#  STATE — shared across all nodes
# =============================================================================

class OrchestratorState(TypedDict):
    # Input
    filepath:          str
    filename:          str
    extra_constraints: str
    user_id:           str           # RAG user identifier

    # DataAgent outputs
    upload_result:     Optional[UploadResult]
    upload_id:         Optional[str]
    data_status:       str           # "pending" | "approved" | "rejected"

    # User decision after HITL
    user_wants_planning: bool

    # RAG context
    rag_context:       str           # context retrieved from ChromaDB

    # PlanningAgent outputs
    planning_result:   Optional[PlanningResult]
    schedule_status:   str           # "pending" | "validated" | "rejected"

    # PedagogicalAgent outputs
    audit_report:      Optional[AuditReport]
    audit_status:      str           # "pending" | "done" | "skipped"

    # AnomalyAgent outputs
    anomaly_result:      Optional[AnomalyAgentResult]
    anomaly_status:      str         # "pending" | "reviewed" | "skipped"
    user_anomaly_action: str         # "continue" | "abort"

    # Error
    error:             str


# =============================================================================
#  NODE 0 — Initialize RAG User  ← NEW
# =============================================================================

def node_init_rag_user(state: OrchestratorState, db: Session) -> dict:
    """
    Ensures the RAG user exists in the DB.
    In terminal mode, uses a fixed system UUID.
    In API mode, the user_id comes from the frontend localStorage UUID.
    """
    print("\n[Orchestrator] Node: init_rag_user")
    user_id = state.get("user_id") or DEFAULT_TERMINAL_USER_ID
    try:
        svc  = RAGService(db)
        user = svc.ensure_user(user_id, "System Administrator")
        print(f"  → RAG user: {user_id[:8]}... ({user.display_name})")
    except Exception as e:
        print(f"  ⚠️  RAG user init failed: {e} (continuing without RAG)")
    return {"user_id": user_id}


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
#  NODE 4 — Retrieve RAG context  ← NEW
# =============================================================================

def node_retrieve_rag_context(state: OrchestratorState, db: Session) -> dict:
    """
    Retrieves adaptive context from past experiences BEFORE planning.
    The context (preferences, past decisions, feedback) is injected into
    the LLM prompt of PlanningAgent.
    """
    print("\n[Orchestrator] Node: retrieve_rag_context")
    user_id = state.get("user_id", DEFAULT_TERMINAL_USER_ID)

    try:
        svc     = RAGService(db)
        context = svc.get_planning_context(user_id)
        if context:
            print(f"  → RAG context retrieved ({len(context)} chars)")
            print("  → Past preferences/decisions will influence this planning.")
        else:
            print("  → No past context found (first planning or empty memory).")
        return {"rag_context": context}
    except Exception as e:
        print(f"  ⚠️  RAG retrieval failed: {e} (continuing without context)")
        return {"rag_context": ""}


# =============================================================================
#  NODE 5 — PlanningAgent (with RAG context injection)
# =============================================================================

def node_run_planning(state: OrchestratorState, db: Session) -> dict:
    print("\n[Orchestrator] Node: run_planning")

    agent  = PlanningAgent(db=db)
    user_id = state.get("user_id", DEFAULT_TERMINAL_USER_ID)
    rag_context = state.get("rag_context", "")

    # Inject RAG context into extra_constraints
    # The PlanningAgent will prepend this to its LLM system prompt
    enriched_constraints = state.get("extra_constraints", "")
    if rag_context:
        enriched_constraints = f"{rag_context}\n\n{enriched_constraints}".strip()

    result = agent.run(extra_constraints=enriched_constraints)

    if not result.success:
        return {
            "planning_result": result,
            "schedule_status": "rejected",
            "error":           result.error,
        }

    print(f"  → {result.total_sessions} session(s) generated.")

    # Store generation event in RAG memory
    try:
        RAGService(db).after_planning_generated(
            user_id     = user_id,
            schedule    = result.schedule,
            constraints = result.constraints_used,
        )
    except Exception as e:
        print(f"  ⚠️  RAG storage failed: {e}")

    return {
        "planning_result": result,
        "schedule_status": "pending",
        "error":           "",
    }


# =============================================================================
#  NODE 6 — HITL: validate or reject schedule
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

    reason = input("  Rejection reason (Enter to skip): ").strip()
    print("  [CANCELLED] Schedule rejected.")
    return {"schedule_status": "rejected", "error": reason}


# =============================================================================
#  NODE 7a — Store validation memory  ← NEW
# =============================================================================

def node_store_validation_memory(state: OrchestratorState, db: Session) -> dict:
    """Stores positive memory after planning validation."""
    print("\n[Orchestrator] Node: store_validation_memory")
    user_id = state.get("user_id", DEFAULT_TERMINAL_USER_ID)
    result  = state.get("planning_result")
    try:
        RAGService(db).after_planning_validated(
            user_id     = user_id,
            schedule    = result.schedule if result else [],
            constraints = result.constraints_used if result else {},
            notes       = "Admin validated in terminal mode",
        )
        print("  → Validation memory stored in RAG.")
    except Exception as e:
        print(f"  ⚠️  RAG storage failed: {e}")
    return {}


# =============================================================================
#  NODE 7b — Store rejection memory  ← NEW
# =============================================================================

def node_store_rejection_memory(state: OrchestratorState, db: Session) -> dict:
    """Extracts and stores feedback memories from rejection."""
    print("\n[Orchestrator] Node: store_rejection_memory")
    user_id = state.get("user_id", DEFAULT_TERMINAL_USER_ID)
    reason  = state.get("error", "")
    try:
        RAGService(db).after_planning_rejected(user_id=user_id, reason=reason)
        if reason:
            print(f"  → Rejection memory stored: '{reason[:60]}...'")
        else:
            print("  → Rejection stored (no reason given).")
    except Exception as e:
        print(f"  ⚠️  RAG storage failed: {e}")
    return {}


# =============================================================================
#  NODE 8 — PedagogicalAgent
# =============================================================================

def node_run_pedagogical_audit(state: OrchestratorState) -> dict:
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
#  NODE 9 — AnomalyAgent
# =============================================================================

def node_run_anomaly_detection(state: OrchestratorState, db: Session) -> dict:
    print("\n[Orchestrator] Node: run_anomaly_detection")

    planning_result = state.get("planning_result")
    if not planning_result or not planning_result.schedule:
        print("  No schedule — skipping anomaly detection.")
        return {"anomaly_result": None, "anomaly_status": "skipped"}

    try:
        agent  = AnomalyAgent(db=db)
        result = agent.analyze(schedule=planning_result.schedule)
        print(f"  → {result.summary}")
        return {"anomaly_result": result, "anomaly_status": "pending"}
    except Exception as e:
        print(f"  ❌ AnomalyAgent failed: {e}")
        return {"anomaly_result": None, "anomaly_status": "skipped", "error": str(e)}


# =============================================================================
#  NODE 10 — Store anomaly memory  ← NEW
# =============================================================================

def node_store_anomaly_memory(state: OrchestratorState, db: Session) -> dict:
    """Stores detected conflicts as CONFLICT_CORRECTION memories."""
    print("\n[Orchestrator] Node: store_anomaly_memory")
    user_id = state.get("user_id", DEFAULT_TERMINAL_USER_ID)
    result  = state.get("anomaly_result")

    if not result or result.total_detected == 0:
        print("  → No anomalies to store.")
        return {}

    try:
        RAGService(db).after_anomaly(
            user_id   = user_id,
            anomalies = result.anomalies,
        )
        print(f"  → {result.high_count + result.medium_count} anomaly memories stored.")
    except Exception as e:
        print(f"  ⚠️  RAG storage failed: {e}")
    return {}


# =============================================================================
#  NODE 11 — HITL: admin reviews anomalies
# =============================================================================

def node_wait_for_anomaly_hitl(state: OrchestratorState) -> dict:
    print("\n[Orchestrator] Node: wait_for_anomaly_hitl")

    result = state.get("anomaly_result")
    if not result or result.total_detected == 0:
        print("  ✅ No anomalies — continuing automatically.")
        return {"user_anomaly_action": "continue"}

    print(f"\n  ⚠️  {result.total_detected} anomaly(ies) detected:")
    print(f"    🔴 HIGH={result.high_count}  🟡 MEDIUM={result.medium_count}  🟢 LOW={result.low_count}")
    for a in result.anomalies[:5]:
        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
            a.get("severity", "").upper(), "⚠️"
        )
        print(f"    {icon} {a.get('title')}")
        if a.get("recommendation"):
            print(f"         → {a['recommendation']}")
    if result.total_detected > 5:
        print(f"    ... and {result.total_detected - 5} more.")

    answer = input("\n  Continue despite anomalies? (Y/N): ").strip().upper()
    return {"user_anomaly_action": "continue" if answer == "Y" else "abort"}


# =============================================================================
#  NODE 12 — Display audit report + anomaly summary
# =============================================================================

def node_show_audit_report(state: OrchestratorState) -> dict:
    print("\n[Orchestrator] Node: show_audit_report")

    report = state.get("audit_report")
    if report:
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
        print(f"{'='*W}")

    anomaly_result = state.get("anomaly_result")
    if anomaly_result and anomaly_result.total_detected > 0:
        print(f"\n  ANOMALY SUMMARY")
        print(f"  Total     : {anomaly_result.total_detected}")
        print(f"  🔴 HIGH   : {anomaly_result.high_count}")
        print(f"  🟡 MEDIUM : {anomaly_result.medium_count}")
        print(f"  🟢 LOW    : {anomaly_result.low_count}")

    # RAG summary
    print(f"\n  RAG MEMORY")
    print(f"  Memories stored during this session.")
    print(f"  They will influence the NEXT planning generation.")

    action = state.get("user_anomaly_action", "continue")
    print(f"\n  {'✅ Planning FINALIZED' if action == 'continue' else '❌ Planning ABORTED'}")
    print()
    return {}


def _grade_label(grade: str) -> str:
    return {
        "A": "Excellent", "B": "Good", "C": "Acceptable",
        "D": "Needs Improvement", "F": "Non-Compliant",
    }.get(grade, grade)


# =============================================================================
#  ROUTING
# =============================================================================

def route_after_hitl(state: OrchestratorState) -> Literal["ask_user_planning", "__end__"]:
    return "ask_user_planning" if state.get("data_status") == "approved" else "__end__"


def route_after_ask_planning(state: OrchestratorState) -> Literal["retrieve_rag_context", "__end__"]:
    return "retrieve_rag_context" if state.get("user_wants_planning") else "__end__"


def route_after_validation(
    state: OrchestratorState,
) -> Literal["store_validation_memory", "store_rejection_memory"]:
    if state.get("schedule_status") == "validated":
        return "store_validation_memory"
    return "store_rejection_memory"


def route_after_anomaly_hitl(state: OrchestratorState) -> Literal["show_audit_report"]:
    return "show_audit_report"


# =============================================================================
#  BUILD GRAPH
# =============================================================================

def build_graph(db: Session) -> StateGraph:
    graph = StateGraph(OrchestratorState)

    # Nodes
    graph.add_node("init_rag_user",           lambda s: node_init_rag_user(s, db))
    graph.add_node("upload_data",             node_upload_data)
    graph.add_node("wait_for_hitl",           node_wait_for_hitl)
    graph.add_node("ask_user_planning",       node_ask_user_planning)
    graph.add_node("retrieve_rag_context",    lambda s: node_retrieve_rag_context(s, db))
    graph.add_node("run_planning",            lambda s: node_run_planning(s, db))
    graph.add_node("wait_for_validation",     node_wait_for_validation)
    graph.add_node("store_validation_memory", lambda s: node_store_validation_memory(s, db))
    graph.add_node("store_rejection_memory",  lambda s: node_store_rejection_memory(s, db))
    graph.add_node("run_pedagogical_audit",   node_run_pedagogical_audit)
    graph.add_node("run_anomaly_detection",   lambda s: node_run_anomaly_detection(s, db))
    graph.add_node("store_anomaly_memory",    lambda s: node_store_anomaly_memory(s, db))
    graph.add_node("wait_for_anomaly_hitl",   node_wait_for_anomaly_hitl)
    graph.add_node("show_audit_report",       node_show_audit_report)

    # Edges
    graph.set_entry_point("init_rag_user")
    graph.add_edge("init_rag_user",           "upload_data")
    graph.add_edge("upload_data",             "wait_for_hitl")

    graph.add_conditional_edges("wait_for_hitl", route_after_hitl,
        {"ask_user_planning": "ask_user_planning", "__end__": END})

    graph.add_conditional_edges("ask_user_planning", route_after_ask_planning,
        {"retrieve_rag_context": "retrieve_rag_context", "__end__": END})

    graph.add_edge("retrieve_rag_context",    "run_planning")
    graph.add_edge("run_planning",            "wait_for_validation")

    graph.add_conditional_edges("wait_for_validation", route_after_validation,
        {"store_validation_memory": "store_validation_memory",
         "store_rejection_memory":  "store_rejection_memory"})

    graph.add_edge("store_validation_memory", "run_pedagogical_audit")
    graph.add_edge("store_rejection_memory",  END)

    graph.add_edge("run_pedagogical_audit",   "run_anomaly_detection")
    graph.add_edge("run_anomaly_detection",   "store_anomaly_memory")
    graph.add_edge("store_anomaly_memory",    "wait_for_anomaly_hitl")

    graph.add_conditional_edges("wait_for_anomaly_hitl", route_after_anomaly_hitl,
        {"show_audit_report": "show_audit_report"})

    graph.add_edge("show_audit_report",       END)

    return graph.compile()


# =============================================================================
#  ORCHESTRATOR CLASS
# =============================================================================

class Orchestrator:
    def __init__(self, db: Session):
        self.db    = db
        self.graph = build_graph(db)

    def run(
        self,
        filepath:          str,
        filename:          str,
        extra_constraints: str = "",
        user_id:           str = DEFAULT_TERMINAL_USER_ID,
    ) -> OrchestratorState:
        print("\n" + "=" * 60)
        print("  ORCHESTRATOR — with RAG Adaptive Memory")
        print("=" * 60)

        initial: OrchestratorState = {
            "filepath":            filepath,
            "filename":            filename,
            "extra_constraints":   extra_constraints,
            "user_id":             user_id,
            "upload_result":       None,
            "upload_id":           None,
            "data_status":         "pending",
            "user_wants_planning": False,
            "rag_context":         "",
            "planning_result":     None,
            "schedule_status":     "pending",
            "audit_report":        None,
            "audit_status":        "pending",
            "anomaly_result":      None,
            "anomaly_status":      "pending",
            "user_anomaly_action": "continue",
            "error":               "",
        }

        final = self.graph.invoke(initial)

        print("\n" + "=" * 60)
        print("  ORCHESTRATOR — Done")
        print(f"  Data status     : {final.get('data_status')}")
        print(f"  Schedule status : {final.get('schedule_status')}")
        print(f"  Audit status    : {final.get('audit_status')}")
        print(f"  Anomaly status  : {final.get('anomaly_status')}")
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
    print("  ORCHESTRATOR — Terminal Mode (with RAG)")
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