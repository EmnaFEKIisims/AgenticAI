import json
from Services.LlmService import _ask_ollama


# =============================================================================
#  SYSTEM PROMPT
# =============================================================================

EXTRACTION_PROMPT = """
You are a data extractor for a training planning system.
Your job is to classify raw records from a file into the correct database entity.

Database entities and their fields:
  - "course"     : title, total_hours, session_duration, pedagogical_objectives, required_equipments (list of strings)
  - "trainer"    : name, email, specialization, availability_notes
  - "room"       : name, capacity (integer), room_type
  - "group"      : name, size (integer), level
  - "equipment"  : name, description, total_quantity (integer)
  - "constraint" : constraint_type (snake_case), constraint_data (JSON object)
  - "unknown"    : use this if the record cannot be classified

You receive a list of raw records. Each record is a dict with arbitrary keys
(may be in English, French, or mixed). Some records may have a "_sheet" key
(Excel sheet name) or "_page" key (PDF page) as hints.

Rules:
  - "title" / "cours" / "formation" / "course"  in keys -> "course"
  - "name"  + ("email" / "mail")                        -> "trainer"
  - "specialization" / "spécialisation" / "formateur"   -> "trainer"
  - "capacity" / "capacité" / "salle" / "room"          -> "room"
  - "size" / "taille" / "groupe" / "group" / "learner"  -> "group"
  - "quantity" / "quantité" / "equipment" / "équipement"-> "equipment"
  - Describes a rule, restriction, availability, forbidden day -> "constraint"
    (set constraint_type to snake_case e.g. "forbidden_days", "trainer_availability")
  - Map field names to DB schema (e.g. "heures" -> "total_hours", "salle" -> "name")

Return ONLY a valid JSON array. No markdown, no explanation.
Format:
[
  {
    "entity_type": "<type>",
    "standardized": { "<db_field>": "<value>" },
    "original": { <original record> }
  }
]
"""


# =============================================================================
#  Main extraction function
# =============================================================================

def extract_entities(raw_records: list[dict]) -> list[dict]:
    """
    Sends raw records to the LLM for classification and field mapping.

    Args:
        raw_records: list of raw dicts from any parser

    Returns:
        List of classified dicts with entity_type + standardized fields.
    """
    if not raw_records:
        return []

    # Send records in batches of 20 to avoid token limits
    BATCH_SIZE = 20
    results    = []

    for i in range(0, len(raw_records), BATCH_SIZE):
        batch = raw_records[i : i + BATCH_SIZE]
        print(f"  [LLM Extractor] Processing batch {i//BATCH_SIZE + 1} "
              f"({len(batch)} record(s))...")

        prompt = (
            "Classify and standardize these records:\n"
            + json.dumps(batch, ensure_ascii=False, indent=2)
        )

        try:
            raw  = _ask_ollama(prompt=prompt, system=EXTRACTION_PROMPT)
            classified = _parse_llm_response(raw)
            results.extend(classified)
            print(f"  [LLM Extractor] Batch classified: {len(classified)} record(s).")
        except Exception as e:
            print(f"  [LLM Extractor] Batch failed: {e}. Marking as unknown.")
            for record in batch:
                results.append({
                    "entity_type":  "unknown",
                    "standardized": {},
                    "original":     record,
                })

    return results


def _parse_llm_response(raw: str) -> list[dict]:
    """Extracts the JSON array from the LLM response."""
    cleaned = (
        raw.strip()
           .removeprefix("```json").removeprefix("```")
           .removesuffix("```").strip()
    )
    start = cleaned.find("[")
    end   = cleaned.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array found in LLM response: {raw[:300]}")
    return json.loads(cleaned[start:end])