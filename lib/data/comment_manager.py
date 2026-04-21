import os
import json
from datetime import datetime

class CommentManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.comments_file = os.path.join(base_path, "data", "comments.json")
        os.makedirs(os.path.dirname(self.comments_file), exist_ok=True)
        self._ensure_comments_file()

    def _ensure_comments_file(self):
        if not os.path.exists(self.comments_file):
            with open(self.comments_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_comments(self):
        with open(self.comments_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_comments(self, data):
        with open(self.comments_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)

    def add_comment(self, post_id, author, content, parent_id=None):
        comments = self._load_comments()

        if post_id not in comments:
            comments[post_id] = []

        comment_id = str(len(comments[post_id]) + 1)
        now = datetime.now()

        comment = {
            "id": comment_id,
            "post_id": post_id,
            "author": author,
            "content": content,
            "parent_id": parent_id,
            "created_at": now.isoformat(),
            "status": "approved"  # For now, auto-approve
        }

        comments[post_id].append(comment)
        self._save_comments(comments)
        return comment_id

    def get_comments(self, post_id, status="approved"):
        comments = self._load_comments()
        post_comments = comments.get(post_id, [])

        # Filter by status and organize by parent/child
        filtered_comments = [c for c in post_comments if c.get("status") == status]

        # Organize into threads
        top_level = []
        replies = {}

        for comment in filtered_comments:
            if comment.get("parent_id"):
                parent_id = comment["parent_id"]
                if parent_id not in replies:
                    replies[parent_id] = []
                replies[parent_id].append(comment)
            else:
                top_level.append(comment)

        # Sort by creation time
        top_level.sort(key=lambda x: x["created_at"])
        for reply_list in replies.values():
            reply_list.sort(key=lambda x: x["created_at"])

        return top_level, replies

    def delete_comment(self, post_id, comment_id):
        comments = self._load_comments()
        if post_id in comments:
            comments[post_id] = [c for c in comments[post_id] if c["id"] != comment_id]
            self._save_comments(comments)
            return True
        return False