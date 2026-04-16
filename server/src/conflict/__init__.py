"""Conflict Engine — neutral arbiter for contractual conflict detection."""

from src.conflict.checker import ConflictChecker
from src.conflict.graph import ConflictGraphManager

# Singleton — loaded once at startup
conflict_graph = ConflictGraphManager()
conflict_checker = ConflictChecker(conflict_graph)


def init_conflict_engine() -> None:
    """Load seed data. Called at server startup."""
    import os

    seed_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "seed", "conflict_graph.json"
    )
    seed_path = os.path.normpath(seed_path)
    conflict_graph.load_from_file(seed_path)


__all__ = [
    "ConflictChecker",
    "ConflictGraphManager",
    "conflict_checker",
    "conflict_graph",
    "init_conflict_engine",
]
