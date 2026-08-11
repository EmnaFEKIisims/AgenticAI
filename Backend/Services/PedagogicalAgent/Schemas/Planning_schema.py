"""
schemas/planning_schema.py
===========================
Pydantic models defining the planning format consumed by the Pedagogical Agent.

These models are the single source of truth for what a "planning" looks like.
Every validator, every service, and the agent itself works with these types.

Hierarchy:
    Planning
        └── Day[]
               └── Session[]
                        └── course, teacher, room, timeslot, type...
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import time, date
from typing import Optional


# =============================================================================
#  ENUMS
# =============================================================================

class SessionType(str, Enum):
    """
    The pedagogical type of a session.
    This is what drives most of the audit rules.
    """
    THEORY       = "theory"        # cours magistral, lecture
    PRACTICE     = "practice"      # TP, lab, hands-on
    EVALUATION   = "evaluation"    # test, exam, quiz
    PROJECT      = "project"       # projet, atelier
    PRESENTATION = "presentation"  # exposé, soutenance
    WORKSHOP     = "workshop"      # atelier mixte
    REVIEW       = "review"        # révision, récapitulatif
    OTHER        = "other"


class DifficultyLevel(str, Enum):
    """
    Cognitive difficulty of a course.
    Used by the workload validator to detect overloaded days.
    """
    EASY   = "easy"      # introductory, overview
    MEDIUM = "medium"    # standard course
    HARD   = "hard"      # advanced, complex, high concentration required


class RoomType(str, Enum):
    """Room types relevant to pedagogical audit."""
    CLASSROOM   = "classroom"
    LAB         = "lab"           # computer lab, science lab
    WORKSHOP    = "workshop"      # atelier
    AMPHITHEATER = "amphitheater"
    VIRTUAL     = "virtual"       # online / remote
    OTHER       = "other"


class WeekDay(str, Enum):
    MONDAY    = "Monday"
    TUESDAY   = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY  = "Thursday"
    FRIDAY    = "Friday"
    SATURDAY  = "Saturday"
    SUNDAY    = "Sunday"


# =============================================================================
#  SESSION
# =============================================================================

class Session(BaseModel):
    """
    A single training session — the atomic unit of a planning.

    One session = one course + one teacher + one room + one time slot.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    session_id:   Optional[int]   = Field(None,  description="DB ID of the ScheduleSlot")
    course_id:    Optional[int]   = Field(None,  description="DB ID of the course")
    trainer_id:   Optional[int]   = Field(None,  description="DB ID of the trainer")
    room_id:      Optional[int]   = Field(None,  description="DB ID of the room")
    group_id:     Optional[int]   = Field(None,  description="DB ID of the learner group")

    # ── Display / human-readable names ────────────────────────────────────────
    course:       str             = Field(..., description="Course title")
    teacher:      str             = Field(..., description="Trainer name")
    room:         str             = Field(..., description="Room name or code")
    group:        str             = Field("",  description="Learner group name")

    # ── When ──────────────────────────────────────────────────────────────────
    day:          WeekDay         = Field(..., description="Day of the week")
    start:        str             = Field(..., description="Start time HH:MM (24h)")
    end:          str             = Field(..., description="End time   HH:MM (24h)")

    # ── Pedagogical metadata ──────────────────────────────────────────────────
    session_type: SessionType     = Field(SessionType.THEORY,
                                          description="Theory / Practice / Evaluation / ...")
    difficulty:   DifficultyLevel = Field(DifficultyLevel.MEDIUM,
                                          description="Cognitive difficulty of the session")
    room_type:    RoomType        = Field(RoomType.CLASSROOM,
                                          description="Type of room used")

    # ── Optional pedagogical context ──────────────────────────────────────────
    prerequisites:    list[str]   = Field(default_factory=list,
                                          description="List of course titles that must come before this one")
    objectives:       list[str]   = Field(default_factory=list,
                                          description="Learning objectives of this session")

    # ── Computed (read-only, set by validators) ────────────────────────────────
    duration_minutes: Optional[float] = Field(None, description="Duration in minutes (computed)")

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Time must be HH:MM, got: '{v}'")
        h, m = parts
        if not (h.isdigit() and m.isdigit()):
            raise ValueError(f"Time must be HH:MM with digits, got: '{v}'")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError(f"Invalid time value: '{v}'")
        return f"{int(h):02d}:{int(m):02d}"

    @model_validator(mode="after")
    def compute_duration(self) -> Session:
        """Auto-computes duration_minutes from start/end."""
        try:
            sh, sm = map(int, self.start.split(":"))
            eh, em = map(int, self.end.split(":"))
            self.duration_minutes = (eh * 60 + em) - (sh * 60 + sm)
            if self.duration_minutes <= 0:
                raise ValueError(f"End time must be after start time ({self.start} → {self.end})")
        except Exception as e:
            pass  # duration stays None if times are invalid
        return self

    @property
    def start_minutes(self) -> int:
        """Start time as minutes since midnight. Useful for sorting and overlap checks."""
        h, m = map(int, self.start.split(":"))
        return h * 60 + m

    @property
    def end_minutes(self) -> int:
        """End time as minutes since midnight."""
        h, m = map(int, self.end.split(":"))
        return h * 60 + m

    @property
    def is_practice(self) -> bool:
        return self.session_type == SessionType.PRACTICE

    @property
    def is_theory(self) -> bool:
        return self.session_type == SessionType.THEORY

    @property
    def is_evaluation(self) -> bool:
        return self.session_type == SessionType.EVALUATION

    @property
    def is_hard(self) -> bool:
        return self.difficulty == DifficultyLevel.HARD


# =============================================================================
#  DAY PLANNING
# =============================================================================

class DayPlanning(BaseModel):
    """
    All sessions scheduled for a single day.
    This is the primary unit of analysis for most validators.
    """
    day:      WeekDay        = Field(..., description="The day")
    sessions: list[Session]  = Field(default_factory=list)

    @property
    def sessions_sorted(self) -> list[Session]:
        """Sessions ordered by start time — required for sequence analysis."""
        return sorted(self.sessions, key=lambda s: s.start_minutes)

    @property
    def total_hours(self) -> float:
        """Total training hours for this day."""
        return sum(s.duration_minutes or 0 for s in self.sessions) / 60

    @property
    def hard_session_count(self) -> int:
        return sum(1 for s in self.sessions if s.is_hard)

    @property
    def unique_teachers(self) -> set[str]:
        return {s.teacher for s in self.sessions}

    @property
    def unique_courses(self) -> set[str]:
        return {s.course for s in self.sessions}


# =============================================================================
#  PLANNING  (full planning — input to the Pedagogical Agent)
# =============================================================================

class Planning(BaseModel):
    """
    A complete training planning.
    This is what the Pedagogical Agent receives as input.

    It can be built from:
      - The PlanningAgent output (schedule list[dict])
      - The ScheduleSlot DB records
      - A direct JSON payload to the API
    """

    planning_id:  Optional[int]   = Field(None, description="DB planning ID if available")
    group_name:   Optional[str]   = Field(None, description="Name of the learner group")
    sessions:     list[Session]   = Field(default_factory=list,
                                          description="All sessions in this planning")

    # ── Derived views ──────────────────────────────────────────────────────────

    @property
    def days(self) -> list[DayPlanning]:
        """Groups sessions by day. Returns DayPlanning list sorted Mon → Sun."""
        day_order = [d.value for d in WeekDay]
        grouped: dict[str, list[Session]] = {}
        for s in self.sessions:
            grouped.setdefault(s.day.value, []).append(s)
        return [
            DayPlanning(day=WeekDay(d), sessions=grouped[d])
            for d in day_order if d in grouped
        ]

    @property
    def sessions_by_teacher(self) -> dict[str, list[Session]]:
        """Groups sessions by teacher name."""
        result: dict[str, list[Session]] = {}
        for s in self.sessions:
            result.setdefault(s.teacher, []).append(s)
        return result

    @property
    def sessions_by_course(self) -> dict[str, list[Session]]:
        """Groups sessions by course title."""
        result: dict[str, list[Session]] = {}
        for s in self.sessions:
            result.setdefault(s.course, []).append(s)
        return result

    @property
    def total_hours(self) -> float:
        return sum(s.duration_minutes or 0 for s in self.sessions) / 60

    @property
    def unique_courses(self) -> list[str]:
        return sorted({s.course for s in self.sessions})

    @property
    def unique_teachers(self) -> list[str]:
        return sorted({s.teacher for s in self.sessions})

    # ── Factory: build from PlanningAgent output ───────────────────────────────

    @classmethod
    def from_schedule(cls, schedule: list[dict], group_name: str = "") -> "Planning":
        """
        Builds a Planning from the PlanningAgent output (list of session dicts).

        The PlanningAgent produces dicts with keys:
          course_title, trainer_name, room_name, group_name,
          suggested_day, suggested_time, session_number, ...

        Maps 'suggested_day' (e.g. "Week 1 — Monday") → WeekDay.
        Maps 'suggested_time' (e.g. "08:00 → 11:00") → start + end.
        """
        sessions = []

        for s in schedule:
            try:
                # Parse day: "Week 1 — Monday" → "Monday"
                raw_day = s.get("suggested_day", "")
                day_name = raw_day.split("—")[-1].strip() if "—" in raw_day else raw_day.strip()

                # Parse time: "08:00 → 11:00" → start="08:00", end="11:00"
                raw_time = s.get("suggested_time", "")
                if "→" in raw_time:
                    start, end = [t.strip() for t in raw_time.split("→")]
                elif "-" in raw_time:
                    start, end = [t.strip() for t in raw_time.split("-")]
                else:
                    start, end = "08:00", "11:00"   # fallback

                sessions.append(Session(
                    session_id    = s.get("session_number"),
                    course_id     = s.get("course_id"),
                    trainer_id    = s.get("trainer_id"),
                    room_id       = s.get("room_id"),
                    course        = s.get("course_title", "Unknown"),
                    teacher       = s.get("trainer_name", "Unknown"),
                    room          = s.get("room_name",    "Unknown"),
                    group         = s.get("group_name",   group_name),
                    day           = WeekDay(day_name),
                    start         = start,
                    end           = end,
                    session_type  = SessionType.THEORY,    # default; enriched later
                    difficulty    = DifficultyLevel.MEDIUM,
                    room_type     = RoomType.CLASSROOM,
                ))
            except Exception as e:
                print(f"  [Planning.from_schedule] Skipped session: {e} | {s}")

        return cls(sessions=sessions, group_name=group_name)