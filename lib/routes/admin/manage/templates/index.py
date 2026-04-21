import os
import json
import uuid
from flask import Blueprint, current_app, render_template, request, redirect, abort, jsonify
from .....netdefense.auth.provider import AuthManager

admin_templates_bp = Blueprint("admin_templates", __name__, url_prefix="/admin/manage/templates")

auth = AuthManager(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))))

def get_static_path():
    return os.path.join(current_app.root_path, "static")

def get_active_theme_path():
    return os.path.join(current_app.root_path, "data", "active_theme.txt")

def get_index_text_path():
    return os.path.join(current_app.root_path, "data", "index_texts.json")

def load_index_texts():
    """Load all index texts from file"""
    path = get_index_text_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("texts", [])
        except:
            return []
    return []

def save_index_texts(texts):
    """Save all index texts to file"""
    data_path = os.path.join(current_app.root_path, "data")
    os.makedirs(data_path, exist_ok=True)
    
    path = get_index_text_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"texts": texts}, f, ensure_ascii=False, indent=2)


@admin_templates_bp.route("/", methods=["GET"])
@auth.require_admin
def manage_templates():
    static_path = get_static_path()
    os.makedirs(static_path, exist_ok=True)

    stylesheets = [f for f in os.listdir(static_path) if f.endswith(".css")]

    active_theme = None
    active_path = get_active_theme_path()
    if os.path.exists(active_path):
        with open(active_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    return render_template("admin/manage/templates/index.html",
                           stylesheets=stylesheets,
                           active_theme=active_theme)


@admin_templates_bp.route("/upload", methods=["POST"])
@auth.require_admin
def upload_template():
    file = request.files.get("file")

    if not file or not file.filename.endswith(".css"):
        return "Nur .css Dateien erlaubt", 400

    static_path = get_static_path()
    os.makedirs(static_path, exist_ok=True)

    save_path = os.path.join(static_path, file.filename)
    file.save(save_path)

    return redirect("/admin/manage/templates")


@admin_templates_bp.route("/activate/<filename>", methods=["POST"])
@auth.require_admin
def activate_template(filename):
    static_path = get_static_path()
    file_path = os.path.join(static_path, filename)

    if not os.path.exists(file_path):
        abort(404)

    active_path = get_active_theme_path()
    os.makedirs(os.path.dirname(active_path), exist_ok=True)

    with open(active_path, "w", encoding="utf-8") as f:
        f.write(filename)

    return redirect("/admin/manage/templates")


@admin_templates_bp.route("/save-index-text", methods=["POST"])
@auth.require_admin
def save_index_text():
    text_id = request.form.get("text_id", "").strip()
    name = request.form.get("name", "").strip()
    content = request.form.get("content", "")
    
    if not name:
        return "Text name is required", 400
    
    texts = load_index_texts()
    
    if text_id:
        # Update existing text
        text = next((t for t in texts if t["id"] == text_id), None)
        if text:
            text["name"] = name
            text["content"] = content
    else:
        # Create new text
        new_text = {
            "id": str(uuid.uuid4()),
            "name": name,
            "content": content,
            "active": len(texts) == 0  # First text is active by default
        }
        texts.append(new_text)
    
    save_index_texts(texts)
    return redirect("/admin/manage/templates")


@admin_templates_bp.route("/get-index-texts", methods=["GET"])
@auth.require_admin
def get_index_texts():
    texts = load_index_texts()
    return jsonify({"texts": texts})


@admin_templates_bp.route("/activate-index-text/<text_id>", methods=["POST"])
@auth.require_admin
def activate_index_text(text_id):
    texts = load_index_texts()
    
    # Deactivate all texts
    for text in texts:
        text["active"] = False
    
    # Activate the selected text
    text = next((t for t in texts if t["id"] == text_id), None)
    if text:
        text["active"] = True
    
    save_index_texts(texts)
    return jsonify({"status": "ok"})


@admin_templates_bp.route("/delete-index-text/<text_id>", methods=["POST"])
@auth.require_admin
def delete_index_text(text_id):
    texts = load_index_texts()
    texts = [t for t in texts if t["id"] != text_id]
    
    # Ensure at least one text is active
    if texts and not any(t.get("active") for t in texts):
        texts[0]["active"] = True
    
    save_index_texts(texts)
    return jsonify({"status": "ok"})


# Public route for switching index text (no auth required)
@admin_templates_bp.route("/set-active-index-text/<text_id>", methods=["POST"])
def set_active_index_text(text_id):
    texts = load_index_texts()
    
    # Deactivate all texts
    for text in texts:
        text["active"] = False
    
    # Activate the selected text
    text = next((t for t in texts if t["id"] == text_id), None)
    if text:
        text["active"] = True
    
    save_index_texts(texts)
    return jsonify({"status": "ok"})