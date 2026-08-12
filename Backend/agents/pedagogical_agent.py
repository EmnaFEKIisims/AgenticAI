"""
agents/pedagogical_agent.py
=============================
Pedagogical Agent — orchestrated with LangGraph.

Each validator is a node in the graph, run in sequence.
A final LLM node (Explanation) transforms technical scores
into a human-readable audit summary.

Graph:
  START
    ↓
  [load_rules]
    ↓
  [validate_workload]
    ↓
  [validate_breaks]
    ↓
  [validate_progression]
    ↓
  [validate_practice]
    ↓
  [validate_teacher]
    ↓
  [score]          ← scoring_service (pure Python)
    ↓
  [explain]        ← LLM (Ollama)  — the "AI" part
    ↓
  [build_report]
    ↓
  END
"""

from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from Services.PedagogicalAgent.Schemas.Planning_schema   import Planning
from Services.PedagogicalAgent.Schemas.audit_schema      import AuditReport, CriterionReport
from models.criterion_result   import CriterionResult
from utils.rule_loader          import load_rules

from Services.PedagogicalAgent.Validators.workload_validator     import validate as validate_workload
from Services.PedagogicalAgent.Validators.break_validator        import validate as validate_breaks
from Services.PedagogicalAgent.Validators.progression_validator  import validate as validate_progression
from Services.PedagogicalAgent.Validators.prerequisite_validator import validate as validate_practice
from Services.PedagogicalAgent.Validators.teacher_validator      import validate as validate_teacher

from Services.PedagogicalAgent.scoring_service import compute_full_score
from Services.Llm.LlmService import _ask_ollama


# =============================================================================
#  SHARED STATE
# =============================================================================

class PedagogicalState(TypedDict):
    planning:     Planning
    rules:        dict
    results:      list[CriterionResult]
    scoring:      dict
    explanation:  str
    report:       Optional[AuditReport]
    error:        str


# =============================================================================
#  LLM PROMPT
# =============================================================================

EXPLANATION_PROMPT = """
You are a pedagogical quality expert writing an audit summary for a training administrator.
You receive a list of pedagogical audit results.
Write a short, professional paragraph (5-8 sentences) in English that:
  1. States the overall compliance level
  2. Names the top 2-3 strengths (passed criteria)
  3. Names the top 2-3 weaknesses (failed HIGH criteria)
  4. Gives one concrete overall recommendation

Tone: professional, factual, constructive. Write in prose, no bullet points.
"""


# =============================================================================
#  NODES
# =============================================================================

def node_load_rules(state: PedagogicalState) -> dict:
    print("\n[PedAgent] Node: load_rules")
    try:
        rules = load_rules()
        print(f"  → {len(rules)} rule section(s) loaded.")
        return {"rules": rules, "results": [], "error": ""}
    except Exception as e:
        return {"rules": {}, "results": [], "error": str(e)}


def _run_validator(state, name, fn):
    print(f"[PedAgent] Node: {name}")
    results = list(state.get("results", []))
    try:
        new = fn(state["planning"])
        results.extend(new)
        passed = sum(1 for r in new if r.passed)
        print(f"  → {passed}/{len(new)} passed.")
    except Exception as e:
        print(f"  ❌ {e}")
    return {"results": results}


def node_validate_workload(state):
    return _run_validator(state, "validate_workload", validate_workload)

def node_validate_breaks(state):
    return _run_validator(state, "validate_breaks", validate_breaks)

def node_validate_progression(state):
    return _run_validator(state, "validate_progression", validate_progression)

def node_validate_practice(state):
    return _run_validator(state, "validate_practice", validate_practice)

def node_validate_teacher(state):
    return _run_validator(state, "validate_teacher", validate_teacher)


def node_score(state: PedagogicalState) -> dict:
    print("[PedAgent] Node: score")
    results = state.get("results", [])
    try:
        scoring = compute_full_score(results)
        print(f"  → {scoring['score']}/100  Grade: {scoring['grade'].value}")
        return {"scoring": scoring}
    except Exception as e:
        print(f"  ❌ {e}")
        return {"scoring": {"score": 0, "grade": "F", "is_compliant": False,
                            "high_violations": 0, "recommendations": []}}


def node_explain(state: PedagogicalState) -> dict:
    """LLM node — turns technical results into human language."""
    print("[PedAgent] Node: explain (LLM)")
    results = state.get("results", [])
    scoring = state.get("scoring", {})

    prompt = (
        f"Score: {scoring.get('score', 0)}/100 | Grade: {scoring.get('grade', 'F')}\n"
        f"Passed: {', '.join(r.rule for r in results if r.passed) or 'None'}\n"
        f"Failed: {', '.join(r.rule + ' (' + r.severity.value + ')' for r in results if not r.passed) or 'None'}\n"
        f"Key recommendations: {'; '.join(scoring.get('recommendations', [])[:3]) or 'None'}"
    )

    try:
        explanation = _ask_ollama(prompt=prompt, system=EXPLANATION_PROMPT)
        print(f"  → {len(explanation)} chars generated.")
    except Exception as e:
        print(f"  ❌ LLM failed: {e}")
        explanation = (
            f"Audit completed. Score: {scoring.get('score', 0)}/100 "
            f"(Grade {scoring.get('grade', 'N/A')}). "
            "Review the detailed criteria below for improvement areas."
        )

    return {"explanation": explanation}


def node_build_report(state: PedagogicalState) -> dict:
    print("[PedAgent] Node: build_report")
    planning = state["planning"]
    results  = state.get("results", [])
    scoring  = state.get("scoring", {})

    total  = len(results)
    passed = sum(1 for r in results if r.passed)
    recs   = [state.get("explanation", "")] + scoring.get("recommendations", [])
    recs   = [r.strip() for r in recs if r.strip()]

    report = AuditReport(
        score           = scoring.get("score", 0),
        grade           = scoring.get("grade", "F"),
        is_compliant    = scoring.get("is_compliant", False),
        criteria        = [CriterionReport(**r.to_dict()) for r in results],
        recommendations = recs,
        total_criteria  = total,
        passed_criteria = passed,
        failed_criteria = total - passed,
        high_violations = scoring.get("high_violations", 0),
        planning_id     = planning.planning_id,
        group_name      = planning.group_name,
        total_sessions  = len(planning.sessions),
        total_hours     = round(planning.total_hours, 2),
    )

    print(f"  → Score={report.score_label}  Grade={report.grade.value}  "
          f"Compliant={report.is_compliant}")
    return {"report": report}


# =============================================================================
#  BUILD GRAPH
# =============================================================================

def build_graph() -> StateGraph:
    g = StateGraph(PedagogicalState)

    g.add_node("load_rules",           node_load_rules)
    g.add_node("validate_workload",    node_validate_workload)
    g.add_node("validate_breaks",      node_validate_breaks)
    g.add_node("validate_progression", node_validate_progression)
    g.add_node("validate_practice",    node_validate_practice)
    g.add_node("validate_teacher",     node_validate_teacher)
    g.add_node("score",                node_score)
    g.add_node("explain",              node_explain)
    g.add_node("build_report",         node_build_report)

    g.set_entry_point("load_rules")
    g.add_edge("load_rules",           "validate_workload")
    g.add_edge("validate_workload",    "validate_breaks")
    g.add_edge("validate_breaks",      "validate_progression")
    g.add_edge("validate_progression", "validate_practice")
    g.add_edge("validate_practice",    "validate_teacher")
    g.add_edge("validate_teacher",     "score")
    g.add_edge("score",                "explain")
    g.add_edge("explain",              "build_report")
    g.add_edge("build_report",         END)

    return g.compile()


# =============================================================================
#  AGENT CLASS
# =============================================================================

class PedagogicalAgent:
    """
    LangGraph-based Pedagogical Agent.
    Orchestrates validators → scoring → LLM explanation → AuditReport.

    Usage:
        agent  = PedagogicalAgent()
        report = agent.audit(planning)        # from Planning object
        report = agent.generate_report(schedule, group_name="Group A")  # from schedule list
    """

    def __init__(self):
        self.graph = build_graph()

    def audit(self, planning: Planning) -> AuditReport:
        print(f"\n{'='*60}")
        print(f"  PEDAGOGICAL AGENT  (LangGraph)")
        print(f"  Sessions : {len(planning.sessions)}")
        print(f"  Hours    : {round(planning.total_hours, 1)}h total")
        print(f"{'='*60}")

        final = self.graph.invoke({
            "planning":    planning,
            "rules":       {},
            "results":     [],
            "scoring":     {},
            "explanation": "",
            "report":      None,
            "error":       "",
        })

        report = final.get("report")
        if report is None:
            raise RuntimeError("Pedagogical audit failed — no report generated.")
        return report

    def generate_report(self, schedule: list[dict], group_name: str = "") -> AuditReport:
        """
        Convenience: builds Planning from PlanningAgent output and audits it.
        """
        planning = Planning.from_schedule(schedule, group_name=group_name)
        return self.audit(planning)