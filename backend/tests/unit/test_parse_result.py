"""Unit tests for ParseResult, ParseError, and ParseWarning types."""

from app.modules.evaluacion_docente.application.parsing.errors import (
    ParseError,
    ParseMetadata,
    ParseResult,
    ParseWarning,
)


class TestParseError:
    def test_frozen(self):
        err = ParseError(stage="open", code="CORRUPT_PDF", message="broken")
        assert err.stage == "open"
        assert err.context == {}

    def test_with_context(self):
        err = ParseError(
            stage="header", code="MISSING", message="no professor",
            context={"page": 1},
        )
        assert err.context["page"] == 1


class TestParseWarning:
    def test_basic(self):
        w = ParseWarning(code="NOISE", message="filtered 5 comments")
        assert w.code == "NOISE"


class TestParseMetadata:
    def test_defaults(self):
        m = ParseMetadata(parser_version="1.0.0", pages_processed=10)
        assert m.total_pages_declared is None
        assert m.tables_found == 0

    def test_full(self):
        m = ParseMetadata(
            parser_version="1.0.0", pages_processed=10,
            total_pages_declared=10, tables_found=14,
            comment_sections_found=7, processing_time_ms=42.5,
        )
        assert m.processing_time_ms == 42.5


class TestParseResult:
    def test_failure(self):
        r = ParseResult(
            success=False,
            errors=[ParseError(stage="open", code="CORRUPT", message="bad")],
        )
        assert not r.success
        assert r.data is None
        assert len(r.errors) == 1

    def test_success_empty_warnings(self):
        r = ParseResult(success=True)
        assert r.warnings == []
        assert r.errors == []
