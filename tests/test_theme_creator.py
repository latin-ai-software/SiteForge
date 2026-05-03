import os
import pytest
from unittest.mock import patch
from flask import Flask
from lib.routes.admin.manage.theme_creator import theme_creator_bp


@pytest.fixture
def app(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.secret_key = 'test-secret-key'
    app.register_blueprint(theme_creator_bp)

    theme_dir = tmp_path / 'static'
    theme_dir.mkdir()
    monkeypatch.setattr('lib.routes.admin.manage.theme_creator.THEME_DIR', str(theme_dir))
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@patch('lib.routes.admin.manage.theme_creator.render_template')
def test_index_route(mock_render, client, app, tmp_path):
    theme_dir = tmp_path / 'static'
    (theme_dir / 'theme1.css').write_text('body { color: red; }')
    mock_render.return_value = 'rendered'

    response = client.get('/admin/manage/theme-creator/')
    assert response.status_code == 200
    mock_render.assert_called_once_with('admin/theme_creator/index.html', themes=['theme1.css'])


@patch('lib.routes.admin.manage.theme_creator.render_template')
def test_new_get_route(mock_render, client):
    mock_render.return_value = 'rendered'

    response = client.get('/admin/manage/theme-creator/new')
    assert response.status_code == 200
    mock_render.assert_called_once()


@patch('lib.routes.admin.manage.theme_creator.generate_theme_file')
def test_new_post_no_name(mock_generate, client):
    response = client.post('/admin/manage/theme-creator/new', data={})
    assert response.status_code == 302


@patch('lib.routes.admin.manage.theme_creator.generate_theme_file')
def test_new_post_existing_theme(mock_generate, client, app):
    theme_dir = app.config.get('THEME_DIR') if 'THEME_DIR' in app.config else None
    # The monkeypatched constant is set in module, but we can use the actual path from the blueprint fixture.
    theme_dir = os.path.join(app.root_path, '..') if theme_dir is None else theme_dir
    # Instead use the global module constant directly if needed
    from lib.routes.admin.manage.theme_creator import THEME_DIR
    existing_path = os.path.join(THEME_DIR, 'existing.css')
    with open(existing_path, 'w', encoding='utf-8') as f:
        f.write('body { }')

    response = client.post('/admin/manage/theme-creator/new', data={'name': 'existing.css'})
    assert response.status_code == 302
    mock_generate.assert_not_called()


@patch('lib.routes.admin.manage.theme_creator.generate_theme_file')
def test_new_post_success(mock_generate, client):
    response = client.post('/admin/manage/theme-creator/new', data={'name': 'newtheme'})
    assert response.status_code == 302
    mock_generate.assert_called_once()


@patch('lib.routes.admin.manage.theme_creator.generate_theme_file')
def test_edit_theme_not_found(mock_generate, client):
    response = client.get('/admin/manage/theme-creator/edit/nonexistent.css')
    assert response.status_code == 302
    mock_generate.assert_not_called()


@patch('lib.routes.admin.manage.theme_creator.render_template')
def test_edit_get_success(mock_render, client):
    from lib.routes.admin.manage.theme_creator import THEME_DIR
    path = os.path.join(THEME_DIR, 'test.css')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(':root { --color: red; --color: red; }')

    mock_render.return_value = 'rendered'
    response = client.get('/admin/manage/theme-creator/edit/test.css')
    assert response.status_code == 200
    assert mock_render.called


@patch('lib.routes.admin.manage.theme_creator.generate_theme_file')
def test_edit_post_success(mock_generate, client):
    from lib.routes.admin.manage.theme_creator import THEME_DIR
    path = os.path.join(THEME_DIR, 'test.css')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(':root { --color: red; }')

    response = client.post('/admin/manage/theme-creator/edit/test.css', data={'color': 'blue'})
    assert response.status_code == 302
    mock_generate.assert_called_once()