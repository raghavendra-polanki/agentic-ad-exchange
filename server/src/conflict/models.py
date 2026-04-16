"""Re-export canonical schema models for backward compatibility within conflict module."""

from src.schemas.conflicts import (
    Athlete,
    Brand,
    CompetesWithEdge,
    Conference,
    ConflictCheckResult,
    ConflictExplanation,
    ConflictGraph,
    ConflictStatus,
    ConflictType,
    NilDealEdge,
    School,
    SponsorshipEdge,
)

__all__ = [
    "Athlete",
    "Brand",
    "CompetesWithEdge",
    "Conference",
    "ConflictCheckResult",
    "ConflictExplanation",
    "ConflictGraph",
    "ConflictStatus",
    "ConflictType",
    "NilDealEdge",
    "School",
    "SponsorshipEdge",
]
