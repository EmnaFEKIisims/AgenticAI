"""
Services/RAG/memory_extractor.py
==================================
Decides WHAT to extract and store from user interactions.

The system must NOT store everything blindly.
It must ask: "Does this interaction contain durable, useful information?"

Sources:
  - Planning rejection  → reason is extracted as USER_FEEDBACK + DECISION_HISTORY
  - Planning validation → positive signal → PLANNING_HISTORY
  - Drag & Drop move    → may indicate preference if it matches a pattern
  - Anomaly detection   → conflict pattern → CONFLICT_CORRECTION
  - Explicit feedback   → directly stored as USER_FEEDBACK
"""

from dataclasses import dataclass
from rag.memory_types import MemoryType


@dataclass
class ExtractedMemory:
    content:     str
    memory_type: MemoryType
    importance:  int      = 2         # 1=low 2=medium 3=high
    confidence:  float    = 1.0       # how certain (1.0=explicit, 0.5=inferred)
    tags:        list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MemoryExtractor:
    """
    Extracts meaningful memories from planning system events.
    Uses simple heuristics — can be upgraded to LLM-based extraction.
    """

    # ── Planning Rejection ────────────────────────────────────────────────────

    def from_rejection(self, reason: str, planning_id: str = "") -> list[ExtractedMemory]:
        """
        Extracts memories from a planning rejection.
        A rejection always contains valuable negative feedback.
        """
        memories = []
        if not reason.strip():
            return memories

        # The rejection reason itself
        memories.append(ExtractedMemory(
            content     = f"Planning rejected: {reason}",
            memory_type = MemoryType.USER_FEEDBACK,
            importance  = 3,
            confidence  = 1.0,
            tags        = ["rejection", "negative_feedback"],
        ))

        # Extract implied preferences from rejection keywords
        reason_lower = reason.lower()
        prefs = self._extract_preferences_from_text(reason_lower)
        memories.extend(prefs)

        return memories

    # ── Planning Validation ───────────────────────────────────────────────────

    def from_validation(
        self,
        schedule:    list[dict],
        constraints: dict,
        notes:       str = "",
    ) -> list[ExtractedMemory]:
        """
        Extracts memories from a validated planning.
        Validation = positive signal about this type of schedule.
        """
        memories = []

        # General positive signal
        constraint_summary = self._summarize_constraints(constraints)
        memories.append(ExtractedMemory(
            content     = f"Planning validated successfully. {constraint_summary}",
            memory_type = MemoryType.PLANNING_HISTORY,
            importance  = 2,
            confidence  = 1.0,
            tags        = ["validated", "positive"],
        ))

        if notes:
            memories.append(ExtractedMemory(
                content     = f"Admin note on validated planning: {notes}",
                memory_type = MemoryType.USER_FEEDBACK,
                importance  = 3,
                tags        = ["admin_note"],
            ))

        # Extract time preferences from the accepted schedule
        time_pref = self._extract_time_preference(schedule)
        if time_pref:
            memories.append(time_pref)

        return memories

    # ── Drag & Drop Move ──────────────────────────────────────────────────────

    def from_move(
        self,
        course_title: str,
        from_day:     str,
        to_day:       str,
        from_time:    str,
        to_time:      str,
        admin_note:   str = "",
    ) -> list[ExtractedMemory]:
        """
        Extracts memories from a drag & drop move.
        One move may indicate preference; store as medium confidence.
        """
        memories = []

        move_desc = (
            f"Admin moved '{course_title}' from {from_day} {from_time} "
            f"to {to_day} {to_time}."
        )
        memories.append(ExtractedMemory(
            content     = move_desc,
            memory_type = MemoryType.DECISION_HISTORY,
            importance  = 2,
            confidence  = 0.7,    # one move = moderate confidence
            tags        = ["drag_drop", "schedule_adjustment"],
        ))

        if admin_note:
            memories.append(ExtractedMemory(
                content     = f"Move reason: {admin_note}",
                memory_type = MemoryType.USER_FEEDBACK,
                importance  = 3,
                confidence  = 1.0,
                tags        = ["explicit_reason"],
            ))

        return memories

    # ── Anomaly Detected ──────────────────────────────────────────────────────

    def from_anomaly(
        self,
        anomaly_type: str,
        description:  str,
        resolution:   str = "",
    ) -> list[ExtractedMemory]:
        """
        Extracts conflict patterns from detected anomalies.
        Helps future plannings avoid the same issues.
        """
        content = f"Conflict detected: {description}"
        if resolution:
            content += f" Resolution: {resolution}"

        return [ExtractedMemory(
            content     = content,
            memory_type = MemoryType.CONFLICT_CORRECTION,
            importance  = 3,
            confidence  = 1.0,
            tags        = ["anomaly", anomaly_type.lower()],
        )]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_preferences_from_text(self, text: str) -> list[ExtractedMemory]:
        """Extracts implied preferences from rejection/feedback text."""
        prefs = []
        keywords = {
            "monday":    "Administrator wants lighter Monday schedule",
            "friday":    "Administrator prefers to avoid sessions on Friday",
            "morning":   "Administrator prefers morning sessions",
            "afternoon": "Administrator avoids heavy afternoon sessions",
            "overload":  "Administrator wants more balanced trainer workload",
            "break":     "Administrator wants more breaks between sessions",
            "heavy":     "Administrator prefers lighter daily schedule",
            "too many":  "Administrator wants fewer sessions per day",
        }
        for kw, pref in keywords.items():
            if kw in text:
                prefs.append(ExtractedMemory(
                    content     = pref,
                    memory_type = MemoryType.USER_PREFERENCE,
                    importance  = 2,
                    confidence  = 0.6,    # inferred from text
                    tags        = ["inferred", kw],
                ))
        return prefs

    def _extract_time_preference(self, schedule: list[dict]) -> ExtractedMemory | None:
        """Infers time preference from accepted schedule's time distribution."""
        if not schedule:
            return None
        times = [s.get("suggested_time", "") for s in schedule if s.get("suggested_time")]
        morning_count   = sum(1 for t in times if t.startswith("08") or t.startswith("09") or t.startswith("10"))
        afternoon_count = sum(1 for t in times if t.startswith("14") or t.startswith("15") or t.startswith("16"))
        total = len(times)
        if total == 0:
            return None

        if morning_count / total > 0.6:
            return ExtractedMemory(
                content     = "Administrator's accepted planning is heavily morning-focused (08:00-11:00)",
                memory_type = MemoryType.USER_PREFERENCE,
                importance  = 1,
                confidence  = 0.5,
                tags        = ["inferred", "morning_preference"],
            )
        return None

    def _summarize_constraints(self, constraints: dict) -> str:
        parts = []
        if constraints.get("forbidden_days"):
            parts.append(f"No sessions on {', '.join(constraints['forbidden_days'])}")
        if constraints.get("day_start_time"):
            parts.append(f"Day starts at {constraints['day_start_time']}")
        return ". ".join(parts) if parts else "Default constraints."