"""
Services/AnomalyAgent/classifier.py
=====================================
Classifies raw anomaly dicts into typed, categorized anomalies.

Input:  raw anomaly dict from detector.py
Output: enriched dict with:
  - anomaly_type  (from AnomalyType enum)
  - severity      (high / medium / low)
  - category      (conflict / overload / compliance / capacity / schedule)
  - iso_reference (mapped ISO standard)

Example:
  Raw: {"anomaly_type": "teacher_overload", ...}
  →   type=TEACHER_OVERLOAD  severity=HIGH  category=overload
"""

from models.anomaly import AnomalyType, AnomalySeverity


# =============================================================================
#  CLASSIFICATION MAP
#  raw_type → (AnomalyType, AnomalySeverity, category, iso_reference)
# =============================================================================

CLASSIFICATION_MAP: dict[str, tuple[AnomalyType, AnomalySeverity, str, str]] = {

    # ── Conflicts ───────────────────────────────────────────────────────────
    "trainer_conflict": (
        AnomalyType.OTHER,
        AnomalySeverity.HIGH,
        "conflict",
        "ISO 21001:2018 §7.1.2",
    ),
    "room_conflict": (
        AnomalyType.OTHER,
        AnomalySeverity.HIGH,
        "conflict",
        "ISO 21001:2018 §7.1.3",
    ),
    "learner_conflict": (
        AnomalyType.OTHER,
        AnomalySeverity.HIGH,
        "conflict",
        "ISO 21001:2018 §8.3",
    ),
    "equipment_conflict": (
        AnomalyType.OTHER,
        AnomalySeverity.MEDIUM,
        "conflict",
        "ISO 21001:2018 §7.1.3",
    ),

    # ── Overload ────────────────────────────────────────────────────────────
    "teacher_overload": (
        AnomalyType.OTHER,
        AnomalySeverity.HIGH,
        "overload",
        "ISO 21001:2018 §7.1.2 / ISO 29993:2017 §5.2",
    ),
    "workload_exceeded": (
        AnomalyType.WORKLOAD_EXCEEDED,
        AnomalySeverity.HIGH,
        "overload",
        "ISO 21001:2018 §8.3",
    ),

    # ── Compliance (pedagogical) ─────────────────────────────────────────────
    "wrong_progression": (
        AnomalyType.WRONG_PROGRESSION,
        AnomalySeverity.HIGH,
        "compliance",
        "ISO 29993:2017 §6.3",
    ),
    "practice_before_theory": (
        AnomalyType.PRACTICE_BEFORE_THEORY,
        AnomalySeverity.HIGH,
        "compliance",
        "ISO 29993:2017 §6.3.3",
    ),
    "prerequisite_violated": (
        AnomalyType.PREREQUISITE_VIOLATED,
        AnomalySeverity.HIGH,
        "compliance",
        "ISO 21001:2018 §8.2",
    ),
    "evaluation_misplaced": (
        AnomalyType.EVALUATION_MISPLACED,
        AnomalySeverity.MEDIUM,
        "compliance",
        "ISO 29993:2017 §6.3",
    ),
    "insufficient_break": (
        AnomalyType.INSUFFICIENT_BREAK,
        AnomalySeverity.HIGH,
        "compliance",
        "ISO 21001:2018 §8.3 / ISO 29993:2017 §6.2",
    ),

    # ── Capacity ────────────────────────────────────────────────────────────
    "room_capacity_insufficient": (
        AnomalyType.ROOM_CAPACITY_INSUFFICIENT,
        AnomalySeverity.MEDIUM,
        "capacity",
        "ISO 21001:2018 §7.1.3",
    ),
    "wrong_room_type": (
        AnomalyType.WRONG_ROOM_TYPE,
        AnomalySeverity.LOW,
        "capacity",
        "ISO 21001:2018 §7.1.3",
    ),

    # ── Schedule ─────────────────────────────────────────────────────────────
    "other": (
        AnomalyType.OTHER,
        AnomalySeverity.MEDIUM,
        "schedule",
        "",
    ),
}

# Category human labels
CATEGORY_LABELS = {
    "conflict":   "Scheduling Conflict",
    "overload":   "Workload Overload",
    "compliance": "Pedagogical Non-Compliance",
    "capacity":   "Capacity Issue",
    "schedule":   "Schedule Violation",
}


# =============================================================================
#  CLASSIFIER
# =============================================================================

def classify(raw_anomaly: dict) -> dict:
    """
    Enriches a raw anomaly dict with typed classification.

    Args:
        raw_anomaly: dict from detector.detect_all()

    Returns:
        Enriched dict with anomaly_type, severity, category, iso_reference added.

    Example:
        {"anomaly_type": "teacher_overload", "title": "...", ...}
        →
        {"anomaly_type": "other", "severity": "high",
         "category": "overload", "iso_reference": "ISO 21001:2018 §7.1.2", ...}
    """
    raw_type = raw_anomaly.get("anomaly_type", "other")
    typed, severity, category, iso_ref = CLASSIFICATION_MAP.get(
        raw_type,
        (AnomalyType.OTHER, AnomalySeverity.MEDIUM, "schedule", "")
    )

    return {
        **raw_anomaly,
        "anomaly_type":     typed.value,
        "severity":         severity.value,
        "category":         category,
        "category_label":   CATEGORY_LABELS.get(category, category),
        "iso_reference":    raw_anomaly.get("iso_reference") or iso_ref,
    }


def classify_all(raw_anomalies: list[dict]) -> list[dict]:
    """
    Classifies a list of raw anomaly dicts.
    Groups them by severity so HIGH anomalies are first.
    """
    classified = [classify(a) for a in raw_anomalies]

    # Sort: HIGH first, then MEDIUM, then LOW
    severity_order = {"high": 0, "medium": 1, "low": 2}
    classified.sort(key=lambda a: severity_order.get(a.get("severity", "low"), 3))

    # Summary log
    counts = {"high": 0, "medium": 0, "low": 0}
    for a in classified:
        counts[a.get("severity", "low")] += 1
    print(
        f"  [Classifier] {len(classified)} anomaly(ies) classified — "
        f"HIGH={counts['high']} MEDIUM={counts['medium']} LOW={counts['low']}"
    )

    return classified