"""Issue #19 / #21: documentation presence and content checks."""

from pathlib import Path

EXP_DIR = Path(__file__).resolve().parents[1]
DOCS = EXP_DIR / "docs"

SCENARIOS = [
    "long_monologue_5min",
    "long_context_recall",
    "interruption_after_long_context",
    "topic_shift",
]


def test_moshi_internals_exists_and_sections():
    p = DOCS / "moshi-internals.md"
    assert p.exists(), f"missing {p}"
    text = p.read_text(encoding="utf-8")
    for kw in ["Mimi", "全二重", "KVキャッシュ", "Temporal", "Depth", "内部独白"]:
        assert kw in text, f"'{kw}' not found in moshi-internals.md"


def test_experiment_mechanism_map_covers_all_scenarios():
    text = (DOCS / "moshi-internals.md").read_text(encoding="utf-8")
    for scenario in SCENARIOS:
        assert scenario in text, f"scenario '{scenario}' missing from mechanism map"


def test_connect_doc_exists():
    p = DOCS / "connect-claude-ai.md"
    assert p.exists(), f"missing {p}"
    text = p.read_text(encoding="utf-8")
    assert "GitHub" in text
    assert "pull" in text
