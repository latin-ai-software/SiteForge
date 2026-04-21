import os
import json
from pathlib import Path


class MediaManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.uploads_dir = os.path.join(base_path, "data", "uploads")
        self.posts_dir = os.path.join(base_path, "data", "posts")
        self.posts_metadata_file = os.path.join(base_path, "data", "posts_metadata.json")

        # Create uploads directory if it doesn't exist
        os.makedirs(self.uploads_dir, exist_ok=True)

    def get_all_files(self):
        """Get all uploaded files with metadata"""
        files = []
        
        if not os.path.exists(self.uploads_dir):
            return files

        for filename in os.listdir(self.uploads_dir):
            filepath = os.path.join(self.uploads_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "path": filepath,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "url": f"/data/uploads/{filename}"
                })

        # Sort by modified date (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    def find_file_usage(self, filename):
        """Find which posts use this file"""
        usage = []
        
        # Check posts metadata
        if os.path.exists(self.posts_metadata_file):
            try:
                with open(self.posts_metadata_file, "r", encoding="utf-8") as f:
                    posts_meta = json.load(f)
                    
                for post_id, post_data in posts_meta.items():
                    # Check if filename is referenced in content
                    content = post_data.get("content", "")
                    if filename in content:
                        usage.append({
                            "post_id": post_id,
                            "title": post_data.get("title", "Untitled"),
                            "type": "post"
                        })
            except:
                pass

        # Check post HTML files
        if os.path.exists(self.posts_dir):
            for post_file in os.listdir(self.posts_dir):
                if post_file.endswith(".html"):
                    filepath = os.path.join(self.posts_dir, post_file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            if filename in content:
                                post_id = post_file.replace(".html", "")
                                # Check if already in usage
                                if not any(u["post_id"] == post_id for u in usage):
                                    usage.append({
                                        "post_id": post_id,
                                        "title": post_id,
                                        "type": "post"
                                    })
                    except:
                        pass

        return usage

    def delete_file(self, filename):
        """Delete a file from uploads"""
        filepath = os.path.join(self.uploads_dir, filename)
        
        # Security check: ensure path is within uploads directory
        if not os.path.abspath(filepath).startswith(os.path.abspath(self.uploads_dir)):
            return False, "Invalid file path"
        
        if not os.path.exists(filepath):
            return False, "File not found"
        
        try:
            os.remove(filepath)
            return True, "File deleted successfully"
        except Exception as e:
            return False, str(e)

    def get_file_info(self, filename):
        """Get detailed info about a file"""
        filepath = os.path.join(self.uploads_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        usage = self.find_file_usage(filename)
        
        return {
            "filename": filename,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "url": f"/data/uploads/{filename}",
            "usage": usage,
            "is_image": filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')),
            "is_document": filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.xlsx', '.pptx')),
            "is_video": filename.lower().endswith(('.mp4', '.webm', '.avi', '.mov'))
        }

    def get_usage_summary(self):
        """Get summary of all files and their usage"""
        files = self.get_all_files()
        summary = []
        
        for file_info in files:
            usage = self.find_file_usage(file_info["filename"])
            summary.append({
                **file_info,
                "usage_count": len(usage),
                "usage": usage
            })
        
        return summary
