"""
YouTube RSS Feed Helper - Fetches latest videos from a YouTube channel via RSS
"""
import requests
import xml.etree.ElementTree as ET
import re
from flask import current_app


class YouTubeHelper:
    """Helper class to fetch videos from YouTube channel RSS feeds (no API key required)"""
    
    def __init__(self):
        """Initialize YouTube helper"""
        self.timeout = 5
        self.rss_base_url = "https://www.youtube.com/feeds/videos.xml?channel_id="
    
    @staticmethod
    def extract_channel_id(channel_url):
        """
        Extract channel ID from various YouTube URL formats
        
        Args:
            channel_url: YouTube channel URL or channel ID
        
        Returns:
            channel_id or None if extraction fails
        """
        if not channel_url:
            return None
        
        url = channel_url.strip()
        
        # Direct channel ID (starts with UC)
        if url.startswith('UC') and len(url) == 24:
            return url
        
        # https://youtube.com/@ChannelName format
        if '/@' in url:
            match = re.search(r'/@([a-zA-Z0-9_-]+)', url)
            if match:
                return match.group(1)
        
        # https://youtube.com/c/ChannelName format
        if '/c/' in url:
            match = re.search(r'/c/([a-zA-Z0-9_-]+)', url)
            if match:
                return match.group(1)
        
        # https://youtube.com/channel/CHANNEL_ID format
        if '/channel/' in url:
            match = re.search(r'/channel/([a-zA-Z0-9_-]+)', url)
            if match:
                return match.group(1)
        
        # Assume it's a channel ID or handle
        return url
    
    def get_latest_videos(self, channel_id, max_results=2):
        if not channel_id:
            return []

        try:
            channel_id = channel_id.strip()
            rss_url = f"{self.rss_base_url}{channel_id}"

            response = requests.get(rss_url, timeout=self.timeout)

            if response.status_code != 200:
                current_app.logger.warning(f"YouTube RSS error: {response.status_code}")
                return []

            root = ET.fromstring(response.content)

            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'media': 'http://search.yahoo.com/mrss/',
                'yt': 'http://www.youtube.com/xml/schemas/2015'
            }

            videos = []
            entries = root.findall('.//atom:entry', namespaces)

            for entry in entries[:max_results]:
                try:
                    title_elem = entry.find('atom:title', namespaces)
                    title = title_elem.text if title_elem is not None else 'Untitled'

                    video_id_elem = entry.find('yt:videoId', namespaces)
                    video_id = video_id_elem.text if video_id_elem is not None else None

                    if not video_id:
                        continue

                    published_elem = entry.find('atom:published', namespaces)
                    published = published_elem.text if published_elem is not None else ''

                    author_elem = entry.find('atom:author/atom:name', namespaces)
                    channel_name = author_elem.text if author_elem is not None else ''

                    # FIXED THUMBNAIL EXTRACTION
                    thumbnail = ''

                    # 1. Try direct media:thumbnail
                    media_thumb = entry.find('media:thumbnail', namespaces)
                    if media_thumb is not None:
                        thumbnail = media_thumb.get('url')

                    # 2. Try media:group/media:thumbnail
                    if not thumbnail:
                        media_group = entry.find('media:group/media:thumbnail', namespaces)
                        if media_group is not None:
                            thumbnail = media_group.get('url')

                    # 3. Fallback to YouTube default thumbnail
                    if not thumbnail:
                        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    summary_elem = entry.find('atom:summary', namespaces)
                    description = summary_elem.text if summary_elem is not None else ''

                    videos.append({
                        'id': video_id,
                        'title': title,
                        'description': description,
                        'thumbnail': thumbnail,
                        'published_at': published,
                        'channel_title': channel_name,
                        'channel_id': channel_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })

                except Exception as e:
                    current_app.logger.error(f"Error parsing YouTube video entry: {e}")
                    continue

            return videos

        except Exception as e:
            current_app.logger.error(f"YouTube RSS error: {e}")

        return []
    
    @staticmethod
    def format_date(date_string):
        """
        Format YouTube ISO 8601 date to readable format
        
        Args:
            date_string: ISO 8601 date string (e.g., "2026-04-25T10:30:00Z")
        
        Returns:
            Formatted date string (e.g., "25. Apr 2026")
        """
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%d. %b %Y')
        except:
            return date_string
