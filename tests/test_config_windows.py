"""Windows-safe TOML path serialization."""

from __future__ import annotations

import tempfile
from pathlib import Path

from anima.config.schema import default_config, load_config, save_config


def test_toml_roundtrip_windows_paths(tmp_path: Path) -> None:
    nested = tmp_path / "data" / "nested"
    cfg = default_config(nested)
    path = save_config(cfg)
    text = path.read_text(encoding="utf-8")
    assert "\\" not in text or "/" in text
    loaded = load_config(path)
    assert loaded.data_dir.resolve() == cfg.data_dir.resolve()
    assert loaded.sibyl_db.resolve() == cfg.sibyl_db.resolve()


def test_setup_writes_loadable_config_on_windows() -> None:
    with tempfile.TemporaryDirectory(prefix="anima-toml-") as tmp:
        root = Path(tmp)
        cfg = default_config(root)
        save_config(cfg)
        loaded = load_config(data_dir=root)
        assert loaded.primary_brain_id == cfg.primary_brain_id
