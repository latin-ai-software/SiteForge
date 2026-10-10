import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app

# Allow tests/dev runs to bypass remote license validation for local checks
os.environ.setdefault('SITEFORGE_ALLOW_TESTS', 'true')
app = create_app('testing')
with app.test_client() as c:
    r = c.get('/admin/editor/home')
    print('STATUS', r.status_code)
    print('CONTENT_SNIPPET:\n', r.get_data(as_text=True)[:800])
