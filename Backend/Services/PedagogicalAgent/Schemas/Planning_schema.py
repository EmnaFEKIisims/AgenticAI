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

import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import time, date, datetime
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

    # ── Week number — see Planning.days docstring for why this matters ────────
    week: Optional[int] = Field(None, description=(
        "Week number of the multi-week program this session belongs to "
        "(parsed from a 'Week N' label, or the ISO calendar week when only "
        "start_time is available). Without this, every 'Monday' across an "
        "entire multi-week program collapses into a single WeekDay bucket, "
        "so a 6-week program's six separate 3h Mondays get summed into one "
        "fake 18h day."
    ))

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

    @property
    def day_key(self) -> tuple:
        """
        Identifies ONE real calendar day: (week, weekday) when a week number
        is known, so the same weekday across different weeks is never
        merged. Falls back to weekday-only (old behavior) when no week
        number could be determined — e.g. a genuinely single-week schedule.
        """
        return (self.week, self.day.value)


# =============================================================================
#  DAY PLANNING
# =============================================================================

class DayPlanning(BaseModel):
    """
    All sessions scheduled for ONE real calendar day — i.e. a specific
    (week, weekday) combination, not just "all sessions on a Monday
    regardless of which week". See Planning.days for why that distinction
    matters for a multi-week program.
    """
    day:      WeekDay        = Field(..., description="The weekday")
    week:     Optional[int]  = Field(None, description="Week number, when known")
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

# Module-level constants used by Planning.from_schedule() below.
#
# IMPORTANT: these must NOT be defined as attributes inside the Planning
# class body. Pydantic v2 auto-converts any leading-underscore class
# attribute on a BaseModel into a `ModelPrivateAttr` descriptor — so
# `cls._DAY_NAMES` would return that descriptor object, not the list,
# and `cls._DAY_NAMES[i]` blows up with "'ModelPrivateAttr' object is not
# subscriptable" for every single session. Keeping them as plain module
# globals sidesteps that entirely.

# English weekday names, index = Python's datetime.weekday() (0=Monday).
# Used instead of strftime("%A") so the result never depends on the
# server's locale (a server set to fr_FR would otherwise produce "lundi"
# and silently break every WeekDay(...) lookup below).
_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Map a few common free-text hints to SessionType / DifficultyLevel,
# used only as a fallback when the schedule dict doesn't carry an explicit
# value (see from_schedule below). Keeps old untyped data working while
# letting enriched data (once the planner/DB provides it) take priority.
_SESSION_TYPE_HINTS = {
    "tp": SessionType.PRACTICE, "practice": SessionType.PRACTICE, "lab": SessionType.PRACTICE,
    "exam": SessionType.EVALUATION, "test": SessionType.EVALUATION, "quiz": SessionType.EVALUATION,
    "evaluation": SessionType.EVALUATION, "project": SessionType.PROJECT,
    "workshop": SessionType.WORKSHOP, "review": SessionType.REVIEW,
}
_DIFFICULTY_HINTS = {
    "easy": DifficultyLevel.EASY, "intro": DifficultyLevel.EASY, "basics": DifficultyLevel.EASY,
    "advanced": DifficultyLevel.HARD, "hard": DifficultyLevel.HARD, "expert": DifficultyLevel.HARD,
}


class Planning(BaseModel):
    """
    A complete training planning.
    This is what the Pedagogical Agent receives as input.

    IMPORTANT — scope: a Planning should represent the schedule of a SINGLE
    learner group. Every validator (workload, breaks, consecutive hours...)
    sums hours and gaps across ALL sessions it is given, on the assumption
    that they all belong to the same learners. Build one Planning PER GROUP
    (see PedagogicalAgent.generate_report(), which now splits a multi-group
    schedule automatically) — never merge several groups' sessions into one
    Planning, or a day with 5 groups in parallel at 08:00 will be scored as
    if one learner attended all 5 at once (15h "in one day" instead of 3h).

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
        """
        Groups sessions into real calendar days: (week, weekday), not just
        weekday. A multi-week program has several different "Mondays" —
        grouping by weekday alone would sum week 1's Monday, week 2's
        Monday, week 3's Monday, etc. into one fake day, massively
        inflating the hours every daily-workload/break/consecutive-hours
        check compares against the per-day limit. Falls back to
        weekday-only grouping when no session carries a week number (a
        genuinely single-week schedule), which keeps old behavior intact.

        Sorted by week number first, then Mon → Sun within each week.
        """
        day_order = [d.value for d in WeekDay]
        grouped: dict[tuple, list[Session]] = {}
        for s in self.sessions:
            grouped.setdefault(s.day_key, []).append(s)

        def sort_key(key: tuple):
            week, day = key
            return (
                week if week is not None else -1,
                day_order.index(day) if day in day_order else 99,
            )

        return [
            DayPlanning(day=WeekDay(day), week=week, sessions=grouped[(week, day)])
            for (week, day) in sorted(grouped.keys(), key=sort_key)
        ]

    @property
    def weeks(self) -> dict[Optional[int], float]:
        """
        Total hours PER WEEK — used by validate_weekly_workload to check
        each calendar week against the weekly limit separately, instead of
        comparing the whole multi-week program's grand total against a
        single week's limit (which would fail by definition for any
        program longer than one week).

        Key is None when no session carries a week number — in that case
        the whole dict collapses to one bucket, same as the old behavior.
        """
        result: dict[Optional[int], float] = {}
        for s in self.sessions:
            result[s.week] = result.get(s.week, 0.0) + (s.duration_minutes or 0) / 60
        return result

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

    @property
    def unique_groups(self) -> list[str]:
        """All distinct group names found in this planning's sessions."""
        return sorted({s.group for s in self.sessions if s.group})

    # ── Factory: build from PlanningAgent output ───────────────────────────────

    @classmethod
    def _infer_session_type(cls, s: dict) -> SessionType:
        # 1) explicit field on the schedule dict (preferred — set by the caller
        #    from the Course record once available)
        explicit = s.get("session_type")
        if explicit:
            try:
                return SessionType(str(explicit).lower())
            except ValueError:
                pass
        # 2) fallback: guess from the course title
        title = str(s.get("course_title", "")).lower()
        for hint, value in _SESSION_TYPE_HINTS.items():
            if hint in title:
                return value
        return SessionType.THEORY

    @classmethod
    def _infer_difficulty(cls, s: dict) -> DifficultyLevel:
        explicit = s.get("difficulty")
        if explicit:
            try:
                return DifficultyLevel(str(explicit).lower())
            except ValueError:
                pass
        title = str(s.get("course_title", "")).lower()
        for hint, value in _DIFFICULTY_HINTS.items():
            if hint in title:
                return value
        return DifficultyLevel.MEDIUM

    @classmethod
    def _infer_room_type(cls, s: dict) -> RoomType:
        explicit = s.get("room_type")
        if explicit:
            try:
                return RoomType(str(explicit).lower())
            except ValueError:
                pass
        name = str(s.get("room_name", "")).lower()
        if "lab" in name:
            return RoomType.LAB
        if "amphi" in name or "conference" in name:
            return RoomType.AMPHITHEATER
        return RoomType.CLASSROOM

    @classmethod
    def _parse_iso_datetime(cls, raw) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return None

    @classmethod
    def _resolve_day(cls, s: dict) -> Optional[str]:
        """
        Determines the day of week for a schedule dict, trying — in order:
          1) an explicit 'day' field (direct session input)
          2) the real ISO 'start_time' (most reliable — immune to however
             'suggested_day' happens to be formatted/punctuated)
          3) a substring search for a day name inside 'suggested_day',
             e.g. "Week 1 — Monday", "Week 1 - Monday", "Week 1 (Monday)"
             all match regardless of which separator character is used.
        """
        explicit = s.get("day")
        if explicit:
            for day in _DAY_NAMES:
                if day.lower() == str(explicit).strip().lower():
                    return day

        dt = cls._parse_iso_datetime(s.get("start_time"))
        if dt is not None:
            return _DAY_NAMES[dt.weekday()]

        raw_day = str(s.get("suggested_day") or "")
        for day in _DAY_NAMES:
            if day.lower() in raw_day.lower():
                return day

        return None

    @classmethod
    def _resolve_week(cls, s: dict) -> Optional[int]:
        """
        Determines the program week number for a schedule dict, trying:
          1) an explicit 'week' field
          2) a "Week N" pattern inside 'suggested_day' (e.g. "Week 1 — Monday")
          3) the ISO calendar week derived from 'start_time' (year*100+week,
             so weeks never collide across a year boundary)
        Returns None only if nothing at all is available — in that case
        every session collapses to the old weekday-only grouping.
        """
        explicit = s.get("week")
        if explicit is not None:
            try:
                return int(explicit)
            except (TypeError, ValueError):
                pass

        raw_day = str(s.get("suggested_day") or "")
        m = re.search(r"week\s*(\d+)", raw_day, re.IGNORECASE)
        if m:
            return int(m.group(1))

        dt = cls._parse_iso_datetime(s.get("start_time"))
        if dt is not None:
            iso_year, iso_week, _ = dt.isocalendar()
            return iso_year * 100 + iso_week

        return None

    @classmethod
    def _resolve_times(cls, s: dict) -> tuple[Optional[str], Optional[str]]:
        """
        Determines start/end "HH:MM" for a schedule dict, trying — in order:
          1) explicit 'start'/'end' fields (direct session input)
          2) the real ISO 'start_time'/'end_time' (most reliable)
          3) any "HH:MM" pattern found in 'suggested_time', regardless of
             the separator used between them ("→", "-", "–", "to", ...)
        """
        if s.get("start") and s.get("end"):
            return str(s["start"]).strip(), str(s["end"]).strip()

        sdt = cls._parse_iso_datetime(s.get("start_time"))
        edt = cls._parse_iso_datetime(s.get("end_time"))
        if sdt is not None and edt is not None:
            return sdt.strftime("%H:%M"), edt.strftime("%H:%M")

        raw_time = str(s.get("suggested_time") or "")
        times = re.findall(r"(\d{1,2}:\d{2})", raw_time)
        if len(times) >= 2:
            return times[0], times[1]

        return None, None

    @classmethod
    def from_schedule(cls, schedule: list[dict], group_name: str = "") -> "Planning":
        """
        Builds a Planning from the PlanningAgent output (list of session dicts).

        The real payload sent by the frontend (ScheduleGrid / Pedagogical.tsx)
        carries BOTH a human-readable pair ('suggested_day'/'suggested_time',
        e.g. "Week 1 — Monday" / "08:00 → 11:00") AND the authoritative ISO
        pair ('start_time'/'end_time', e.g. "2025-09-01T08:00:00"). The ISO
        pair is parsed first since it can't be broken by punctuation/locale —
        the display strings are only a fallback for inputs that don't carry
        start_time/end_time at all.

        Any field that is present in the dict but explicitly null (common for
        a draft slot — e.g. 'group_name': null before a group is assigned)
        is treated as missing, not as the literal value None, so it never
        reaches a required str field on Session.

        session_type / difficulty / room_type are taken from the dict when
        present (so the caller can enrich from the Course/Room DB records),
        and otherwise guessed from the course/room names — never silently
        forced to theory/medium/classroom for every session.
        """
        sessions = []
        skipped  = []

        for s in schedule:
            slot_id = s.get("id") or s.get("session_number")
            try:
                day_name = cls._resolve_day(s)
                if not day_name:
                    raise ValueError(
                        f"could not determine day of week "
                        f"(suggested_day={s.get('suggested_day')!r}, "
                        f"start_time={s.get('start_time')!r})"
                    )

                start, end = cls._resolve_times(s)
                if not start or not end:
                    raise ValueError(
                        f"could not determine start/end time "
                        f"(suggested_time={s.get('suggested_time')!r}, "
                        f"start_time={s.get('start_time')!r}, "
                        f"end_time={s.get('end_time')!r})"
                    )

                sessions.append(Session(
                    session_id    = slot_id,
                    course_id     = s.get("course_id"),
                    trainer_id    = s.get("trainer_id"),
                    room_id       = s.get("room_id"),
                    group_id      = s.get("group_id"),
                    course        = s.get("course_title") or "Unknown",
                    teacher       = s.get("trainer_name") or "Unknown",
                    room          = s.get("room_name")    or "Unknown",
                    group         = s.get("group_name")   or group_name or "",
                    day           = WeekDay(day_name),
                    start         = start,
                    end           = end,
                    session_type  = cls._infer_session_type(s),
                    difficulty    = cls._infer_difficulty(s),
                    room_type     = cls._infer_room_type(s),
                    week          = cls._resolve_week(s),
                ))
            except Exception as e:
                skipped.append((slot_id, str(e)))
                print(f"  [Planning.from_schedule] Skipped session id={slot_id}: {e}")

        if skipped:
            print(
                f"[Planning.from_schedule] {len(skipped)}/{len(schedule)} "
                f"session(s) skipped — ids: {[sid for sid, _ in skipped]}"
            )

        return cls(sessions=sessions, group_name=group_name)