import sys
from flask import Flask, render_template, send_from_directory
import lib.netdefense.check
from lib.routes.create.post.index import post_create_bp
from lib.routes.root.index import root_bp
from lib.routes.admin.manage.templates.index import admin_templates_bp
from lib.routes.admin.manage.posts.index import admin_posts_bp
from lib.routes.admin.manage.users.index import admin_users_bp
from lib.routes.admin.manage.settings.index import admin_settings_bp
from lib.routes.root.auth import auth_bp
from lib.netdefense.auth.provider import AuthManager
import os

app = Flask(__name__)
app.secret_key = "irgendein_langes_random_secret_das_wirklich_gar_keiner_kompromittier_dabei_bin_ich_mir_sicher_vertrau_mir"

app.register_blueprint(post_create_bp)
app.register_blueprint(root_bp)
app.register_blueprint(admin_templates_bp)
app.register_blueprint(admin_posts_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(admin_settings_bp)
app.register_blueprint(auth_bp)

# Route for serving uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    uploads_dir = os.path.join(app.root_path, 'data', 'uploads')
    return send_from_directory(uploads_dir, filename)


def handle_cli():
    """
    CLI‑Argumente prüfen:
    --create-admin <name> -p <passwort> [--role <role>]
    """
    if "--create-admin" in sys.argv:
        try:
            name_index = sys.argv.index("--create-admin") + 1
            username = sys.argv[name_index]
        except Exception:
            print("Fehler: Benutzername fehlt nach --create-admin")
            sys.exit(1)

        if "-p" not in sys.argv:
            print("Fehler: Passwort fehlt. Nutze: --create-admin <name> -p <passwort> [--role <role>]")
            sys.exit(1)

        try:
            pass_index = sys.argv.index("-p") + 1
            password = sys.argv[pass_index]
        except Exception:
            print("Fehler: Passwort fehlt nach -p")
            sys.exit(1)

        role = "administrator"  # default
        if "--role" in sys.argv:
            try:
                role_index = sys.argv.index("--role") + 1
                role = sys.argv[role_index]
            except Exception:
                print("Fehler: Rolle fehlt nach --role")
                sys.exit(1)

        base_path = os.path.dirname(os.path.abspath(__file__))
        auth = AuthManager(base_path)

        ok, msg = auth.create_user(username, password, role)
        print(msg)

        # Admin erzwingen
        if ok and username != "admin":
            print("Hinweis: Nur der Benutzername 'admin' gilt als Administrator.")
            print("Wenn du einen Admin willst, nutze:")
            print("   --create-admin admin -p <passwort>")

        sys.exit(0)


if __name__ == "__main__":
    handle_cli()
    app.run(debug=True)