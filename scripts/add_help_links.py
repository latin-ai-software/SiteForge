from pathlib import Path

root = Path('templates/admin')
files = [p for p in root.rglob('*.html') if p.name != 'help.html']
for path in files:
    text = path.read_text(encoding='utf-8')
    if 'url_for(\'admin_help\')' in text or 'href="/admin/help"' in text:
        continue
    old = '<a href="{{ url_for(\'theme_creator.index\') }}">Theme Creator</a>'
    old2 = '<a href="{{ url_for(\'theme_creator.index\') }}" class="active">Theme Creator</a>'
    if old in text:
        text = text.replace(old, '<a href="{{ url_for(\'admin_help\') }}">Hilfe</a>\n            ' + old)
        path.write_text(text, encoding='utf-8')
        print(f'Updated {path}')
    elif old2 in text:
        text = text.replace(old2, '<a href="{{ url_for(\'admin_help\') }}">Hilfe</a>\n            ' + old2)
        path.write_text(text, encoding='utf-8')
        print(f'Updated {path}')
