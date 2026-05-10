from dataclasses import dataclass
from sqlalchemy.orm import Session

from Services.constraintAgent.Schema import (
    ConstraintInput, ConstraintOutput, ValidationResult
)
from Services.constraintAgent.Analyzer          import Analyzer
from Services.constraintAgent.Validator          import Validator
from Services.constraintAgent.constraint_merger  import ConstraintMerger
from Services.constraintAgent.Loaders.Iso_loader         import ISOLoader
from Services.constraintAgent.Loaders.PedagogicalLoader import PedagogicalLoader
from utils.Text_processing      import (
    preprocess_constraint_text, summarize_for_log
)


# =============================================================================
#  RESULT TYPE
# =============================================================================

@dataclass
class ConstraintAgentResult:

    success:       bool
    output:        ConstraintOutput    # merged constraints
    validation:    ValidationResult    # status + issues + warnings
    planning_dict: dict                # ready for PlanningAgent.run()
    preprocessing: dict                # text analysis metadata
    error:         str = ""


# =============================================================================
#  CONSTRAINT AGENT
# =============================================================================

class ConstraintAgent:


    def __init__(self, db: Session):
        self.db        = db
        self.analyzer  = Analyzer()
        self.validator = Validator()    # handles iso_rules + business_rules internally
        self.merger    = ConstraintMerger()

    # ── MAIN ENTRY POINT ───────────────────────────────────────────────────────

    def run(
        self,
        pedagogical_text: str = "",
        user_text:        str = "",
    ) -> ConstraintAgentResult:

        print("\n" + "=" * 60)
        print("  CONSTRAINT AGENT")
        print("=" * 60)

        # ── Step 1: Preprocess text inputs ────────────────────────────────────
        print("\n[1/6] Preprocessing text inputs...")
        ped_meta  = preprocess_constraint_text(pedagogical_text) if pedagogical_text.strip() else {}
        user_meta = preprocess_constraint_text(user_text)        if user_text.strip()        else {}

        if ped_meta:
            print(f"  Pedagogical: '{ped_meta['preview']}' | lang={ped_meta['language']} "
                  f"| days={ped_meta['day_mentions']} | times={ped_meta['time_mentions']}")
        if user_meta:
            print(f"  User:        '{user_meta['preview']}' | lang={user_meta['language']} "
                  f"| days={user_meta['day_mentions']} | times={user_meta['time_mentions']}")

        # ── Step 2: Load ISO constraints from DB ──────────────────────────────
        print("\n[2/6] Loading ISO constraints from DB...")
        iso_list = ISOLoader(self.db).load()

        # ── Step 3: Load pedagogical rules from DB ────────────────────────────
        print("\n[3/6] Loading pedagogical rules from DB...")
        db_ped, _ = PedagogicalLoader(self.db).load(user_text=pedagogical_text)

        # ── Step 4: Analyze via LLM ───────────────────────────────────────────
        print("\n[4/6] Analyzing constraints via LLM...")
        constraint_input = ConstraintInput(
            iso_constraints  = iso_list,
            pedagogical_text = pedagogical_text,
            user_text        = user_text,
        )
        analyzer_output = self.analyzer.analyze(constraint_input)

        # ── Step 5: Merge all sources ─────────────────────────────────────────
        print("\n[5/6] Merging all constraint sources...")
        merged_output = self.merger.merge(
            iso_constraints = iso_list,
            db_pedagogical  = db_ped,
            analyzer_output = analyzer_output,
        )

        # ── Step 6: Validate ──────────────────────────────────────────────────
        print("\n[6/6] Validating merged constraints...")
        validation = self.validator.validate(merged_output)

        # ── Build planning dict ───────────────────────────────────────────────
        planning_dict = ConstraintMerger.to_planning_dict(merged_output)

        print(f"\n  [ConstraintAgent] Done.")
        print(f"  Valid  : {validation.is_valid}")
        print(f"  Issues : {len(validation.issues)}")
        print(f"  Warnings: {len(validation.warnings)}")

        return ConstraintAgentResult(
            success       = validation.is_valid,
            output        = merged_output,
            validation    = validation,
            planning_dict = planning_dict,
            preprocessing = {
                "pedagogical": ped_meta,
                "user":        user_meta,
            },
        )

    # ── TERMINAL MODE ──────────────────────────────────────────────────────────

    def run_interactive(self) -> ConstraintAgentResult:
        """Interactive terminal mode — prompts the user for input."""
        print("\n" + "=" * 60)
        print("  CONSTRAINT AGENT — Interactive Mode")
        print("=" * 60)

        print("\n  [A] Pedagogical constraints")
        print("  Describe pedagogical rules (Enter to skip):")
        ped_text = input("  → ").strip()

        print("\n  [B] Scheduling constraints")
        print("  Describe your planning preferences (Enter to skip):")
        user_text = input("  → ").strip()

        result = self.run(pedagogical_text=ped_text, user_text=user_text)

        print(f"\n  Validation: {'✅ VALID' if result.success else '❌ ISSUES FOUND'}")
        for issue in result.validation.issues:
            icon = "❌" if not result.validation.is_valid else "⚠️ "
            print(f"  {icon} [{issue.field}] {issue.message}")
        for w in result.validation.warnings:
            print(f"  💡 {w}")

        return result