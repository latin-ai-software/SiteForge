import os
from lib.data import settings as settings_module


def test_get_theme_returns_default_when_missing(tmp_path, monkeypatch):
    theme_file = tmp_path / "nested" / "active_theme.txt"
    monkeypatch.setattr(settings_module, "THEME_FILE", str(theme_file))

    assert settings_module.get_theme() == "theme.css"


def test_set_theme_writes_theme_file(tmp_path, monkeypatch):
    theme_file = tmp_path / "nested" / "active_theme.txt"
    monkeypatch.setattr(settings_module, "THEME_FILE", str(theme_file))

    settings_module.set_theme("custom.css")

    assert os.path.exists(str(theme_file))
    assert theme_file.read_text() == "custom.css"
    assert settings_module.get_theme() == "custom.css"
