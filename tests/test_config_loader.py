import json
from pathlib import Path

import pytest

from src.core.config_loader import ConfigLoader

_TIER_FREE = {
    "free": {"max_messages": 1, "window_hours": 1, "num_ctx": 1, "num_predict": 1},
}


def _write_limits(tmp: Path) -> None:
    (tmp / "limits.json").write_text(json.dumps({"tiers": _TIER_FREE}), encoding="utf-8")


def test_validate_passes_with_repo_config() -> None:
    root = Path(__file__).resolve().parent.parent
    loader = ConfigLoader(str(root / "config" / "config.json"))
    assert loader.validate() is True


def test_validate_rejects_missing_ollama(tmp_path: Path) -> None:
    _write_limits(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"system": {"max_history": 10}}), encoding="utf-8")
    loader = ConfigLoader(str(tmp_path / "config.json"))
    with pytest.raises(ValueError, match="ollama"):
        loader.validate()


def test_validate_rejects_bad_host_scheme(tmp_path: Path) -> None:
    _write_limits(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"ollama": {"host": "ftp://x", "model": "m", "timeout": 60}, "system": {"max_history": 10}}),
        encoding="utf-8",
    )
    loader = ConfigLoader(str(tmp_path / "config.json"))
    with pytest.raises(ValueError, match="http"):
        loader.validate()
