"""Shared constants for the PDF parser — anchors, patterns, noise words."""

from __future__ import annotations

import re

PARSER_VERSION = "1.0.0"

# ── Header anchors ──────────────────────────────────────────────────────

PERIODO_RE = re.compile(r"Evaluaci[oó]n\s+docente:\s*(.+)", re.IGNORECASE)
RECINTO_RE = re.compile(r"Recinto:\s*(.+)", re.IGNORECASE)
PROFESOR_RE = re.compile(
    r"Profesor:\s*(.+?)\s*(?:\((\w+)\))?\s*$", re.IGNORECASE | re.MULTILINE
)

# ── Metrics table identification ────────────────────────────────────────

DIMENSION_HEADER_MARKERS = {"Dimensiones", "METODOLOGÍA", "Dominio", "CUMPLIMIENTO"}
KNOWN_DIMENSIONS = {"METODOLOGÍA", "Dominio", "CUMPLIMIENTO", "ESTRATEGIA", "GENERAL"}

# ── Courses table identification ────────────────────────────────────────

COURSES_HEADER_MARKER = "Código"  # first cell when header row contains "Código asignatura"
TOTAL_ESTUDIANTES_RE = re.compile(r"(\d+)\s*/\s*(\d+)")

# ── Comments section anchor ─────────────────────────────────────────────

COMMENT_SECTION_RE = re.compile(
    r"Evaluaci[oó]n\s+(Estudiante|Director)\s+Profesor\s+--\s+(.+)",
    re.IGNORECASE,
)
COMMENT_HEADER_MARKERS = {"Fortalezas", "Mejoras", "Observaciones"}

# ── Noise filtering for qualitative comments ────────────────────────────

NOISE_VALUES: set[str] = {
    ".",
    "..",
    "-",
    "--",
    "'",
    "''",
    "n/a",
    "na",
    "no",
    "ninguna",
    "ninguno",
    "no de momento",
    "no tengo ninguna",
    "no tengo ninguna.",
    "sin comentarios",
    "sin comentarios.",
    "todo perfecto",
}

# ── Footer pattern (page numbering) ────────────────────────────────────

FOOTER_PAGE_RE = re.compile(r"(\d+)\s+de\s+(\d+)")

# ── Puntos fraction pattern ─────────────────────────────────────────────

PUNTOS_RE = re.compile(r"([\d.]+)\s*/\s*([\d.]+)")
