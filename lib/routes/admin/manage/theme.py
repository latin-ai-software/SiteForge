import os
from flask import Blueprint, render_template, redirect, url_for, flash
from lib.data.settings import get_theme, set_theme

theme_bp = Blueprint("theme", __name__, url_prefix="/admin/manage/theme")

THEME_DIR = "static"

@theme_bp.route("/")
def theme_index():
    themes = [f for f in os.listdir(THEME_DIR) if f.endswith(".css")]
    current = get_theme()
    return render_template("admin/theme/index.html", themes=themes, current=current)

@theme_bp.route("/set/<name>")
def theme_set(name):
    set_theme(name)
    flash(f"Theme geändert zu: {name}", "success")
    return redirect(url_for("theme.theme_index"))
