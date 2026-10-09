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

IMPORTANT — generate_report() now audits PER LEARNER GROUP.
Every validator sums hours/gaps across all sessions it receives, assuming
they belong to one learner's schedule. A schedule with several groups
running in parallel (e.g. 5 groups all at 08:00 Monday) used to be fed in
as ONE Planning, making the audit think a single learner had 15h of class
on Monday instead of 3h — tanking the score for a schedule that is
actually well optimized. generate_report() now splits the incoming
schedule by group_name, audits each group's Planning separately, and
returns an aggregated report (average score, per-group breakdown in
`group_scores`).
"""

from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from Services.PedagogicalAgent.Schemas.Planning_schema   import Planning
from Services.PedagogicalAgent.Schemas.audit_schema      import AuditReport, AuditGrade, CriterionReport
from models.criterion_result   import CriterionResult
from utils.rule_loader          import load_rules

from Services.PedagogicalAgent.Validators.workload_validator     import validate as validate_workload
from Services.PedagogicalAgent.Validators.break_validator        import validate as validate_breaks
from Services.PedagogicalAgent.Validators.progression_validator  import validate as validate_progression
from Services.PedagogicalAgent.Validators.prerequisite_validator import validate as validate_practice
from Services.PedagogicalAgent.Validators.teacher_validator      import validate as validate_teacher

from Services.PedagogicalAgent.scoring_service import compute_full_score, grade as grade_from_score
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
        report = agent.audit(planning)        # from a Planning already scoped to ONE group
        report = agent.generate_report(schedule, group_name="Group A")  # from raw schedule list
    """

    def __init__(self):
        self.graph = build_graph()

    def audit(self, planning: Planning) -> AuditReport:
        """
        Audits a SINGLE Planning. Callers must make sure `planning` holds
        the sessions of one learner group only — every validator assumes
        that. generate_report() below handles the multi-group splitting
        for you; only call audit() directly with an already-filtered Planning.
        """
        print(f"\n{'='*60}")
        print(f"  PEDAGOGICAL AGENT  (LangGraph)")
        print(f"  Group    : {planning.group_name or 'N/A'}")
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
        Builds Planning(s) from the PlanningAgent output and audits them.

        If `schedule` contains sessions from several learner groups (several
        distinct `group_name` values), each group is audited SEPARATELY —
        auditing the whole mixed schedule as one Planning would sum every
        group's hours into the same "day", flagging workload/break
        violations that don't exist for any actual learner. The returned
        report aggregates the per-group scores (simple average) and exposes
        the breakdown in `report.group_scores`.
        """
        if not schedule:
            raise ValueError("Schedule is empty — nothing to audit.")

        groups_present = sorted({
            (s.get("group_name") or group_name) for s in schedule
            if (s.get("group_name") or group_name)
        })

        if len(groups_present) <= 1:
            planning = Planning.from_schedule(schedule, group_name=group_name)
            if not planning.sessions:
                raise ValueError(
                    f"None of the {len(schedule)} session(s) in the schedule could be "
                    "parsed into a valid Planning — check that each slot carries either "
                    "'suggested_day'/'suggested_time' or 'start_time'/'end_time'. "
                    "See the server logs for the per-session reason."
                )
            return self.audit(planning)

        print(f"\n[PedAgent] Schedule spans {len(groups_present)} groups "
              f"— auditing each group separately: {groups_present}")

        per_group_reports: dict[str, AuditReport] = {}
        for g in groups_present:
            group_schedule = [s for s in schedule if (s.get("group_name") or group_name) == g]
            planning = Planning.from_schedule(group_schedule, group_name=g)
            if not planning.sessions:
                print(f"  [PedAgent] Skipping group '{g}': no valid sessions parsed.")
                continue
            per_group_reports[g] = self.audit(planning)

        if not per_group_reports:
            raise ValueError(
                f"None of the {len(schedule)} session(s) across {len(groups_present)} "
                "group(s) could be parsed into a valid Planning. See server logs for "
                "the per-session reason."
            )

        return self._aggregate_group_reports(per_group_reports)

    def _aggregate_group_reports(self, reports: dict[str, AuditReport]) -> AuditReport:
        """Combines several per-group AuditReports into one overall report."""
        n = len(reports)
        avg_score = sum(r.score for r in reports.values()) / n if n else 0.0

        # Union of all criteria across groups, for the detail table
        all_criteria: list[CriterionReport] = []
        for r in reports.values():
            all_criteria.extend(r.criteria)

        # Recommendations, tagged by group, deduplicated
        all_recs: list[str] = []
        for g, r in reports.items():
            for rec in r.recommendations:
                tagged = f"[{g}] {rec}"
                if tagged not in all_recs:
                    all_recs.append(tagged)

        total_criteria  = sum(r.total_criteria  for r in reports.values())
        passed_criteria = sum(r.passed_criteria for r in reports.values())
        high_violations = sum(r.high_violations for r in reports.values())
        total_sessions  = sum(r.total_sessions   for r in reports.values())
        total_hours     = sum(r.total_hours      for r in reports.values())

        aggregated = AuditReport(
            score           = round(avg_score, 2),
            grade           = grade_from_score(avg_score),
            is_compliant    = avg_score >= 60 and high_violations == 0,
            criteria        = all_criteria,
            recommendations = all_recs,
            group_scores    = {g: r.score for g, r in reports.items()},
            total_criteria  = total_criteria,
            passed_criteria = passed_criteria,
            failed_criteria = total_criteria - passed_criteria,
            high_violations = high_violations,
            planning_id     = None,
            group_name      = None,
            total_sessions  = total_sessions,
            total_hours     = round(total_hours, 2),
        )

        print(f"\n[PedAgent] Aggregated {n} group report(s) → "
              f"average score {aggregated.score_label} (Grade {aggregated.grade.value})")
        for g, r in reports.items():
            print(f"    - {g}: {r.score_label} (Grade {r.grade.value})")

        return aggregated