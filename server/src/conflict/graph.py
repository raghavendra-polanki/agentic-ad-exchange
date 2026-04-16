"""Conflict graph manager — loads and queries the in-memory conflict graph."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.conflict.models import (
    Athlete,
    Brand,
    CompetesWithEdge,
    Conference,
    ConflictGraph,
    NilDealEdge,
    School,
    SponsorshipEdge,
)


class ConflictGraphManager:
    """In-memory conflict graph for Phase 1. Loaded from seed JSON."""

    def __init__(self) -> None:
        self.schools: dict[str, School] = {}
        self.athletes: dict[str, Athlete] = {}
        self.brands: dict[str, Brand] = {}
        self.conferences: dict[str, Conference] = {}
        self.sponsorships: list[SponsorshipEdge] = []
        self.nil_deals: list[NilDealEdge] = []
        self.competitors: list[CompetesWithEdge] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_from_file(self, path: str) -> None:
        """Load conflict graph from JSON seed file."""
        raw = json.loads(Path(path).read_text())
        graph = ConflictGraph.model_validate(raw)

        self.schools = {s.school_id: s for s in graph.schools}
        self.athletes = {a.athlete_id: a for a in graph.athletes}
        self.brands = {b.brand_id: b for b in graph.brands}
        self.conferences = {c.conference_id: c for c in graph.conferences}
        self.sponsorships = graph.sponsorships
        self.nil_deals = graph.nil_deals
        self.competitors = graph.competitors

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_school_sponsors(self, school_id: str) -> list[SponsorshipEdge]:
        """Get all currently-active exclusive sponsors for a school."""
        today = date.today()
        return [
            s
            for s in self.sponsorships
            if s.school_id == school_id and s.start_date <= today <= s.end_date
        ]

    def get_athlete_nil_deals(self, athlete_id: str) -> list[NilDealEdge]:
        """Get all currently-active NIL deals for an athlete."""
        today = date.today()
        return [
            n
            for n in self.nil_deals
            if n.athlete_id == athlete_id and n.start_date <= today <= n.end_date
        ]

    def are_competitors(self, brand_a: str, brand_b: str) -> bool:
        """Check if two brands compete (bidirectional). Accepts brand IDs."""
        for c in self.competitors:
            if (c.brand_a_id == brand_a and c.brand_b_id == brand_b) or (
                c.brand_a_id == brand_b and c.brand_b_id == brand_a
            ):
                return True
        return False

    def find_brand_by_name(self, name: str) -> Brand | None:
        """Case-insensitive brand lookup by name."""
        lower = name.lower()
        for brand in self.brands.values():
            if brand.name.lower() == lower:
                return brand
        return None

    def find_school_by_name(self, name: str) -> School | None:
        """Case-insensitive school lookup by name."""
        lower = name.lower()
        for school in self.schools.values():
            if school.name.lower() == lower:
                return school
        return None

    def find_athlete_by_name(self, name: str) -> Athlete | None:
        """Case-insensitive athlete lookup by name."""
        lower = name.lower()
        for athlete in self.athletes.values():
            if athlete.name.lower() == lower:
                return athlete
        return None
