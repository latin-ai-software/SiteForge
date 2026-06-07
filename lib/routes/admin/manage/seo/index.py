"""SEO Admin Route - SEO analysis and management panel."""

import os
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....seo_analyzer import SEOAnalyzer

admin_seo_bp = Blueprint("admin_seo", __name__, url_prefix="/admin/seo")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = IdentitasAuthManager(BASE_PATH)

FIXABLE_ISSUE_MAP = {
    "Missing meta description on index page": {
        "fix_key": "add_meta_description",
        "label": "Add meta description"
    },
    "Meta keywords not found": {
        "fix_key": "add_meta_keywords",
        "label": "Add keywords meta"
    },
    "Missing page title": {
        "fix_key": "add_title_tag",
        "label": "Add title tag"
    },
    "Missing viewport meta tag": {
        "fix_key": "add_viewport_meta",
        "label": "Add viewport tag"
    },
    "Open Graph meta tags not found": {
        "fix_key": "add_open_graph_tags",
        "label": "Add Open Graph tags"
    },
    "sitemap.xml not found": {
        "fix_key": "create_sitemap_xml",
        "label": "Create sitemap.xml"
    },
    "robots.txt not found": {
        "fix_key": "create_robots_txt",
        "label": "Create robots.txt"
    }
}


def _get_fix_actions(analysis_results):
    actions = []
    for item in (analysis_results.get("issues", []) + analysis_results.get("warnings", [])):
        cleaned = item.replace("✗", "").replace("⚠", "").strip()
        for key, fix in FIXABLE_ISSUE_MAP.items():
            if key in cleaned:
                actions.append({
                    "issue": item,
                    "fix_key": fix["fix_key"],
                    "label": fix["label"]
                })
    return actions


def _insert_into_head(file_path, content_to_add):
    if not os.path.exists(file_path):
        return False
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if content_to_add in content:
        return False
    if '<head>' in content:
        content = content.replace('<head>', '<head>\n    ' + content_to_add, 1)
    elif '<head ' in content:
        content = content.replace('>', '>\n    ' + content_to_add, 1)
    else:
        return False
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def _create_file_if_missing(file_path, content):
    if os.path.exists(file_path):
        return False
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def _apply_fix(base_path, fix_key):
    root_index = os.path.join(base_path, 'templates', 'root', 'index.html')
    base_template = os.path.join(base_path, 'templates', 'base.html')
    robots_file = os.path.join(base_path, 'static', 'robots.txt')
    sitemap_file = os.path.join(base_path, 'static', 'sitemap.xml')

    if fix_key == 'add_meta_description':
        return _insert_into_head(root_index, '<meta name="description" content="Add a short site description here">')
    if fix_key == 'add_meta_keywords':
        return _insert_into_head(root_index, '<meta name="keywords" content="keyword1, keyword2, keyword3">')
    if fix_key == 'add_title_tag':
        return _insert_into_head(root_index, '<title>Your Site Title</title>')
    if fix_key == 'add_viewport_meta':
        return _insert_into_head(base_template, '<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    if fix_key == 'add_open_graph_tags':
        return _insert_into_head(root_index, '<meta property="og:title" content="Your Site Title">\n    <meta property="og:description" content="A short description for social sharing">\n    <meta property="og:type" content="website">')
    if fix_key == 'create_robots_txt':
        return _create_file_if_missing(robots_file, 'User-agent: *\nDisallow: /admin\nDisallow: /uploads\n')
    if fix_key == 'create_sitemap_xml':
        return _create_file_if_missing(sitemap_file, '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n    <url>\n        <loc>http://localhost:5000/</loc>\n        <changefreq>daily</changefreq>\n    </url>\n</urlset>\n')
    return False


@admin_seo_bp.route("/", methods=["GET"])
@auth.require_admin
def seo_index():
    """SEO Analysis Dashboard."""
    analyzer = SEOAnalyzer(current_app.root_path)
    analysis_results = analyzer.analyze()
    fix_actions = _get_fix_actions(analysis_results)
    
    return render_template(
        "admin/manage/seo/index.html",
        analysis=analysis_results,
        fix_actions=fix_actions
    )


@admin_seo_bp.route("/api/analyze", methods=["POST"])
@auth.require_admin
def run_seo_analysis():
    """Run SEO analysis and return results as JSON."""
    try:
        analyzer = SEOAnalyzer(current_app.root_path)
        analysis_results = analyzer.analyze()
        
        # Save analysis to file
        analysis_file = os.path.join(current_app.root_path, "data", "seo_analysis.json")
        os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        return jsonify({
            "status": "success",
            "data": analysis_results
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_seo_bp.route("/api/fix", methods=["POST"])
@auth.require_admin
def seo_fix_issue():
    """Apply a quick fix for a known SEO issue."""
    try:
        data = request.get_json() or {}
        fix_key = data.get('fix_key')
        if not fix_key:
            return jsonify({
                "status": "error",
                "message": "Missing fix_key"
            }), 400

        success = _apply_fix(current_app.root_path, fix_key)
        if not success:
            return jsonify({
                "status": "error",
                "message": "Could not apply the requested fix or the issue is already fixed"
            }), 400

        return jsonify({
            "status": "success",
            "message": "Quick fix applied successfully. Run analysis again to verify."
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_seo_bp.route("/api/history", methods=["GET"])
@auth.require_admin
def seo_history():
    """Get SEO analysis history."""
    try:
        analysis_file = os.path.join(current_app.root_path, "data", "seo_analysis.json")
        
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            return jsonify({
                "status": "success",
                "data": analysis_data
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No analysis data available yet"
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_seo_bp.route("/recommendations", methods=["GET"])
@auth.require_admin
def seo_recommendations():
    """Get SEO improvement recommendations."""
    recommendations = [
        {
            "category": "Meta Tags",
            "priority": "High",
            "items": [
                "Add comprehensive meta descriptions to all pages",
                "Include target keywords in meta titles",
                "Add Open Graph tags for social sharing",
                "Set canonical URLs for duplicate content"
            ]
        },
        {
            "category": "Content",
            "priority": "High",
            "items": [
                "Ensure each page has at least one H1 tag",
                "Use descriptive, keyword-rich headings",
                "Add alt text to all images",
                "Create internal links between related pages",
                "Maintain consistent content quality and length"
            ]
        },
        {
            "category": "Performance",
            "priority": "Medium",
            "items": [
                "Enable GZIP compression",
                "Minify CSS and JavaScript files",
                "Optimize and compress images",
                "Implement lazy loading for images",
                "Use a CDN for static assets",
                "Reduce server response time"
            ]
        },
        {
            "category": "Technical",
            "priority": "High",
            "items": [
                "Ensure mobile-friendly design (responsive layout)",
                "Fix all broken internal links",
                "Implement XML sitemap",
                "Use HTTPS on all pages",
                "Set up proper redirects (301)",
                "Implement structured data markup"
            ]
        },
        {
            "category": "Links & Authority",
            "priority": "Medium",
            "items": [
                "Build quality backlinks",
                "Create internal linking strategy",
                "Get listed in relevant directories",
                "Submit to business listings",
                "Engage on social media"
            ]
        },
        {
            "category": "User Experience",
            "priority": "Medium",
            "items": [
                "Improve page load speed",
                "Optimize for mobile devices",
                "Clear call-to-action buttons",
                "Easy navigation structure",
                "Reduce bounce rate with engaging content"
            ]
        }
    ]
    
    return jsonify({
        "status": "success",
        "recommendations": recommendations
    })
