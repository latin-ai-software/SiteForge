import os, sys, json
proj = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj not in sys.path: sys.path.insert(0, proj)
os.environ.setdefault('SITEFORGE_ALLOW_TESTS', 'true')
from app import create_app
app = create_app('testing')
with app.test_client() as c:
    dsl = {
        'blocks': [
            {'type': 'hero', 'data': {'title': 'Welcome', 'subtitle': 'Hello world'}},
            {'type': 'post_list', 'data': {}},
            {'type': 'social_links', 'data': {}}
        ]
    }
    r = c.post('/admin/editor/api/page/home', json=dsl)
    print('SAVE STATUS', r.status_code, r.get_json())
    # Now GET root
    r2 = c.get('/')
    print('ROOT STATUS', r2.status_code)
    content = r2.get_data(as_text=True)
    print(content[:500])
