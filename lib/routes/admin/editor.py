import os
import json
from flask import Blueprint, render_template, request, jsonify, current_app

editor_bp = Blueprint('admin_editor', __name__, url_prefix='/admin/editor')

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
PAGES_DIR = os.path.join(BASE_PATH, 'data', 'pages')
os.makedirs(PAGES_DIR, exist_ok=True)


def page_path(name):
    return os.path.join(PAGES_DIR, f"{name}.json")


def generated_path(name):
    return os.path.join(PAGES_DIR, f"{name}.generated.jinja")


def load_settings():
    settings_file = os.path.join(current_app.root_path, 'data', 'settings.json')
    settings = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception:
            settings = {}
    return settings


def default_dsl_for(page_name):
    # Build a reasonable default DSL representation from settings and templates
    settings = load_settings()
    blocks = []
    # Hero / heading
    blocks.append({
        'type': 'hero',
        'data': {
            'title': settings.get('site_title', 'SiteForge'),
            'subtitle': settings.get('slideshow_header') or settings.get('site_description', '')
        }
    })
    # Search
    blocks.append({'type': 'search', 'data': {}})
    # Index text
    blocks.append({'type': 'index_text', 'data': {}})
    # Post list
    blocks.append({'type': 'post_list', 'data': {}})
    # YouTube
    if settings.get('youtube_channel_id'):
        blocks.append({'type': 'youtube', 'data': {'channel_id': settings.get('youtube_channel_id')}})
    # Social links
    blocks.append({'type': 'social_links', 'data': {}})
    return {'blocks': blocks}


def parse_template_to_dsl(page_name):
    """Heuristic parsing of the existing template into DSL blocks.

    This is best-effort: we look for known markers/snippets in the template
    and create corresponding DSL blocks. It avoids executing Jinja.
    """
    tpl_path = os.path.join(current_app.root_path, 'templates', 'root', 'index.html')
    if not os.path.exists(tpl_path):
        return None
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            src = f.read()
    except Exception:
        return None

    blocks = []
    # Hero/slideshow detection
    if 'class="hero"' in src or 'slideshow' in src:
        blocks.append({'type': 'hero', 'data': {}})

    # Search block presence
    if 'form action="/search"' in src or 'name="q"' in src:
        blocks.append({'type': 'search', 'data': {}})

    # Index text
    if 'index-text' in src or 'index_text' in src:
        blocks.append({'type': 'index_text', 'data': {}})

    # Post list detection
    if '{% if posts %}' in src or 'for post in posts' in src:
        blocks.append({'type': 'post_list', 'data': {}})

    # YouTube
    if 'youtube-videos' in src or 'youtube_channel_id' in src or 'youtube' in src:
        # try to extract channel id from settings reference
        blocks.append({'type': 'youtube', 'data': {}})

    # Social links
    if 'show_social_links' in src or 'twitter_handle' in src or 'facebook_page' in src:
        blocks.append({'type': 'social_links', 'data': {}})

    return {'blocks': blocks} if blocks else None


@editor_bp.route('/<page_name>')
def editor(page_name='home'):
    # Render the editor application (client-side handles load/save)
    return render_template('admin/editor/editor.html', page_name=page_name)


@editor_bp.route('/api/page/<page_name>', methods=['GET'])
def get_page(page_name):
    p = page_path(page_name)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Try to parse existing site template into DSL first
        parsed = parse_template_to_dsl(page_name)
        if parsed:
            data = parsed
        else:
            # default DSL built from settings/templates so editor always has a usable model
            data = default_dsl_for(page_name)
    return jsonify(data)


@editor_bp.route('/api/page/<page_name>', methods=['POST'])
def save_page(page_name):
    try:
        payload = request.get_json() or {}
        p = page_path(page_name)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Also generate Jinja HTML from DSL and store it so the site can render it directly
        try:
            jinja = render_dsl_to_jinja(payload)
            gp = generated_path(page_name)
            with open(gp, 'w', encoding='utf-8') as gf:
                gf.write(jinja)
        except Exception:
            current_app.logger.exception('Failed to render DSL to Jinja')
        return jsonify({"status": "ok"})
    except Exception as e:
        current_app.logger.exception('Failed to save page')
        return jsonify({"status": "error", "msg": str(e)}), 500


# Convenience public API endpoints for external integrations / older clients
@editor_bp.route('/api/homepage/load', methods=['GET'])
def api_homepage_load():
    return get_page('home')


@editor_bp.route('/api/homepage/save', methods=['POST'])
def api_homepage_save():
    return save_page('home')


def render_dsl_to_jinja(dsl):
    """Transform a DSL JSON into a Jinja template string. Keep Jinja structures for dynamic parts."""
    parts = []
    for block in dsl.get('blocks', []):
        t = block.get('type')
        data = block.get('data', {})
        if t == 'hero':
            title = data.get('title', '{{ settings.site_title if settings.site_title else "SiteForge" }}')
            subtitle = data.get('subtitle', '{{ settings.site_description }}')
            parts.append(f"<header class=\"hero\">\n  <div class=\"hero-copy\">\n    <h1 class=\"title-main-index\">{title}</h1>\n    <p class=\"subtitle\">{subtitle}</p>\n  </div>\n</header>")
        elif t == 'search':
            parts.append("<div class=\"search-block\">\n  <form action=\"/search\" method=\"GET\">\n    <input type=\"text\" name=\"q\" placeholder=\"{{ t('search_posts') }}\">\n    <button type=\"submit\">{{ t('search') }}</button>\n  </form>\n</div>")
        elif t == 'index_text':
            parts.append("<div class=\"index-text\">\n  <h2>{{ active_text.name if active_text else 'Aktueller Text' }}</h2>\n  <p>{{ index_text|striptags|truncate(300, True, '...') }}</p>\n  {% if active_text_id %}<a href=\"/index-text/{{ active_text_id }}\">{{ t('read_more') }}</a>{% endif %}\n</div>")
        elif t == 'post_list':
            # Insert the canonical post-list jinja snippet
            parts.append('''{% if posts %}
                <div style="display: grid; gap: 2rem;">
                    {% for post in posts %}
                        <article class="card">
                            <div class="card-body">
                                <h2 style="margin-top: 0;">
                                    <a href="/post/{{ post.slug }}" style="color: var(--primary-color);">{{ post.title }}</a>
                                </h2>
                                <div class="text-muted" style="margin-bottom: 1rem; font-size: 0.95rem;">
                                    By <strong>{{ post.author }}</strong> on <time>{{ post.created_at[:10] if post.created_at else 'Unknown' }}</time>
                                </div>
                                {% if post.categories or post.tags %}
                                    <div style="margin-bottom: 1rem;">
                                        {% for category in post.categories %}
                                            <span style="display: inline-block; background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; margin-right: 0.5rem; margin-bottom: 0.5rem;">📁 {{ category }}</span>
                                        {% endfor %}
                                        {% for tag in post.tags %}
                                            <span style="display: inline-block; background: #9b59b6; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; margin-right: 0.5rem; margin-bottom: 0.5rem;"># {{ tag }}</span>
                                        {% endfor %}
                                    </div>
                                {% endif %}
                                <p style="color: var(--gray-700); line-height: 1.6;">{{ post.content[:250] }}{% if post.content|length > 250 %}...{% endif %}</p>
                                <a href="/post/{{ post.slug }}" class="btn btn-primary btn-sm">{{ t('read_full_article') }}</a>
                            </div>
                        </article>
                    {% endfor %}
                </div>
            {% else %}
                <div class="alert alert-info">
                    <strong>{{ t('no_posts') }}</strong>
                    {% if session.user %}
                        <a href="/admin/posts/create">{{ t('create_your_first_post') }}</a>
                    {% else %}
                        <a href="/login">{{ t('login') }}</a> to create your first post!
                    {% endif %}
                </div>
            {% endif %}
''')
        elif t == 'youtube':
            cid = data.get('channel_id', '{{ settings.youtube_channel_id }}')
            parts.append(f"<div id=\"youtube-videos-section\">\n  <h2>{{{{ t('latest_videos') }}}}</h2>\n  <div id=\"youtube-videos-container\">{{% raw %}}{{% endraw %}}</div>\n</div>")
        elif t == 'social_links':
            parts.append('''{% if settings.show_social_links %}
            <div style="margin-top: 1rem; display: flex; justify-content: center; gap: 1rem;">

                {% if settings.twitter_handle %}
                    <a href="https://twitter.com/{{ settings.twitter_handle }}" target="_blank">Twitter</a>
                {% endif %}

                {% if settings.facebook_page %}
                    <a href="{{ settings.facebook_page }}" target="_blank">Facebook</a>
                {% endif %}

            </div>
        {% endif %}
''')
        else:
            # Unknown block -> try to render raw HTML if provided
            parts.append(data.get('html', ''))

    # Join parts with newlines
    return '\n\n'.join(parts)
