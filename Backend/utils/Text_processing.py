"""
agents/constraint_agent/utils/text_processing.py
==================================================
Simple NLP helpers for preprocessing constraint text
before sending to the LLM.
"""

import re


# =============================================================================
#  DAY DICTIONARIES
# =============================================================================

DAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAYS_FR = ["lundi",  "mardi",  "mercredi",  "jeudi",   "vendredi", "samedi",   "dimanche"]
FR_TO_EN = dict(zip(DAYS_FR, DAYS_EN))


# =============================================================================
#  NEGATION WORDS
# =============================================================================

NEGATION_WORDS = {
    "no", "not", "never", "avoid", "without", "except",
    "pas", "ne", "jamais", "éviter", "sans", "sauf", "interdit", "interdite"
}

FRENCH_KEYWORDS = {
    "le", "la", "les", "du", "de", "des", "pas", "ne",
    "séance", "séances", "cours", "formateur", "formatrice",
    "disponible", "interdit", "pause", "déjeuner", "matin",
    "après-midi", "seulement", "salle", "capacité", "groupe",
    "lundi", "mardi", "mercredi", "jeudi", "vendredi"
}


# =============================================================================
#  1. NORMALIZE
# =============================================================================

def normalize_text(text: str) -> str:
    """Cleans raw user input: strip, collapse spaces, remove non-printable chars."""
    if not text:
        return ""
    text = re.sub(r"[^\x20-\x7EàâçéèêëîïôùûüÿœæÀÂÇÉÈÊËÎÏÔÙÛÜŸŒÆ\n\r\t.,;:!?()\-]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


# =============================================================================
#  2. DETECT LANGUAGE
# =============================================================================

def detect_language(text: str) -> str:
    """Returns 'fr' if text is likely French, 'en' otherwise."""
    words      = set(re.findall(r"\b\w+\b", text.lower()))
    french_hits = len(words & FRENCH_KEYWORDS)
    return "fr" if french_hits >= 2 else "en"


# =============================================================================
#  3. SPLIT INTO SENTENCES
# =============================================================================

def split_sentences(text: str) -> list[str]:
    """Splits constraint text into individual constraint lines."""
    if not text:
        return []
    parts  = re.split(r"[.;!\n]|(?:^|\s)[-–•]\s", text)
    result = []
    for part in parts:
        part = part.strip(" \t\r.,;:-")
        if len(part) > 3:
            result.append(part)
    return result


# =============================================================================
#  4. EXTRACT DAY MENTIONS
# =============================================================================

def extract_day_mentions(text: str) -> list[str]:
    """
    Finds all day names (EN or FR) and returns canonical English capitalized names.
    e.g. "lundi et mercredi" → ["Monday", "Wednesday"]
    """
    text_lower = text.lower()
    found      = []

    for fr, en in FR_TO_EN.items():
        if re.search(r"\b" + fr + r"\b", text_lower):
            canon = en.capitalize()
            if canon not in found:
                found.append(canon)

    for en in DAYS_EN:
        if re.search(r"\b" + en + r"\b", text_lower):
            canon = en.capitalize()
            if canon not in found:
                found.append(canon)

    return found


# =============================================================================
#  5. EXTRACT NUMBERS WITH CONTEXT
# =============================================================================

def extract_numbers(text: str) -> list[dict]:
    """
    Extracts numeric values with context.
    Converts Xh30 → minutes (e.g. 1h30 → 90).
    Returns [{"value": int, "unit": str, "context": str}]
    """
    results = []

    # "Xh30" or "XhYY"
    for m in re.finditer(r"(\d+)\s*h\s*(\d{0,2})", text, re.IGNORECASE):
        h       = int(m.group(1))
        minutes = int(m.group(2)) if m.group(2) else 0
        total   = h * 60 + minutes
        context = text[max(0, m.start()-10):m.end()+10].strip()
        results.append({"value": total, "unit": "minutes", "context": context})

    # Plain numbers with units
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*(minutes?|mins?|heures?|hours?|h\b|séances?|sessions?|jours?|days?)",
        text, re.IGNORECASE
    ):
        raw_val = float(m.group(1))
        unit    = m.group(2).lower()
        context = text[max(0, m.start()-10):m.end()+10].strip()

        if any(u in unit for u in ["heure", "hour"]):
            results.append({"value": int(raw_val * 60), "unit": "minutes", "context": context})
        elif any(u in unit for u in ["minute", "min"]):
            results.append({"value": int(raw_val), "unit": "minutes", "context": context})
        else:
            results.append({"value": int(raw_val), "unit": unit, "context": context})

    return results


# =============================================================================
#  6. EXTRACT TIME MENTIONS
# =============================================================================

def extract_time_mentions(text: str) -> list[str]:
    """
    Extracts time expressions → HH:MM format.
    Handles: "08:00", "8h30", "8h", "9am", "14h00", "2pm"
    """
    results = []

    for m in re.finditer(r"\b(\d{1,2}):(\d{2})\b", text):
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mn <= 59:
            t = f"{h:02d}:{mn:02d}"
            if t not in results:
                results.append(t)

    for m in re.finditer(r"\b(\d{1,2})h(\d{0,2})\b", text, re.IGNORECASE):
        h  = int(m.group(1))
        mn = int(m.group(2)) if m.group(2) else 0
        if 0 <= h <= 23 and 0 <= mn <= 59:
            t = f"{h:02d}:{mn:02d}"
            if t not in results:
                results.append(t)

    for m in re.finditer(r"\b(\d{1,2})\s*(am|pm)\b", text, re.IGNORECASE):
        h      = int(m.group(1))
        period = m.group(2).lower()
        if period == "pm" and h != 12:
            h += 12
        elif period == "am" and h == 12:
            h = 0
        if 0 <= h <= 23:
            t = f"{h:02d}:00"
            if t not in results:
                results.append(t)

    return results


# =============================================================================
#  7. DETECT NEGATION
# =============================================================================

def has_negation(text: str) -> bool:
    """Returns True if the text contains a negation word."""
    words = set(re.findall(r"\b\w+\b", text.lower()))
    return bool(words & NEGATION_WORDS)


# =============================================================================
#  8. SUMMARIZE FOR LOG
# =============================================================================

def summarize_for_log(text: str, max_len: int = 80) -> str:
    """Short preview of text for console logging."""
    text = normalize_text(text)
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# =============================================================================
#  9. FULL PREPROCESSING PIPELINE  (main entry point)
# =============================================================================

def preprocess_constraint_text(raw_text: str) -> dict:
    """
    Runs the full preprocessing pipeline on raw user text.

    Returns:
        {
          "normalized":   str,
          "language":     "en" | "fr",
          "sentences":    list[str],
          "day_mentions": list[str],       e.g. ["Monday", "Wednesday"]
          "time_mentions":list[str],       e.g. ["08:00", "17:00"]
          "numbers":      list[dict],      e.g. [{"value": 90, "unit": "minutes", ...}]
          "has_negation": bool,
          "preview":      str,
        }

    This dict is passed to the LLM as additional context
    to improve extraction accuracy.
    """
    normalized = normalize_text(raw_text)
    return {
        "normalized":    normalized,
        "language":      detect_language(normalized),
        "sentences":     split_sentences(normalized),
        "day_mentions":  extract_day_mentions(normalized),
        "time_mentions": extract_time_mentions(normalized),
        "numbers":       extract_numbers(normalized),
        "has_negation":  has_negation(normalized),
        "preview":       summarize_for_log(normalized),
    }