"""Issue #21: new generation-side sub-agent definitions are well-formed."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
NEW_AGENTS = ["progress-digest", "moshi-explainer"]


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path} missing YAML frontmatter"
    _, fm, _ = text.split("---", 2)
    data = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


@pytest.mark.parametrize("name", NEW_AGENTS)
def test_new_agents_have_frontmatter(name):
    path = AGENTS_DIR / f"{name}.md"
    assert path.exists(), f"missing {path}"
    fm = _frontmatter(path)
    for key in ("name", "description", "tools"):
        assert key in fm, f"{path} frontmatter missing '{key}'"
    assert fm["name"] == name, f"{path} name should be '{name}'"
