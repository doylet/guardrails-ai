# tests/conftest.py (lightweight check)
import pytest
import pathlib
import sys

FORBIDDEN = ("src.ai_deck_gen.engines.",)
ALLOWED   = ("src.ai_deck_gen.domain.ports", "app.cli.v1")

def pytest_collection_modifyitems(config, items):
    # Ensure markers exist on each test file (at least one common marker somewhere)
    missing_markers = []
    for item in items:
        if not any(m in item.keywords for m in ("unit","contract","integration","e2e","smoke","performance")):
            missing_markers.append(item.nodeid)
    if missing_markers:
        config.warn(code="GDM001", message=f"Missing test markers on: {missing_markers[:10]} …")

def pytest_sessionstart(session):
    # Simple source import scan (block deep engine imports in tests)
    root = pathlib.Path.cwd()
    for p in root.rglob("tests/**/*.py"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if any(f in txt for f in FORBIDDEN) and not any(a in txt for a in ALLOWED):
            print(f"[guardrails] Forbidden engine import in tests: {p}", file=sys.stderr)
            pytest.exit("Forbidden deep engine imports; use ports/CLI", returncode=2)
