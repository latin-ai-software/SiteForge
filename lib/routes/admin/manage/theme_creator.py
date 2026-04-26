import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from lib.theme_creator.generator import THEME_VARS, generate_theme_file

theme_creator_bp = Blueprint("theme_creator", __name__, url_prefix="/admin/manage/theme-creator")

THEME_DIR = "static"

def get_themes():
    return [f for f in os.listdir(THEME_DIR) if f.endswith(".css")]

@theme_creator_bp.route("/")
def index():
    themes = get_themes()
    return render_template("admin/theme_creator/index.html", themes=themes)

@theme_creator_bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Bitte einen Theme-Namen angeben.", "error")
            return redirect(url_for("theme_creator.new"))

        if not name.endswith(".css"):
            name += ".css"

        output_path = os.path.join(THEME_DIR, name)
        if os.path.exists(output_path):
            flash("Theme existiert bereits.", "error")
            return redirect(url_for("theme_creator.new"))

        generate_theme_file(request.form, output_path)
        flash("Theme erstellt.", "success")
        return redirect(url_for("theme_creator.index"))

    return render_template("admin/theme_creator/new.html", vars=THEME_VARS)

@theme_creator_bp.route("/edit/<name>", methods=["GET", "POST"])
def edit(name):
    path = os.path.join(THEME_DIR, name)

    if not os.path.exists(path):
        flash("Theme nicht gefunden.", "error")
        return redirect(url_for("theme_creator.index"))

    if request.method == "POST":
        generate_theme_file(request.form, path)
        flash("Theme gespeichert.", "success")
        return redirect(url_for("theme_creator.index"))

    # Simple Parser: liest nur :root-Block und extrahiert --var: value;
    values = {}
    with open(path, "r", encoding="utf-8") as f:
        in_root = False
        for line in f:
            line = line.strip()
            if line.startswith(":root"):
                in_root = True
                continue
            if in_root and line.startswith("}"):
                break
            if in_root and line.startswith("--"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()[2:]  # ohne --
                    val = parts[1].strip().rstrip(";")
                    values[var_name] = val

    # Merge mit Defaults
    filled_vars = []
    for v in THEME_VARS:
        key = v["name"]
        filled_vars.append({
            **v,
            "value": values.get(key, v["default"])
        })

    return render_template("admin/theme_creator/edit.html", name=name, vars=filled_vars)
