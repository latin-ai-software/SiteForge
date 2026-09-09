import io
import json
import os
import pytest
from unittest.mock import patch
from flask import Flask
from werkzeug.datastructures import FileStorage
from lib.routes.admin.manage.posts.index import admin_posts_bp
from lib.routes.create.post.index import post_create_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.register_blueprint(admin_posts_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_session(client):
    with client.session_transaction() as sess:
        sess['user'] = 'testuser'
    return client


@pytest.fixture
def auth_patches():
    with patch('lib.routes.admin.manage.posts.index.auth.current_user', return_value='testuser'), \
         patch('lib.routes.admin.manage.posts.index.auth.get_user_role', return_value='author'):
        yield


@patch('lib.routes.admin.manage.posts.index.render_template')
def test_create_post_form(mock_render, auth_session, auth_patches):
    mock_render.return_value = 'rendered'
    response = auth_session.get('/admin/posts/create')
    assert response.status_code == 200
    mock_render.assert_called_once_with(
        'admin/posts/create.html',
        git_plugin_available=False,
        git_repos=[],
        user='testuser',
        editor_mode='gutenberg'
    )


def test_create_form_has_document_metadata_controls():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app = Flask(__name__, template_folder=os.path.join(project_root, 'templates'))
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.jinja_env.globals['t'] = lambda key, *args, **kwargs: key
    app.register_blueprint(admin_posts_bp)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user'] = 'testuser'
        with patch('lib.routes.admin.manage.posts.index.auth.current_user', return_value='testuser'), \
             patch('lib.routes.admin.manage.posts.index.auth.get_user_role', return_value='author'):
            response = client.get('/admin/posts/create')

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    form_start = html.index('<form id="post-form"')
    form_end = html.index('</form>', form_start)
    form_html = html[form_start:form_end]

    assert 'Document' in form_html
    assert 'name="categories"' in form_html
    assert 'name="tags"' in form_html
    assert 'name="featured_image"' in form_html
    assert 'name="status"' in form_html
    assert 'name="allow_comments"' in form_html


@patch('lib.routes.admin.manage.posts.index.send_newsletter')
@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_create_post_success(mock_post_manager, mock_send_newsletter, auth_session, auth_patches):
    mock_post_manager.create_post.return_value = 'test-post-id'
    response = auth_session.post(
        '/admin/posts/create',
        data={
            'title': 'Test Post',
            'content': 'Test content',
            'categories': 'cat1, cat2',
            'tags': 'tag1, tag2',
            'status': 'draft',
            'allow_comments': 'off',
            'featured_image': 'https://example.com/feature.jpg'
        }
    )
    assert response.status_code == 302
    mock_post_manager.create_post.assert_called_once()
    kwargs = mock_post_manager.create_post.call_args.kwargs
    assert kwargs['status'] == 'draft'
    assert kwargs['allow_comments'] is False
    assert kwargs['featured_image'] == 'https://example.com/feature.jpg'
    mock_send_newsletter.assert_called_once()


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_create_post_missing_title(mock_post_manager, auth_session, auth_patches):
    response = auth_session.post('/admin/posts/create', data={'content': 'Test content'})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'title und content erforderlich'


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_create_post_missing_content(mock_post_manager, auth_session, auth_patches):
    response = auth_session.post('/admin/posts/create', data={'title': 'Test Post'})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'title und content erforderlich'


@patch('lib.routes.admin.manage.posts.index.file_manager')
@patch('lib.routes.admin.manage.posts.index.post_manager')
@patch('lib.routes.admin.manage.posts.index.send_newsletter')
def test_create_post_with_attachments(mock_send_newsletter, mock_post_manager, mock_file_manager, auth_session, auth_patches):
    mock_post_manager.create_post.return_value = 'test-post-id'
    mock_file_manager.save_file.return_value = (True, 'success', {
        'original_name': 'test.txt',
        'filename': 'saved_test.txt',
        'size': 100,
        'mime_type': 'text/plain'
    })

    data = {
        'title': 'Test Post',
        'content': 'Test content',
        'attachments': (io.BytesIO(b'test content'), 'test.txt')
    }

    response = auth_session.post('/admin/posts/create', data=data, content_type='multipart/form-data')
    assert response.status_code == 302
    mock_file_manager.save_file.assert_called()
    mock_post_manager.create_post.assert_called_once()


@patch('lib.routes.admin.manage.posts.index.media_manager')
@patch('lib.routes.admin.manage.posts.index.post_manager')
@patch('lib.routes.admin.manage.posts.index.send_newsletter')
def test_create_post_with_existing_files(mock_send_newsletter, mock_post_manager, mock_media_manager, auth_session, auth_patches):
    mock_post_manager.create_post.return_value = 'test-post-id'
    mock_media_manager.get_file_info.return_value = {'size': 200}

    response = auth_session.post(
        '/admin/posts/create',
        data={
            'title': 'Test Post',
            'content': 'Test content',
            'existing_files': ['existing_file.txt']
        }
    )
    assert response.status_code == 302
    mock_media_manager.get_file_info.assert_called_with('existing_file.txt')
    mock_post_manager.create_post.assert_called_once()


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_create_post_with_survey(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.create_post.return_value = 'test-post-id'
    response = auth_session.post(
        '/admin/posts/create',
        data={
            'title': 'Test Post',
            'content': 'Test content',
            'survey_enabled': 'on',
            'survey_question': 'What is your favorite?',
            'survey_options': 'Option A\nOption B'
        }
    )
    assert response.status_code == 302
    mock_post_manager.create_post.assert_called_once()


@patch('lib.routes.admin.manage.posts.index.post_manager')
@patch('lib.routes.admin.manage.posts.index.render_template')
def test_admin_posts_index(mock_render, mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_posts.return_value = [{'id': '1', 'title': 'Test Post'}]
    mock_render.return_value = 'rendered'

    response = auth_session.get('/admin/posts/')
    assert response.status_code == 200
    mock_render.assert_called_once_with('admin/posts/index.html', posts=[{'id': '1', 'title': 'Test Post'}])


@patch('lib.routes.admin.manage.posts.index.post_manager')
@patch('lib.routes.admin.manage.posts.index.render_template')
def test_edit_post_get(mock_render, mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'title': 'Test Post', 'author': 'testuser'}
    mock_render.return_value = 'rendered'

    response = auth_session.get('/admin/posts/edit/1')
    assert response.status_code == 200
    mock_render.assert_called_once_with(
        'admin/posts/edit.html',
        post={'id': '1', 'title': 'Test Post', 'author': 'testuser'},
        editor_mode='gutenberg'
    )


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_edit_post_not_found(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = None

    response = auth_session.get('/admin/posts/edit/nonexistent')
    assert response.status_code == 404


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_edit_post_permission_denied(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'title': 'Test Post', 'author': 'otheruser'}
    with patch('lib.routes.admin.manage.posts.index.auth.get_user_role', return_value='author'):
        response = auth_session.get('/admin/posts/edit/1')
    assert response.status_code == 403


@patch('lib.routes.admin.manage.posts.index.post_manager')
@patch('lib.routes.admin.manage.posts.index.send_newsletter')
def test_save_post_success(mock_send_newsletter, mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'title': 'Old Title', 'author': 'testuser', 'attachments': []}
    mock_post_manager.update_post.return_value = True

    response = auth_session.post(
        '/admin/posts/edit/1',
        data={
            'title': 'Updated Title',
            'content': 'Updated content',
            'categories': 'cat1',
            'tags': 'tag1',
            'status': 'draft',
            'allow_comments': 'on',
            'featured_image': 'https://example.com/edit-feature.jpg'
        }
    )
    assert response.status_code == 302
    mock_post_manager.update_post.assert_called_once()
    kwargs = mock_post_manager.update_post.call_args.kwargs
    assert kwargs['status'] == 'draft'
    assert kwargs['allow_comments'] is True
    assert kwargs['featured_image'] == 'https://example.com/edit-feature.jpg'

@patch('lib.routes.create.post.index.auth.current_user', return_value=None)
@patch('lib.routes.create.post.index.post_manager.get_post')
def test_draft_post_is_not_public_for_anon(mock_get_post, mock_current_user):
    mock_get_post.return_value = {
        'id': 'draft-id',
        'title': 'Draft',
        'status': 'draft',
        'author': 'testuser',
        'categories': [],
        'tags': [],
        'attachments': [],
        'survey': None,
        'allow_comments': True,
    }

    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(post_create_bp)
    with app.test_client() as client:
        response = client.get('/post/draft-id')
        assert response.status_code == 404


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_save_post_missing_title(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'author': 'testuser'}

    response = auth_session.post('/admin/posts/edit/1', data={'content': 'Updated content'})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'title und content erforderlich'


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_save_post_not_found(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = None

    response = auth_session.post('/admin/posts/edit/1', data={'title': 'Title', 'content': 'Content'})
    assert response.status_code == 404


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_save_post_permission_denied(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'author': 'otheruser'}
    with patch('lib.routes.admin.manage.posts.index.auth.get_user_role', return_value='author'):
        response = auth_session.post('/admin/posts/edit/1', data={'title': 'Title', 'content': 'Content'})
    assert response.status_code == 403


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_delete_post_success(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'author': 'testuser'}
    mock_post_manager.delete_post.return_value = True

    response = auth_session.post('/admin/posts/delete/1')
    assert response.status_code == 302


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_delete_post_not_found(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = None

    response = auth_session.post('/admin/posts/delete/1')
    assert response.status_code == 404


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_delete_post_permission_denied(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'author': 'otheruser'}
    with patch('lib.routes.admin.manage.posts.index.auth.get_user_role', return_value='author'):
        response = auth_session.post('/admin/posts/delete/1')
    assert response.status_code == 403


@patch('lib.routes.admin.manage.posts.index.post_manager')
def test_delete_post_failure(mock_post_manager, auth_session, auth_patches):
    mock_post_manager.get_post.return_value = {'id': '1', 'author': 'testuser'}
    mock_post_manager.delete_post.return_value = False

    response = auth_session.post('/admin/posts/delete/1')


def test_public_post_page_renders(tmp_path):
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.root_path = str(tmp_path)
    app.jinja_env.globals['t'] = lambda key, **kwargs: key
    app.register_blueprint(post_create_bp)

    data_dir = tmp_path / 'data'
    data_dir.mkdir(exist_ok=True)
    (data_dir / 'settings.json').write_text(json.dumps({'site_title': 'Test Site'}), encoding='utf-8')

    post_payload = {
        'id': 'p1',
        'title': 'Test post',
        'author': 'testuser',
        'created_at': '2024-01-01',
        'status': 'publish',
        'categories': ['news'],
        'tags': ['tag1'],
        'content': '<h2>Intro</h2><p>Hello world</p>',
        'attachments': [],
        'survey': None,
        'allow_comments': True,
    }

    with patch('lib.routes.create.post.index.post_manager.get_post', return_value=post_payload), \
         patch('lib.routes.create.post.index.comment_manager.get_comments', return_value=([], {})):
        with app.test_client() as client:
            response = client.get('/post/test-post')
            assert response.status_code == 200
            assert b'Test post' in response.data
            assert b'Hello world' in response.data


@patch('lib.routes.admin.manage.posts.index.file_manager')
def test_upload_post_media_success(mock_file_manager, auth_session, auth_patches):
    mock_file_manager.save_file.return_value = (True, 'success', {'filename': 'uploaded_file.txt'})
    mock_file_manager.get_file_url.return_value = '/uploads/uploaded_file.txt'

    data = {'file': (io.BytesIO(b'test file content'), 'test.txt')}
    response = auth_session.post('/admin/posts/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'
    assert response.get_json()['filename'] == 'uploaded_file.txt'


def test_upload_post_media_no_file(auth_session, auth_patches):
    response = auth_session.post('/admin/posts/upload', data={})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Keine Datei erhalten'


def test_upload_post_media_empty_filename(auth_session, auth_patches):
    data = {'file': (io.BytesIO(b'content'), '')}
    response = auth_session.post('/admin/posts/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Ungültiger Dateiname'


@patch('lib.routes.admin.manage.posts.index.file_manager')
def test_upload_post_media_save_failure(mock_file_manager, auth_session, auth_patches):
    mock_file_manager.save_file.return_value = (False, 'Upload failed', None)
    data = {'file': (io.BytesIO(b'content'), 'test.txt')}
    response = auth_session.post('/admin/posts/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Upload failed'
