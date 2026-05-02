import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from ..netdefense.check import MalwareChecker

# Add Intermediarium cache
try:
    from Intermediarium import Cache
    _cache_available = True
except ImportError:
    _cache_available = False

class FileManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.uploads_dir = os.path.join(base_path, "data", "uploads")
        self.security = MalwareChecker()
        os.makedirs(self.uploads_dir, exist_ok=True)

    def _is_allowed_file(self, filename, allowed_extensions=None):
        """Check if file extension is allowed"""
        if allowed_extensions is None:
            allowed_extensions = {
                'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'doc', 'docx',
                'xls', 'xlsx', 'ppt', 'pptx', 'mp3', 'mp4', 'avi', 'mov', 'wav', 'wmv', 'ico'
            }

        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def _generate_unique_filename(self, original_filename):
        """Generate a unique filename to prevent conflicts"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())
        return f"{unique_id}.{ext}" if ext else unique_id

    def _is_binary_file(self, filename, file_content):
        """Return True for known binary media/file types to skip text scanning."""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        binary_extensions = {
            'mp3', 'mp4', 'avi', 'mov', 'wmv', 'wav', 'ogg', 'm4a',
            'png', 'jpg', 'jpeg', 'gif', 'ico', 'webp', 'zip', 'pdf', 'doc', 'docx',
            'ppt', 'pptx', 'xlsx', 'xls'
        }
        if ext in binary_extensions:
            return True

        if not file_content:
            return False

        non_text_bytes = sum(1 for b in file_content if b < 9 or (13 < b < 32) or b == 127)
        return non_text_bytes / max(len(file_content), 1) > 0.30

    def save_file(self, file, max_size_mb=10):
        """
        Save uploaded file with security checks
        Returns: (success, filename_or_error_message, file_info)
        """
        if not file or not file.filename:
            return False, "No file provided", None

        filename = secure_filename(file.filename)

        # Check file size (max 10MB by default)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > max_size_mb * 1024 * 1024:
            return False, f"File too large (max {max_size_mb}MB)", None

        # Check file extension
        if not self._is_allowed_file(filename):
            return False, "File type not allowed", None

        # Security scan - skip text scanning for binary media files
        file_content = file.read()
        
        # Malware scan
        if self.security.is_suspicious(file_content):
            return False, "Malware detected: suspicious content found", None
        
        if not self._is_binary_file(filename, file_content):
            try:
                # Try to decode as UTF-8 text
                text_content = file_content.decode('utf-8', errors='ignore')
                if self.security.is_suspicious(text_content):
                    result = self.security.check_text(text_content)
                    return False, f"File contains suspicious content: {result}", None
            except UnicodeDecodeError:
                pass

        # Reset file pointer for saving
        file.seek(0)

        # Generate unique filename
        unique_filename = self._generate_unique_filename(filename)
        file_path = os.path.join(self.uploads_dir, unique_filename)

        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
        except Exception as e:
            return False, f"Failed to save file: {str(e)}", None

        # Get file info
        mime_type, _ = mimetypes.guess_type(filename)
        file_info = {
            'original_name': filename,
            'filename': unique_filename,
            'size': file_size,
            'mime_type': mime_type or 'application/octet-stream',
            'path': file_path
        }

        return True, unique_filename, file_info

    def delete_file(self, filename):
        """Delete a file"""
        file_path = os.path.join(self.uploads_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception:
                return False
        return False

    def get_file_path(self, filename):
        """Get full path to a file"""
        return os.path.join(self.uploads_dir, filename)

    def get_file_url(self, filename):
        """Get URL path for a file"""
        return f"/uploads/{filename}"

    def list_files(self):
        """List all uploaded files"""
        if not os.path.exists(self.uploads_dir):
            return []

        files = []
        for filename in os.listdir(self.uploads_dir):
            file_path = os.path.join(self.uploads_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        return files