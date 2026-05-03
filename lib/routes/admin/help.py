"""Admin help page route."""
from flask import Blueprint, render_template
from ...netdefense.auth.identitas_auth import IdentitasAuthManager
import os

# Blueprint name is internal; endpoint is explicitly set to 'admin_help'
admin_help_bp = Blueprint('admin_help_routes', __name__, url_prefix='/admin')

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
auth = IdentitasAuthManager(BASE_PATH)


@admin_help_bp.route('/help', methods=['GET'], endpoint='admin_help')
@auth.require_admin
def help_page():
    """Admin help page."""
    return render_template('admin/help.html')


def _register_admin_help_alias(state):
    """Register a direct admin_help endpoint alias for templates."""
    app = state.app
    app.add_url_rule('/admin/help', endpoint='admin_help', view_func=help_page)


admin_help_bp.record(_register_admin_help_alias)
