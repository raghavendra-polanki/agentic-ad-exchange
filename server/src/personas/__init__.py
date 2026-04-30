"""Persona loading + parsing — frontmatter + body markdown files.

On startup the server scans personas/*.md and seeds BrandRules / ContentRules
into the in-memory store. Edits made via the dashboard then write to
state.json (see src.persistence) and override the on-disk file values.
"""

from .loader import load_personas, parse_persona_file

__all__ = ["load_personas", "parse_persona_file"]
