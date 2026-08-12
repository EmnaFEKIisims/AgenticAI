import json
from Services.Llm.LlmService import _ask_ollama
from Services.constraintAgent.Schema import (
    ConstraintInput, ConstraintOutput,
    ISOConstraint, PedagogicalConstraint, UserConstraint,
    ConstraintSeverity,
)


# =============================================================================
#  PROMPT — Pedagogical constraints
# =============================================================================

PEDAGOGICAL_PROMPT = """
You are an expert in training pedagogy and adult learning.
The user describes pedagogical wishes for a training schedule.
Extract and return ONLY a valid JSON array. No markdown, no explanation.

Each element must follow this structure:
{
  "rule": "<normalized rule in English>",
  "severity": "hard" or "soft",
  "category": "progression" | "load" | "balance" | "other"
}

Category definitions:
  - "progression"  : rules about logical ordering of content (e.g. fundamentals before advanced)
  - "load"         : rules about cognitive load (e.g. max 2 new concepts per session)
  - "balance"      : rules about balancing session types (e.g. mix theory and practice)
  - "other"        : anything that does not fit the above

Severity:
  - "hard" : must be respected — failure to comply blocks the planning
  - "soft" : preferred — planning continues but a warning is raised if not respected

Examples of inputs and expected outputs:
  Input: "Start with basics before advanced topics"
  Output: [{"rule": "Start with fundamentals before advanced content", "severity": "hard", "category": "progression"}]

  Input: "Avoid cramming too many new concepts in one session. Balance theory and practice."
  Output: [
    {"rule": "Limit new concepts to 2 per session", "severity": "soft", "category": "load"},
    {"rule": "Balance theory and practice within each day", "severity": "soft", "category": "balance"}
  ]

Rules:
- Extract each distinct pedagogical rule as a separate element
- Normalize the rule to clear, concise English
- If nothing pedagogical is mentioned, return []
- Never invent rules not implied by the text
"""


# =============================================================================
#  PROMPT — User scheduling constraints
# =============================================================================

USER_CONSTRAINT_PROMPT = """
You are a constraint extractor for a training planning system.
The user describes scheduling wishes in natural language (English or French).
Extract and return ONLY a valid JSON object. No markdown, no explanation.

Return exactly this structure:
{
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
}

Rules:
- "forbidden_days"                : English day names e.g. ["Friday"]
- "trainer_availability"          : {"trainer name": "availability description"}
- "session_duration_override"     : integer in MINUTES (e.g. "1h30" → 90)
- "sessions_per_day"              : integer
- "break_between_sessions_minutes": integer in minutes
- "lunch_break_after_n_sessions"  : integer (after how many sessions)
- "lunch_break_duration_minutes"  : integer in minutes
- "day_start_time"                : "HH:MM" 24h format
- "min_room_capacity"             : integer
- "room_type_required"            : string e.g. "Lab"
- "group_priority"                : group name string
- "no_parallel_sessions_same_group": boolean
- "prefer_matching_specialization": boolean
- "other"                         : list of strings for anything else
- Fields not mentioned → keep default value
"""


# =============================================================================
#  LLM call helpers
# =============================================================================

def _call_llm(prompt: str, system: str) -> str:
    """Calls Ollama and returns raw text."""
    return _ask_ollama(prompt=prompt, system=system)


def _parse_json_object(raw: str) -> dict:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        return {}
    return json.loads(cleaned[start:end])


def _parse_json_array(raw: str) -> list:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start = cleaned.find("[")
    end   = cleaned.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    return json.loads(cleaned[start:end])


# =============================================================================
#  ANALYZER
# =============================================================================

class Analyzer:


    def analyze(self, constraint_input: ConstraintInput) -> ConstraintOutput:
        output = ConstraintOutput()

        # ── Step 1: Analyze pedagogical text ──────────────────────────────────
        pedagogical_constraints = []
        if constraint_input.pedagogical_text.strip():
            print(f"\n  [Analyzer] Extracting pedagogical constraints...")
            try:
                raw  = _call_llm(constraint_input.pedagogical_text, PEDAGOGICAL_PROMPT)
                print(f"  [Analyzer] Pedagogical raw: {raw[:200]}")
                items = _parse_json_array(raw)
                for item in items:
                    pedagogical_constraints.append(PedagogicalConstraint(
                        rule     = item.get("rule", ""),
                        severity = ConstraintSeverity(item.get("severity", "soft")),
                        category = item.get("category", "other"),
                        raw_text = constraint_input.pedagogical_text,
                    ))
                print(f"  [Analyzer] {len(pedagogical_constraints)} pedagogical rule(s) extracted.")
            except Exception as e:
                print(f"  [Analyzer] Pedagogical extraction failed: {e}")

        # ── Step 2: Analyze user scheduling text ──────────────────────────────
        user_constraints_dict = {}
        if constraint_input.user_text.strip():
            print(f"\n  [Analyzer] Extracting user scheduling constraints...")
            try:
                raw  = _call_llm(constraint_input.user_text, USER_CONSTRAINT_PROMPT)
                print(f"  [Analyzer] User raw: {raw[:200]}")
                user_constraints_dict = _parse_json_object(raw)
                print(f"  [Analyzer] User constraints: {user_constraints_dict}")
            except Exception as e:
                print(f"  [Analyzer] User extraction failed: {e}")

        # ── Step 3: Merge ISO constraints ─────────────────────────────────────
        for iso in constraint_input.iso_constraints:
            self._apply_iso(output, iso)

        # ── Step 4: Merge user constraints (override ISO if provided) ─────────
        self._apply_user_dict(output, user_constraints_dict)

        # ── Step 5: Collect pedagogical rules ─────────────────────────────────
        output.pedagogical_rules = [p.rule for p in pedagogical_constraints]

        print(f"\n  [Analyzer] Done. Output summary:")
        print(f"    forbidden_days={output.forbidden_days}")
        print(f"    session_duration={output.session_duration_override}min")
        print(f"    sessions_per_day={output.sessions_per_day}")
        print(f"    max_hours_per_day={output.max_hours_per_day}h (ISO)")
        print(f"    pedagogical_rules={output.pedagogical_rules}")

        return output

    # ──   ────────────────────────────────────────────────────────

    def _apply_iso(self, output: ConstraintOutput, iso: ISOConstraint):
        t = iso.constraint_type
        v = iso.value

        if   t == "max_hours_per_day":
            output.max_hours_per_day = float(v)
            output.sources["max_hours_per_day"] = "iso"

        elif t == "mandatory_break_minutes":
            # ISO mandatory break → maps to break_between_sessions_minutes
            if output.break_between_sessions_minutes is None:
                output.break_between_sessions_minutes = int(v)
                output.sources["break_between_sessions_minutes"] = "iso"

        elif t == "max_consecutive_sessions":
            output.max_consecutive_sessions = int(v)
            output.sources["max_consecutive_sessions"] = "iso"

        elif t == "min_break_between_sessions_minutes":
            if output.break_between_sessions_minutes is None:
                output.break_between_sessions_minutes = int(v)
                output.sources["break_between_sessions_minutes"] = "iso"

        elif t == "forbidden_days":
            days = v if isinstance(v, list) else [v]
            output.forbidden_days.extend(days)
            output.sources["forbidden_days"] = "iso"

        elif t == "sessions_per_day":
            output.sessions_per_day = int(v)
            output.sources["sessions_per_day"] = "iso"

        elif t == "lunch_break_after_n_sessions":
            output.lunch_break_after_n_sessions = int(v)
            output.sources["lunch_break_after_n_sessions"] = "iso"

        elif t == "lunch_break_duration_minutes":
            output.lunch_break_duration_minutes = int(v)
            output.sources["lunch_break_duration_minutes"] = "iso"

        elif t == "day_start_time":
            output.day_start_time = str(v)
            output.sources["day_start_time"] = "iso"

        else:
            output.other.append(f"[ISO] {t}: {v}")

    # ── User dict application ──────────────────────────────────────────────────

    def _apply_user_dict(self, output: ConstraintOutput, d: dict):
       
        if not d:
            return

        def _set(field, value, source="user"):
            if value is not None:
                setattr(output, field, value)
                output.sources[field] = source

        _set("session_duration_override",      d.get("session_duration_override"))
        _set("sessions_per_day",               d.get("sessions_per_day"))
        _set("break_between_sessions_minutes", d.get("break_between_sessions_minutes"))
        _set("lunch_break_after_n_sessions",   d.get("lunch_break_after_n_sessions"))
        _set("lunch_break_duration_minutes",   d.get("lunch_break_duration_minutes"))
        _set("day_start_time",                 d.get("day_start_time"))
        _set("min_room_capacity",              d.get("min_room_capacity"))
        _set("room_type_required",             d.get("room_type_required"))
        _set("group_priority",                 d.get("group_priority"))

        # Forbidden days: union with ISO
        user_forbidden = d.get("forbidden_days", [])
        if user_forbidden:
            output.forbidden_days = list(set(output.forbidden_days + user_forbidden))
            output.sources["forbidden_days"] = "user+iso" if "forbidden_days" in output.sources else "user"

        # Trainer availability: merge
        trainer_avail = d.get("trainer_availability", {})
        if trainer_avail:
            output.trainer_availability.update(trainer_avail)
            output.sources["trainer_availability"] = "user"

        # Booleans
        if d.get("no_parallel_sessions_same_group"):
            output.no_parallel_sessions_same_group = True
            output.sources["no_parallel_sessions_same_group"] = "user"
        if d.get("prefer_matching_specialization") is False:
            output.prefer_matching_specialization = False
            output.sources["prefer_matching_specialization"] = "user"

        # Other
        other = d.get("other", [])
        if other:
            output.other.extend(other)