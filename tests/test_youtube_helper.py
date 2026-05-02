import pytest
from unittest.mock import patch, MagicMock
from lib.youtube_helper import YouTubeHelper


class TestYouTubeHelper:
    def test_init(self):
        """Test YouTubeHelper initialization."""
        helper = YouTubeHelper()
        assert helper.timeout == 5
        assert helper.rss_base_url == "https://www.youtube.com/feeds/videos.xml?channel_id="

    def test_extract_channel_id_direct(self):
        """Test extract_channel_id with direct channel ID."""
        channel_id = "UC123456789012345678901234"
        result = YouTubeHelper.extract_channel_id(channel_id)
        assert result == channel_id

    def test_extract_channel_id_at_format(self):
        """Test extract_channel_id with @ format."""
        url = "https://youtube.com/@ChannelName"
        result = YouTubeHelper.extract_channel_id(url)
        assert result == "ChannelName"

    def test_extract_channel_id_c_format(self):
        """Test extract_channel_id with /c/ format."""
        url = "https://youtube.com/c/ChannelName"
        result = YouTubeHelper.extract_channel_id(url)
        assert result == "ChannelName"

    def test_extract_channel_id_channel_format(self):
        """Test extract_channel_id with /channel/ format."""
        url = "https://youtube.com/channel/UC123456789012345678901234"
        result = YouTubeHelper.extract_channel_id(url)
        assert result == "UC123456789012345678901234"

    def test_extract_channel_id_user_format(self):
        """Test extract_channel_id with /user/ format."""
        url = "https://youtube.com/user/ChannelName"
        result = YouTubeHelper.extract_channel_id(url)
        assert result == "ChannelName"

    def test_extract_channel_id_invalid(self):
        """Test extract_channel_id with invalid URL."""
        url = "https://example.com"
        result = YouTubeHelper.extract_channel_id(url)
        assert result is None

    def test_extract_channel_id_empty(self):
        """Test extract_channel_id with empty input."""
        result = YouTubeHelper.extract_channel_id("")
        assert result is None

    @patch('requests.get')
    def test_get_latest_videos(self, mock_get):
        """Test get_latest_videos."""
        # Mock XML response
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>yt:video:VIDEO_ID_1</id>
                <title>Video Title 1</title>
                <published>2023-01-01T00:00:00+00:00</published>
                <media:thumbnail url="http://example.com/thumb1.jpg"/>
            </entry>
            <entry>
                <id>yt:video:VIDEO_ID_2</id>
                <title>Video Title 2</title>
                <published>2023-01-02T00:00:00+00:00</published>
                <media:thumbnail url="http://example.com/thumb2.jpg"/>
            </entry>
        </feed>"""
        mock_get.return_value = mock_response

        helper = YouTubeHelper()
        videos = helper.get_latest_videos("UC123", max_results=2)
        assert len(videos) == 2
        assert videos[0]["title"] == "Video Title 1"
        assert videos[0]["video_id"] == "VIDEO_ID_1"

    @patch('requests.get')
    def test_get_latest_videos_error(self, mock_get):
        """Test get_latest_videos with request error."""
        mock_get.side_effect = Exception("Network error")

        helper = YouTubeHelper()
        videos = helper.get_latest_videos("UC123")
        assert videos == []

    def test_format_date(self):
        """Test format_date."""
        date_string = "2023-01-01T00:00:00+00:00"
        result = YouTubeHelper.format_date(date_string)
        assert result == "2023-01-01"

    def test_format_date_invalid(self):
        """Test format_date with invalid date."""
        result = YouTubeHelper.format_date("invalid")
        assert result == "invalid"