import os, sys
sys.path.insert(0, os.path.abspath('.'))

from app import create_app

app = create_app()

with app.test_client() as client:
    # Test admin users route
    response = client.get('/admin/users')
    print(f'Admin users route status: {response.status_code}')

    # Test admin notifications route
    response = client.get('/admin/notifications/')
    print(f'Admin notifications route status: {response.status_code}')

    # Test with session
    with client.session_transaction() as sess:
        sess['user'] = 'admin'

    response = client.get('/admin/notifications/')
    print(f'Admin notifications with admin session: {response.status_code}')

    # Also test the context processor
    response = client.get('/admin/settings')
    print(f'Admin settings route status: {response.status_code}')