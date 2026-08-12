from Services.constraintAgent.Schema import (
    ConstraintOutput,
    ISOConstraint,
    PedagogicalConstraint,
    ConstraintSeverity,
)


class ConstraintMerger:

    def merge(
        self,
        iso_constraints:  list[ISOConstraint],
        db_pedagogical:   list[PedagogicalConstraint],
        analyzer_output:  ConstraintOutput,
    ) -> ConstraintOutput:

        output = ConstraintOutput()

        # ── Step 1: Apply ISO constraints (highest priority) ─────────────────
        for iso in iso_constraints:
            if iso.severity == ConstraintSeverity.HARD:
                self._apply_iso_hard(output, iso)

        # ── Step 2: Apply user + soft ISO from analyzer output ────────────────
        # (analyzer already merged user + soft ISO)
        self._merge_analyzer_output(output, analyzer_output)

        # ── Step 3: Collect all pedagogical rules ─────────────────────────────
        # DB pedagogical rules + LLM-extracted pedagogical rules
        all_ped_rules = [p.rule for p in db_pedagogical] + analyzer_output.pedagogical_rules
        output.pedagogical_rules = list(dict.fromkeys(all_ped_rules))  # deduplicate preserving order

        # ── Step 4: Merge other ───────────────────────────────────────────────
        output.other = list(set(analyzer_output.other))

        # ── Step 5: Copy sources traceability ────────────────────────────────
        output.sources = {**analyzer_output.sources}

        print(f"\n  [Merger] Final ConstraintOutput:")
        print(f"    forbidden_days             = {output.forbidden_days}")
        print(f"    trainer_availability       = {output.trainer_availability}")
        print(f"    session_duration_override  = {output.session_duration_override}min")
        print(f"    sessions_per_day           = {output.sessions_per_day}")
        print(f"    max_hours_per_day          = {output.max_hours_per_day}h (ISO)")
        print(f"    max_consecutive_sessions   = {output.max_consecutive_sessions} (ISO)")
        print(f"    pedagogical_rules          = {output.pedagogical_rules}")

        return output

    def _apply_iso_hard(self, output: ConstraintOutput, iso: ISOConstraint):

        t, v = iso.constraint_type, iso.value

        if   t == "max_hours_per_day":
            output.max_hours_per_day = float(v)
            output.sources["max_hours_per_day"] = "iso_hard"

        elif t == "mandatory_break_minutes":
            # Hard ISO break overrides any user-set break if it's higher
            current = output.break_between_sessions_minutes or 0
            output.break_between_sessions_minutes = max(int(v), current)
            output.sources["break_between_sessions_minutes"] = "iso_hard"

        elif t == "max_consecutive_sessions":
            output.max_consecutive_sessions = int(v)
            output.sources["max_consecutive_sessions"] = "iso_hard"

        elif t == "min_break_between_sessions_minutes":
            current = output.break_between_sessions_minutes or 0
            output.break_between_sessions_minutes = max(int(v), current)
            output.sources["break_between_sessions_minutes"] = "iso_hard"

        elif t == "forbidden_days":
            days = v if isinstance(v, list) else [v]
            output.forbidden_days = list(set(output.forbidden_days + days))
            output.sources["forbidden_days"] = "iso_hard"

    def _merge_analyzer_output(self, output: ConstraintOutput, analyzer: ConstraintOutput):

        def _set_if_none(field: str, value):
            """Set a field only if not already set by ISO HARD."""
            source = output.sources.get(field, "")
            if source != "iso_hard" and value is not None:
                setattr(output, field, value)
                if field not in output.sources:
                    output.sources[field] = analyzer.sources.get(field, "analyzer")

        _set_if_none("session_duration_override",      analyzer.session_duration_override)
        _set_if_none("sessions_per_day",               analyzer.sessions_per_day)
        _set_if_none("lunch_break_after_n_sessions",   analyzer.lunch_break_after_n_sessions)
        _set_if_none("lunch_break_duration_minutes",   analyzer.lunch_break_duration_minutes)
        _set_if_none("day_start_time",                 analyzer.day_start_time)
        _set_if_none("min_room_capacity",              analyzer.min_room_capacity)
        _set_if_none("room_type_required",             analyzer.room_type_required)
        _set_if_none("group_priority",                 analyzer.group_priority)

        # Forbidden days: always union (ISO hard already applied)
        extra = [d for d in analyzer.forbidden_days if d not in output.forbidden_days]
        output.forbidden_days.extend(extra)

        # Trainer availability: merge
        output.trainer_availability.update(analyzer.trainer_availability)

        # Break: take the maximum (strictest) if both set
        if analyzer.break_between_sessions_minutes is not None:
            current = output.break_between_sessions_minutes or 0
            if output.sources.get("break_between_sessions_minutes") != "iso_hard":
                output.break_between_sessions_minutes = max(
                    analyzer.break_between_sessions_minutes, current
                )

        # Booleans
        if analyzer.no_parallel_sessions_same_group:
            output.no_parallel_sessions_same_group = True
        if analyzer.prefer_matching_specialization is False:
            output.prefer_matching_specialization = False

    # ==========================================================================
    #  CONVERT to planning_agent-compatible dict
    # ==========================================================================

    @staticmethod
    def to_planning_dict(output: ConstraintOutput) -> dict:

        return {
            "forbidden_days":                    output.forbidden_days,
            "trainer_availability":              output.trainer_availability,
            "session_duration_override":         output.session_duration_override,
            "sessions_per_day":                  output.sessions_per_day,
            "break_between_sessions_minutes":    output.break_between_sessions_minutes,
            "lunch_break_after_n_sessions":      output.lunch_break_after_n_sessions,
            "lunch_break_duration_minutes":      output.lunch_break_duration_minutes,
            "day_start_time":                    output.day_start_time,
            "min_room_capacity":                 output.min_room_capacity,
            "room_type_required":                output.room_type_required,
            "group_priority":                    output.group_priority,
            "no_parallel_sessions_same_group":   output.no_parallel_sessions_same_group,
            "prefer_matching_specialization":    output.prefer_matching_specialization,
            "other":                             output.other + output.pedagogical_rules,
            # max_hours_per_day and max_consecutive_sessions are used
            # by the Validator, not directly by the PlanningAgent scheduler
        }