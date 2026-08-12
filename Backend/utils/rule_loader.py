"""
utils/rule_loader.py
=====================
Loads pedagogical_rules.json and provides a clean interface to access rules.

Functions:
  load_rules()        -> loads (or returns cached) full rules dict
  get_rule(name)      -> returns one rule section by name
  reload_rules()      -> forces a fresh read from disk

Why a separate file?
  - Validators never import the JSON directly
  - If the file path changes → only this file needs updating
  - reload_rules() lets you hot-reload without restarting the server
"""

import json
import os
from typing import Any

# =============================================================================
#  Path to pedagogical_rules.json
#  Resolves relative to THIS file → works regardless of cwd
# =============================================================================

_RULES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "Services",
    "PedagogicalAgent",
    "rules",
    "pedagogical_rules.json",
)

# =============================================================================
#  Internal cache
# =============================================================================

_cache: dict | None = None


# =============================================================================
#  PUBLIC FUNCTIONS
# =============================================================================

def load_rules() -> dict:
    """
    Returns the full pedagogical rules dict.
    Reads from disk only once, then caches in memory.

    Returns:
        Full dict from pedagogical_rules.json, e.g.:
        {
          "workload":          {"max_daily_hours": 6, ...},
          "breaks":            {"mandatory_break_after_minutes": 180, ...},
          "progression":       {...},
          "practice_balance":  {...},
          "teacher_workload":  {...},
          "room":              {...},
          "difficulty_spread": {...},
        }
    """
    global _cache
    if _cache is None:
        _cache = _read_from_disk()
    return _cache


def get_rule(name: str) -> dict:
    """
    Returns a single rule section by name.

    Args:
        name: section key in pedagogical_rules.json
              e.g. "workload", "breaks", "progression", "practice_balance"

    Returns:
        The section dict, or {} if not found.

    Example:
        get_rule("workload")
        → {"max_daily_hours": 6, "max_consecutive_hours": 3, "weight": 25, ...}
    """
    rules = load_rules()
    section = rules.get(name, {})
    if not section:
        print(f"  [RuleLoader] ⚠️  Section '{name}' not found in rules file.")
    return section


def get_value(section: str, key: str, default: Any = None) -> Any:
    """
    Returns a single value from a rule section.

    Args:
        section: rule section name, e.g. "workload"
        key:     rule key within the section, e.g. "max_daily_hours"
        default: value returned if key is not found

    Example:
        get_value("workload", "max_daily_hours", default=6)
        → 6.0
    """
    return get_rule(section).get(key, default)


def reload_rules() -> dict:
    """
    Forces a fresh read of pedagogical_rules.json from disk.
    Use this if the file was modified at runtime without restarting the server.

    Returns:
        The newly loaded rules dict.
    """
    global _cache
    _cache = _read_from_disk()
    print(f"  [RuleLoader] Rules reloaded from: {_RULES_PATH}")
    return _cache


def all_weights() -> dict[str, int]:
    """
    Returns the weight of each rule section.
    Used by the scoring service to compute the final audit score.

    Returns:
        {"workload": 25, "breaks": 20, "progression": 20, ...}
    """
    rules = load_rules()
    return {
        section: data.get("weight", 0)
        for section, data in rules.items()
        if isinstance(data, dict) and not section.startswith("_")
    }


# =============================================================================
#  INTERNAL
# =============================================================================

def _read_from_disk() -> dict:
    """Reads and parses the JSON file. Raises FileNotFoundError if missing."""
    path = os.path.normpath(_RULES_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[RuleLoader] pedagogical_rules.json not found at: {path}\n"
            f"Expected location: rules/pedagogical_rules.json"
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Remove metadata key from rule access
    data.pop("_meta", None)
    print(f"  [RuleLoader] Rules loaded from: {path} "
          f"({len([k for k in data if not k.startswith('_')])} section(s))")
    return data