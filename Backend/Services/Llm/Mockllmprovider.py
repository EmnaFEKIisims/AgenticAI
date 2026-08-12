"""
Services/LLM/MockLLMProvider.py
================================
Mock LLM provider — returns predefined responses.
Used for testing FastAPI, LangGraph, and React without running Ollama.

Set in .env:
  LLM_PROVIDER=mock

The mock returns valid JSON structures so agents don't crash.
"""

from Services.Llm.Llmprovider import LLMProvider


class MockLLMProvider(LLMProvider):

    def generate(self, prompt: str, system: str | None = None) -> str:
        """
        Returns a valid mock response based on what the prompt seems to ask.
        Detects JSON format expected by each agent.
        """
        prompt_lower = prompt.lower()

        # ── Constraint extraction (planning agent / constraint agent) ──────────
        if any(k in prompt_lower for k in ["forbidden", "constraint", "contrainte", "session"]):
            return """{
  "forbidden_days": [],
  "trainer_availability": {},
  "session_duration_override": null,
  "sessions_per_day": null,
  "break_between_sessions_minutes": null,
  "lunch_break_after_n_sessions": null,
  "lunch_break_duration_minutes": null,
  "day_start_time": null,
  "min_room_capacity": null,
  "room_type_required": null,
  "group_priority": null,
  "no_parallel_sessions_same_group": false,
  "prefer_matching_specialization": true,
  "other": []
}"""

        # ── Pedagogical rule extraction ────────────────────────────────────────
        if any(k in prompt_lower for k in ["pedagogical", "pédagogique", "progression", "theory"]):
            return """[
  {"rule": "Start with fundamentals before advanced topics", "severity": "hard", "category": "progression"},
  {"rule": "Balance theory and practice within each day", "severity": "soft", "category": "balance"}
]"""

        # ── Data classification (data agent) ──────────────────────────────────
        if any(k in prompt_lower for k in ["classify", "course", "trainer", "room", "group"]):
            return """[
  {"entity_type": "course", "standardized": {"title": "Mock Course", "total_hours": 12, "session_duration": 3}, "original": {}}
]"""

        # ── Pedagogical audit explanation ─────────────────────────────────────
        if any(k in prompt_lower for k in ["audit", "score", "grade", "compliant"]):
            return (
                "The planning audit has been completed. "
                "The schedule shows good overall compliance with ISO 21001:2018 standards. "
                "Minor improvements are suggested regarding session sequencing. "
                "Consider reviewing the workload distribution across the week."
            )

        # ── Generic fallback ──────────────────────────────────────────────────
        print("  [MockLLM] Generic response returned.")
        return "Mock LLM response"