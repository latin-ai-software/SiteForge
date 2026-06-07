"""API Documentation Admin Route - API documentation panel."""

import os
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....api_docs_generator import APIDocsGenerator

admin_api_docs_bp = Blueprint("admin_api_docs", __name__, url_prefix="/admin/api-docs")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = IdentitasAuthManager(BASE_PATH)


@admin_api_docs_bp.route("/", methods=["GET"])
@auth.require_admin
def api_docs_index():
    """API Documentation Dashboard."""
    docs_gen = APIDocsGenerator(current_app.root_path)
    docs = docs_gen.generate_docs(current_app)
    
    return render_template(
        "admin/manage/api_docs/index.html",
        docs=docs,
        endpoints_tree=docs['endpoints']
    )


@admin_api_docs_bp.route("/api/generate", methods=["POST"])
@auth.require_admin
def generate_api_docs():
    """Generate API documentation and return as JSON."""
    try:
        docs_gen = APIDocsGenerator(current_app.root_path)
        docs = docs_gen.generate_docs(current_app)
        
        # Save documentation to file
        docs_file = os.path.join(current_app.root_path, "data", "api_docs.json")
        os.makedirs(os.path.dirname(docs_file), exist_ok=True)
        
        with open(docs_file, 'w', encoding='utf-8') as f:
            # Convert sets and other non-serializable values to JSON-safe data
            docs_serializable = json.loads(json.dumps(docs, default=str))
            json.dump(docs_serializable, f, indent=2)
        
        return jsonify({
            "status": "success",
            "message": "API documentation generated successfully",
            "data": docs_serializable
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_api_docs_bp.route("/api/endpoint/<endpoint>", methods=["GET"])
@auth.require_admin
def get_endpoint_details(endpoint):
    """Get detailed information about a specific endpoint."""
    try:
        docs_gen = APIDocsGenerator(current_app.root_path)
        details = docs_gen.get_endpoint_details(current_app, endpoint)
        
        if details is None:
            return jsonify({
                "status": "error",
                "message": "Endpoint not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "data": details
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_api_docs_bp.route("/api/tree", methods=["GET"])
@auth.require_admin
def get_endpoint_tree():
    """Get endpoint tree structure."""
    try:
        docs_gen = APIDocsGenerator(current_app.root_path)
        tree = docs_gen.get_endpoint_tree(current_app)
        
        return jsonify({
            "status": "success",
            "tree": tree
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_api_docs_bp.route("/api/quick-reference", methods=["GET"])
@auth.require_admin
def get_quick_reference():
    """Get API quick reference guide."""
    try:
        docs_gen = APIDocsGenerator(current_app.root_path)
        quick_ref = docs_gen.get_quick_reference(current_app)
        
        return jsonify({
            "status": "success",
            "data": quick_ref
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_api_docs_bp.route("/api/export", methods=["GET"])
@auth.require_admin
def export_api_docs():
    """Export API documentation as JSON."""
    try:
        docs_gen = APIDocsGenerator(current_app.root_path)
        docs = docs_gen.generate_docs(current_app)
        
        # Make it JSON serializable
        docs_export = json.loads(json.dumps(docs, default=str))
        
        return jsonify({
            "status": "success",
            "data": docs_export
        }), 200, {
            'Content-Disposition': 'attachment; filename="api_documentation.json"'
        }
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
