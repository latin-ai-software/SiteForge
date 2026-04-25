"""
YouTube API route for fetching latest videos via RSS
"""
import os
import json
from flask import Blueprint, current_app, jsonify
from ...youtube_helper import YouTubeHelper

youtube_bp = Blueprint("youtube", __name__, url_prefix="/api/youtube")


def get_settings():
    """Load settings from JSON file"""
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


@youtube_bp.route("/latest-videos", methods=["GET"])
def get_latest_videos():
    """
    Get latest videos from configured YouTube channel via RSS
    
    Returns:
        JSON with video list or error message
    """
    settings = get_settings()
    channel_id = settings.get("youtube_channel_id", "").strip()
    
    if not channel_id:
        return jsonify({
            "status": "error",
            "message": "YouTube channel not configured",
            "videos": []
        })
    
    # Extract channel ID from URL if needed
    channel_id = YouTubeHelper.extract_channel_id(channel_id)
    
    helper = YouTubeHelper()
    videos = helper.get_latest_videos(channel_id, max_results=2)
    
    # Format dates
    for video in videos:
        video['published_at_formatted'] = YouTubeHelper.format_date(video['published_at'])
    
    return jsonify({
        "status": "ok",
        "videos": videos,
        "count": len(videos)
    })
