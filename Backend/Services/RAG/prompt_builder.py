"""
Services/RAG/prompt_builder.py
================================
Formats retrieved memories and knowledge into a context string
injected into LLM prompts.

Output format:
  ╔══════════════════════════════════════════════════╗
  ║  ADAPTIVE CONTEXT — PAST EXPERIENCE & PREFERENCES ║
  ╠══════════════════════════════════════════════════╣
  ║ [FEEDBACK] Administrator rejected previous planning: too heavy on Monday
  ║ [PREFERENCE] Administrator prefers morning sessions (08:00-11:00)
  ║ [DECISION] Friday sessions avoided: ISO 21001 + trainer conflict
  ╠══════════════════════════════════════════════════╣
  ║ [KNOWLEDGE] Theory must precede practice (ISO 21001:2018)
  ╚══════════════════════════════════════════════════╝

The LLM receives this BEFORE the user request, biasing it
toward decisions that match past preferences.
"""

from rag.memory_types import MemoryDocument, MemoryType


# Icons per memory type for LLM readability
TYPE_ICONS = {
    MemoryType.USER_FEEDBACK:         "💬 FEEDBACK",
    MemoryType.USER_PREFERENCE:       "⚙️  PREFERENCE",
    MemoryType.DECISION_HISTORY:      "📋 DECISION",
    MemoryType.PLANNING_HISTORY:      "📅 PLANNING",
    MemoryType.CONFLICT_CORRECTION:   "⚠️  CONFLICT",
    MemoryType.PEDAGOGICAL_KNOWLEDGE: "🎓 KNOWLEDGE",
}


def build_planning_context(
    memories:  list[MemoryDocument],
    knowledge: list[dict] = None,
) -> str:
    """
    Builds the full context string for PlanningAgent.

    Args:
        memories:  retrieved user memories (preferences, decisions, feedback)
        knowledge: retrieved pedagogical rules (from knowledge documents)

    Returns:
        Context string to inject into the LLM system prompt.
        Empty string if no relevant context exists.
    """
    if not memories and not knowledge:
        return ""

    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║  ADAPTIVE CONTEXT — PAST EXPERIENCE & PREFERENCES ║",
        "╚══════════════════════════════════════════════════╝",
        "",
    ]

    # User memories (preferences, decisions, feedback)
    if memories:
        lines.append("📌 RELEVANT PAST EXPERIENCE:")
        # Sort: feedback first (importance 3), then preferences, then decisions
        sorted_mems = sorted(memories, key=lambda m: m.importance, reverse=True)
        for mem in sorted_mems:
            icon = TYPE_ICONS.get(mem.memory_type, "📎")
            lines.append(f"  [{icon}] {mem.content}")
        lines.append("")

    # Pedagogical knowledge
    if knowledge:
        lines.append("📚 RELEVANT PEDAGOGICAL RULES:")
        for doc in knowledge:
            src = f" ({doc.get('source', '')})" if doc.get("source") else ""
            lines.append(f"  [🎓 RULE{src}] {doc['content']}")
        lines.append("")

    lines.append("Use this context to produce a better, more personalized planning.")
    lines.append("If context conflicts with hard constraints (ISO), hard constraints take priority.")

    return "\n".join(lines)


def build_constraint_context(memories: list[MemoryDocument]) -> str:
    """Builds context for ConstraintAgent."""
    if not memories:
        return ""

    lines = [
        "PAST CONSTRAINT DECISIONS:",
        *[f"  • {m.content}" for m in memories],
        "",
        "Apply these when analyzing current constraints.",
    ]
    return "\n".join(lines)


def build_pedagogical_context(
    memories:  list[MemoryDocument],
    knowledge: list[dict] = None,
) -> str:
    """Builds context for PedagogicalAgent."""
    if not memories and not knowledge:
        return ""

    lines = ["PEDAGOGICAL CONTEXT:"]

    if knowledge:
        for doc in knowledge:
            lines.append(f"  • [RULE] {doc['content']}")

    if memories:
        for mem in memories:
            lines.append(f"  • {mem.content}")

    lines.append("")
    return "\n".join(lines)


def build_anomaly_context(memories: list[MemoryDocument]) -> str:
    """Builds context for AnomalyAgent."""
    if not memories:
        return ""

    lines = [
        "PAST CONFLICTS AND RESOLUTIONS:",
        *[f"  • {m.content}" for m in memories],
        "",
        "Watch for similar patterns in the current planning.",
    ]
    return "\n".join(lines)


def is_context_useful(context: str) -> bool:
    """Returns True if context has meaningful content (not just headers)."""
    return bool(context and len(context.strip()) > 50)