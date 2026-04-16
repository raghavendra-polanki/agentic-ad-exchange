"""Tests for the Conflict Engine — verifies demo scenario conflict detection."""

from __future__ import annotations

import os

import pytest

from src.conflict.checker import ConflictChecker
from src.conflict.graph import ConflictGraphManager
from src.conflict.models import ConflictStatus, ConflictType


@pytest.fixture(scope="module")
def checker() -> ConflictChecker:
    """Load the seed conflict graph and return a configured checker."""
    graph = ConflictGraphManager()
    seed_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "seed", "conflict_graph.json"
    )
    seed_path = os.path.normpath(seed_path)
    graph.load_from_file(seed_path)
    return ConflictChecker(graph)


# -----------------------------------------------------------------------
# Graph manager unit tests
# -----------------------------------------------------------------------


class TestGraphManager:
    def test_load_schools(self, checker: ConflictChecker) -> None:
        assert "mit" in checker.graph.schools

    def test_load_brands(self, checker: ConflictChecker) -> None:
        assert "nike" in checker.graph.brands
        assert "adidas" in checker.graph.brands

    def test_find_brand_case_insensitive(self, checker: ConflictChecker) -> None:
        assert checker.graph.find_brand_by_name("nike") is not None
        assert checker.graph.find_brand_by_name("Nike") is not None
        assert checker.graph.find_brand_by_name("NIKE") is not None

    def test_find_school_case_insensitive(self, checker: ConflictChecker) -> None:
        assert checker.graph.find_school_by_name("mit") is not None
        assert checker.graph.find_school_by_name("MIT") is not None

    def test_find_athlete_case_insensitive(self, checker: ConflictChecker) -> None:
        assert checker.graph.find_athlete_by_name("Jane Doe") is not None
        assert checker.graph.find_athlete_by_name("jane doe") is not None

    def test_competitors_bidirectional(self, checker: ConflictChecker) -> None:
        assert checker.graph.are_competitors("nike", "adidas")
        assert checker.graph.are_competitors("adidas", "nike")

    def test_non_competitors(self, checker: ConflictChecker) -> None:
        assert not checker.graph.are_competitors("nike", "gatorade")

    def test_unknown_brand_returns_none(self, checker: ConflictChecker) -> None:
        assert checker.graph.find_brand_by_name("unknown_brand") is None


# -----------------------------------------------------------------------
# Pre-screen tests
# -----------------------------------------------------------------------


class TestPreScreen:
    def test_prescreen_nike_mit_cleared(self, checker: ConflictChecker) -> None:
        """Nike is MIT's exclusive apparel sponsor -- should be cleared."""
        result = checker.pre_screen("MIT", "basketball", "Nike")
        assert result.status == ConflictStatus.CLEARED
        assert result.check_type == "pre_screen"
        assert len(result.conflicts) == 0

    def test_prescreen_adidas_mit_blocked(self, checker: ConflictChecker) -> None:
        """Adidas competes with Nike (MIT's sponsor) -- should be blocked."""
        result = checker.pre_screen("MIT", "basketball", "Adidas")
        assert result.status == ConflictStatus.BLOCKED
        assert len(result.conflicts) >= 1

        conflict_types = {c.conflict_type for c in result.conflicts}
        assert ConflictType.SCHOOL_EXCLUSIVE_SPONSOR in conflict_types
        # Should mention Nike and MIT in explanation
        desc = result.conflicts[0].description
        assert "Nike" in desc
        assert "MIT" in desc

    def test_prescreen_gatorade_mit_cleared(self, checker: ConflictChecker) -> None:
        """No school-level conflict for Gatorade -- should be cleared at pre-screen."""
        result = checker.pre_screen("MIT", "basketball", "Gatorade")
        assert result.status == ConflictStatus.CLEARED
        assert len(result.conflicts) == 0

    def test_prescreen_campus_pizza_mit_cleared(self, checker: ConflictChecker) -> None:
        """No conflicts for Campus Pizza -- should be cleared."""
        result = checker.pre_screen("MIT", "basketball", "Campus Pizza")
        assert result.status == ConflictStatus.CLEARED
        assert len(result.conflicts) == 0

    def test_prescreen_unknown_brand_cleared(self, checker: ConflictChecker) -> None:
        """Unknown brands should be cleared (no data to block)."""
        result = checker.pre_screen("MIT", "basketball", "SomeBrand")
        assert result.status == ConflictStatus.CLEARED

    def test_prescreen_unknown_school_cleared(self, checker: ConflictChecker) -> None:
        """Unknown schools should be cleared (no data to block)."""
        result = checker.pre_screen("Stanford", "basketball", "Nike")
        assert result.status == ConflictStatus.CLEARED


# -----------------------------------------------------------------------
# Final check tests
# -----------------------------------------------------------------------


class TestFinalCheck:
    def test_final_check_nike_jane_doe_cleared(self, checker: ConflictChecker) -> None:
        """Nike has no athlete-level conflict with Jane Doe -- should be cleared."""
        result = checker.final_check("MIT", "basketball", "Nike", ["Jane Doe"])
        assert result.status == ConflictStatus.CLEARED
        assert result.check_type == "final_check"
        assert len(result.conflicts) == 0

    def test_final_check_gatorade_jane_doe_blocked(self, checker: ConflictChecker) -> None:
        """Jane Doe has BodyArmor NIL deal, BodyArmor competes with Gatorade -- blocked."""
        result = checker.final_check("MIT", "basketball", "Gatorade", ["Jane Doe"])
        assert result.status == ConflictStatus.BLOCKED
        assert len(result.conflicts) >= 1

        conflict_types = {c.conflict_type for c in result.conflicts}
        assert ConflictType.ATHLETE_NIL_DEAL in conflict_types

        # Verify explanation mentions key entities
        nil_conflict = next(
            c for c in result.conflicts if c.conflict_type == ConflictType.ATHLETE_NIL_DEAL
        )
        assert "Jane Doe" in nil_conflict.description
        assert "BodyArmor" in nil_conflict.description
        assert "Gatorade" in nil_conflict.description

    def test_final_check_campus_pizza_jane_doe_cleared(self, checker: ConflictChecker) -> None:
        """Campus Pizza has no conflicts at any level."""
        result = checker.final_check("MIT", "basketball", "Campus Pizza", ["Jane Doe"])
        assert result.status == ConflictStatus.CLEARED
        assert len(result.conflicts) == 0

    def test_final_check_adidas_jane_doe_blocked(self, checker: ConflictChecker) -> None:
        """Adidas still blocked at final check (school-level conflict persists)."""
        result = checker.final_check("MIT", "basketball", "Adidas", ["Jane Doe"])
        assert result.status == ConflictStatus.BLOCKED
        conflict_types = {c.conflict_type for c in result.conflicts}
        assert ConflictType.SCHOOL_EXCLUSIVE_SPONSOR in conflict_types

    def test_final_check_no_athletes(self, checker: ConflictChecker) -> None:
        """Final check with empty athlete list behaves like pre-screen."""
        result = checker.final_check("MIT", "basketball", "Gatorade", [])
        assert result.status == ConflictStatus.CLEARED
        assert result.check_type == "final_check"

    def test_final_check_unknown_athlete(self, checker: ConflictChecker) -> None:
        """Unknown athletes should not cause conflicts."""
        result = checker.final_check("MIT", "basketball", "Gatorade", ["Unknown Person"])
        assert result.status == ConflictStatus.CLEARED
