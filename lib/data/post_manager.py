import os
import json
import subprocess
from datetime import datetime
from flask import current_app

# Add Intermediarium cache
try:
    from Intermediarium import Cache
    _cache_available = True
except ImportError:
    _cache_available = False

class PostManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.posts_dir = os.path.join(base_path, "data", "posts")
        self.metadata_file = os.path.join(base_path, "data", "posts_metadata.json")
        os.makedirs(self.posts_dir, exist_ok=True)
        self._ensure_metadata_file()
        # Initialize cache for post metadata (30 minute TTL)
        if _cache_available:
            self._post_cache = Cache(maxsize=1000, policy='lru', ttl=1800)
        else:
            self._post_cache = None

    def _ensure_metadata_file(self):
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _run_git_command(self, repo_path, args):
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip() or e.stdout.strip()
        except FileNotFoundError:
            return False, "Git ist nicht installiert oder nicht im PATH verfügbar."

    def _create_git_repository(self, repo_name, author):
        """Create a new Git repository for the given repo name and author"""
        try:
            repo_root = os.path.join(self.base_path, "static", "git")
            user_repo_dir = os.path.join(repo_root, author)
            os.makedirs(user_repo_dir, exist_ok=True)

            target_dir = os.path.join(user_repo_dir, repo_name)
            if os.path.exists(target_dir):
                return True  # Repository already exists

            # Initialize empty git repo
            success, result = self._run_git_command(self.base_path, ["init", target_dir])
            if not success:
                print(f"Failed to init git repo: {result}")
                return False

            # Configure git user
            success, result = self._run_git_command(target_dir, ["config", "user.name", author])
            if success:
                success, result = self._run_git_command(target_dir, ["config", "user.email", f"{author}@localhost"])

            if success:
                # Create README
                readme_path = os.path.join(target_dir, "README.md")
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(f"# {repo_name}\n\nRepository created by {author}\n")
                success, result = self._run_git_command(target_dir, ["add", "README.md"])

            if success:
                success, result = self._run_git_command(target_dir, ["commit", "-m", "Initial commit"])

            if success:
                # Update git repos data
                git_data_file = os.path.join(self.base_path, "data", "git_repos.json")
                os.makedirs(os.path.dirname(git_data_file), exist_ok=True)
                
                if os.path.exists(git_data_file):
                    with open(git_data_file, "r", encoding="utf-8") as f:
                        git_data = json.load(f)
                else:
                    git_data = {}

                if author not in git_data:
                    git_data[author] = {}

                # Get base URL dynamically - use request.host_url if available, otherwise build from settings
                try:
                    from flask import request
                    base_url = request.host_url.rstrip("/")
                except (RuntimeError, ImportError):
                    # Fallback: try to get from settings
                    base_url = "http://localhost"
                    try:
                        settings = json.load(open(os.path.join(os.path.dirname(__file__), "../../data/settings.json"), "r", encoding="utf-8"))
                        if settings.get("domain"):
                            domain = settings.get("domain").strip()
                            if domain.startswith("http://") or domain.startswith("https://"):
                                base_url = domain.rstrip("/")
                            else:
                                base_url = f"https://{domain}"
                    except:
                        pass
                
                git_data[author][repo_name] = {
                    "remote": "",
                    "branch": "main",
                    "clone_url": f"{base_url}/git/{author}/{repo_name}",
                    "created_at": datetime.now().isoformat()
                }
                with open(git_data_file, "w", encoding="utf-8") as f:
                    json.dump(git_data, f, indent=4, default=str)

            return success
        except Exception as e:
            print(f"Error creating git repository: {e}")
            return False

    def _load_metadata(self):
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_metadata(self, data):
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)

    def create_post(self, title, content, author, status="publish", post_type="post", categories=None, tags=None, attachments=None, git_repository=None, release_tag=None):
        metadata = self._load_metadata()

        # Generate slug from title
        slug = self._generate_slug(title)
        if slug in metadata:
            # Handle duplicates
            counter = 1
            while f"{slug}-{counter}" in metadata:
                counter += 1
            slug = f"{slug}-{counter}"

        post_id = slug
        now = datetime.now()

        metadata[post_id] = {
            "id": post_id,
            "title": title,
            "content": content,
            "author": author,
            "status": status,
            "type": post_type,
            "categories": categories or [],
            "tags": tags or [],
            "attachments": attachments or [],
            "git_repository": git_repository or "",
            "release_tag": release_tag or "",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
            "slug": slug
        }

        self._save_metadata(metadata)

        # Automatically create Git repository if git_repository is specified
        if git_repository:
            self._create_git_repository(git_repository, author)

        return post_id

    def update_post(self, post_id, title=None, content=None, status=None, categories=None, tags=None, attachments=None, git_repository=None, release_tag=None):
        metadata = self._load_metadata()
        if post_id not in metadata:
            return False

        if title is not None:
            metadata[post_id]["title"] = title
        if content is not None:
            metadata[post_id]["content"] = content
        if status is not None:
            metadata[post_id]["status"] = status
        if categories is not None:
            metadata[post_id]["categories"] = categories
        if tags is not None:
            metadata[post_id]["tags"] = tags
        if attachments is not None:
            metadata[post_id]["attachments"] = attachments
        if git_repository is not None:
            old_git_repo = metadata[post_id].get("git_repository")
            metadata[post_id]["git_repository"] = git_repository
            # Create Git repository if it was added
            if git_repository and not old_git_repo:
                self._create_git_repository(git_repository, metadata[post_id]["author"])
        if release_tag is not None:
            metadata[post_id]["release_tag"] = release_tag

        metadata[post_id]["modified_at"] = datetime.now().isoformat()
        self._save_metadata(metadata)
        return True

    def get_post(self, post_id):
        metadata = self._load_metadata()
        return metadata.get(post_id)

    def get_posts(self, status="publish", post_type="post", limit=None):
        metadata = self._load_metadata()
        posts = []

        for post_id, post_data in metadata.items():
            # If status is None, get all posts regardless of status
            # Otherwise, filter by the specified status
            status_match = status is None or post_data.get("status") == status
            type_match = post_data.get("type") == post_type

            if status_match and type_match:
                posts.append(post_data)

        # Sort by creation date, newest first
        posts.sort(key=lambda x: x["created_at"], reverse=True)

        if limit:
            posts = posts[:limit]

        return posts

    def delete_post(self, post_id):
        metadata = self._load_metadata()
        if post_id in metadata:
            del metadata[post_id]
            self._save_metadata(metadata)
            return True
        return False

    def _generate_slug(self, title):
        # Simple slug generation
        return title.lower().replace(" ", "-").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")

    def get_posts_by_category(self, category, status="publish"):
        metadata = self._load_metadata()
        posts = []

        for post_id, post_data in metadata.items():
            if post_data.get("status") == status and category in post_data.get("categories", []):
                posts.append(post_data)

        posts.sort(key=lambda x: x["created_at"], reverse=True)
        return posts

    def get_posts_by_tag(self, tag, status="publish"):
        metadata = self._load_metadata()
        posts = []

        for post_id, post_data in metadata.items():
            if post_data.get("status") == status and tag in post_data.get("tags", []):
                posts.append(post_data)

        posts.sort(key=lambda x: x["created_at"], reverse=True)
        return posts

    def get_all_categories(self):
        metadata = self._load_metadata()
        categories = set()
        for post_data in metadata.values():
            categories.update(post_data.get("categories", []))
        return sorted(list(categories))

    def get_all_tags(self):
        metadata = self._load_metadata()
        tags = set()
        for post_data in metadata.values():
            tags.update(post_data.get("tags", []))
        return sorted(list(tags))

    def search_posts(self, query, status="publish"):
        metadata = self._load_metadata()
        query_lower = query.lower().strip()
        posts = []

        for post_id, post_data in metadata.items():
            if status is not None and post_data.get("status") != status:
                continue
            if query_lower in post_data.get("title", "").lower() or \
               query_lower in post_data.get("content", "").lower() or \
               query_lower in post_data.get("slug", "").lower() or \
               any(query_lower in (category.lower() if category else "") for category in post_data.get("categories", [])) or \
               any(query_lower in (tag.lower() if tag else "") for tag in post_data.get("tags", [])):
                posts.append(post_data)

        posts.sort(key=lambda x: x["created_at"], reverse=True)
        return posts

    def get_posts_by_author(self, author, status="publish"):
        metadata = self._load_metadata()
        posts = []

        for post_id, post_data in metadata.items():
            if post_data.get("status") == status and post_data.get("author") == author:
                posts.append(post_data)

        posts.sort(key=lambda x: x["created_at"], reverse=True)
        return posts