import os
from flask import Blueprint, current_app, render_template, request, redirect, abort
from .....netdefense.auth.provider import AuthManager

admin_templates_bp = Blueprint("admin_templates", __name__, url_prefix="/admin/manage/templates")

auth = AuthManager(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))))

def get_static_path():
    return os.path.join(current_app.root_path, "static")

def get_active_theme_path():
    return os.path.join(current_app.root_path, "data", "active_theme.txt")


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