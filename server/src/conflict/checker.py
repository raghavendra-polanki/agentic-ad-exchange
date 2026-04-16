"""Two-pass conflict checker: pre-screen (fast) and final check (thorough)."""

from __future__ import annotations

from src.conflict.graph import ConflictGraphManager
from src.conflict.models import (
    ConflictCheckResult,
    ConflictExplanation,
    ConflictStatus,
    ConflictType,
)


class ConflictChecker:
    """Two-pass conflict checking: pre-screen (fast) and final check (thorough)."""

    def __init__(self, graph: ConflictGraphManager) -> None:
        self.graph = graph

    # ------------------------------------------------------------------
    # Pre-screen (matching time — no specific athletes yet)
    # ------------------------------------------------------------------

    def pre_screen(
        self, school_name: str, sport: str, brand_name: str
    ) -> ConflictCheckResult:
        """
        Fast pre-screen at matching time.

        Checks:
          1. Does school have an exclusive sponsor in the brand's category?
             - If so, is the requesting brand *different* from that sponsor?
          2. Does the brand compete with any of the school's exclusive sponsors?

        Returns CLEARED or BLOCKED with explanations.
        """
        conflicts: list[ConflictExplanation] = []

        brand = self.graph.find_brand_by_name(brand_name)
        school = self.graph.find_school_by_name(school_name)

        if brand is None or school is None:
            # Unknown brand/school — no conflicts can be determined, clear it
            return ConflictCheckResult(
                status=ConflictStatus.CLEARED,
                brand=brand_name,
                conflicts=[],
                check_type="pre_screen",
            )

        sponsorships = self.graph.get_school_sponsors(school.school_id)

        for sponsorship in sponsorships:
            sponsor_brand = self.graph.brands.get(sponsorship.brand_id)
            if sponsor_brand is None:
                continue

            # Check 1: School has exclusive sponsor in same category, and it's not *this* brand
            if sponsorship.category == brand.category and sponsorship.brand_id != brand.brand_id:
                conflicts.append(
                    ConflictExplanation(
                        conflict_type=ConflictType.SCHOOL_EXCLUSIVE_SPONSOR,
                        description=(
                            f"{school.name} has exclusive {sponsorship.category} deal with "
                            f"{sponsor_brand.name} ({sponsorship.start_date.year}-"
                            f"{sponsorship.end_date.year}). "
                            f"{brand.name} cannot run {sponsorship.category} campaigns here."
                        ),
                        entities_involved=[school.name, sponsor_brand.name, brand.name],
                        chain=(
                            f"{brand.name} ─blocked_by─► {sponsor_brand.name} "
                            f"◄─exclusive_{sponsorship.category}─ {school.name}"
                        ),
                    )
                )

            # Check 2: Brand competes with this school's sponsor
            if self.graph.are_competitors(brand.brand_id, sponsorship.brand_id):
                # Avoid duplicate if already caught by category check above
                already_reported = any(
                    c.conflict_type == ConflictType.SCHOOL_EXCLUSIVE_SPONSOR
                    and sponsor_brand.name in c.entities_involved
                    for c in conflicts
                )
                if not already_reported:
                    conflicts.append(
                        ConflictExplanation(
                            conflict_type=ConflictType.BRAND_COMPETITOR,
                            description=(
                                f"{brand.name} and {sponsor_brand.name} are registered "
                                f"competitors in the {sponsorship.category} category. "
                                f"{sponsor_brand.name} is {school.name}'s exclusive "
                                f"{sponsorship.category} sponsor."
                            ),
                            entities_involved=[brand.name, sponsor_brand.name, school.name],
                            chain=(
                                f"{brand.name} ─competes_with─► {sponsor_brand.name} "
                                f"◄─exclusive_{sponsorship.category}─ {school.name}"
                            ),
                        )
                    )

        status = ConflictStatus.BLOCKED if conflicts else ConflictStatus.CLEARED
        return ConflictCheckResult(
            status=status,
            brand=brand_name,
            conflicts=conflicts,
            check_type="pre_screen",
        )

    # ------------------------------------------------------------------
    # Final check (post-proposal — specific athletes known)
    # ------------------------------------------------------------------

    def final_check(
        self,
        school_name: str,
        sport: str,
        brand_name: str,
        athlete_names: list[str],
    ) -> ConflictCheckResult:
        """
        Thorough check after proposal, with specific athletes.

        Runs all pre-screen checks PLUS:
          1. Does any featured athlete have a NIL deal with a competing brand?
          2. Time-window validation on NIL deals (only active deals block).

        Returns CLEARED or BLOCKED with detailed explanations.
        """
        # Start with pre-screen checks
        result = self.pre_screen(school_name, sport, brand_name)
        conflicts = list(result.conflicts)

        brand = self.graph.find_brand_by_name(brand_name)
        if brand is None:
            return ConflictCheckResult(
                status=ConflictStatus.CLEARED,
                brand=brand_name,
                conflicts=[],
                check_type="final_check",
            )

        # Athlete-level checks
        for athlete_name in athlete_names:
            athlete = self.graph.find_athlete_by_name(athlete_name)
            if athlete is None:
                continue

            nil_deals = self.graph.get_athlete_nil_deals(athlete.athlete_id)
            for deal in nil_deals:
                deal_brand = self.graph.brands.get(deal.brand_id)
                if deal_brand is None:
                    continue

                # Check: athlete has NIL deal with a brand that competes with requesting brand
                if self.graph.are_competitors(brand.brand_id, deal.brand_id):
                    conflicts.append(
                        ConflictExplanation(
                            conflict_type=ConflictType.ATHLETE_NIL_DEAL,
                            description=(
                                f"{athlete.name} has an active {deal.deal_type} deal with "
                                f"{deal_brand.name} ({deal.start_date.year}-"
                                f"{deal.end_date.year}). "
                                f"{deal_brand.name} and {brand.name} are registered competitors "
                                f"in the {deal_brand.category} category."
                            ),
                            entities_involved=[
                                athlete.name,
                                deal_brand.name,
                                brand.name,
                            ],
                            chain=(
                                f"{brand.name} ─competes_with─► {deal_brand.name} "
                                f"◄─nil_{deal.deal_type}─ {athlete.name}"
                            ),
                        )
                    )

        status = ConflictStatus.BLOCKED if conflicts else ConflictStatus.CLEARED
        return ConflictCheckResult(
            status=status,
            brand=brand_name,
            conflicts=conflicts,
            check_type="final_check",
        )
