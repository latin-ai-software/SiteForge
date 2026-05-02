import json
import os
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from lib.routes.data.youtube import get_settings, get_latest_videos


@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.root_path = str(tmp_path)
    return app


def test_get_settings_no_file(app):
    with app.app_context():
        assert get_settings() == {}


def test_get_settings_with_file(app):
    with app.app_context():
        settings_file = os.path.join(app.root_path, "data", "settings.json")
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump({"youtube_channel_id": "UC1234567890123456789012"}, f)

        settings = get_settings()
        assert settings["youtube_channel_id"] == "UC1234567890123456789012"


@patch("lib.routes.data.youtube.YouTubeHelper")
def test_get_latest_videos_missing_channel(mock_helper_class, app):
    with app.test_request_context("/api/youtube/latest-videos"):
        response = get_latest_videos()
        data = response.get_json()

        assert data["status"] == "error"
        assert data["videos"] == []


@patch("lib.routes.data.youtube.YouTubeHelper")
def test_get_latest_videos_success(mock_helper_class, app):
    with app.test_request_context("/api/youtube/latest-videos"):
        settings_file = os.path.join(app.root_path, "data", "settings.json")
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump({"youtube_channel_id": "https://www.youtube.com/channel/UC1234567890123456789012"}, f)

        mock_helper = MagicMock()
        mock_helper_class.return_value = mock_helper
        mock_helper_class.extract_channel_id.return_value = "UC1234567890123456789012"
        mock_helper.get_latest_videos.return_value = [
            {"id": "abc", "published_at": "2026-05-01T12:00:00Z"}
        ]
        mock_helper_class.format_date.return_value = "2026-05-01"

        response = get_latest_videos()
        data = response.get_json()

        assert data["status"] == "ok"
        assert data["count"] == 1
        assert data["videos"][0]["published_at_formatted"] == "2026-05-01"
