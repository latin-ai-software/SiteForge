$ python -m pytest --cov=lib --cov-report=html --cov-report=term --cov-report=xml:htmlcov/cobertura.xml
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /builds/latin-ai-software/latinmagazine
configfile: pytest.ini
plugins: cov-7.1.0
collected 147 items
tests/test_admin_settings.py ssssssss                                    [  5%]
tests/test_app.py ..                                                     [  6%]
tests/test_cache_utils.py ...                                            [  8%]
tests/test_comment_manager.py ......Current version: 0.1.0, Latest version: 0.1.0
......                               [ 17%]
tests/test_encryption.py .                                               [ 17%]
tests/test_file_manager.py ...............                               [ 27%]
tests/test_install_update.py ..                                          [ 29%]
tests/test_newsletter.py ...........F.                                   [ 38%]
tests/test_post_manager.py ..........................                    [ 55%]
tests/test_ratelimiter.py ...                                            [ 57%]
tests/test_root.py ..........F..                                         [ 66%]
tests/test_secure_config.py ............                                 [ 74%]
tests/test_security_headers.py ......                                    [ 78%]
tests/test_setup.py ..........F.F                                        [ 87%]
tests/test_user_manager.py .FFFF.                                        [ 91%]
tests/test_youtube_helper.py ............                                [100%]
=================================== FAILURES ===================================
_____________________ TestNewsletter.test_send_newsletter ______________________
self = <tests.test_newsletter.TestNewsletter object at 0x73ff0e445b20>
mock_smtp = <MagicMock name='SMTP' id='127539273440272'>
app = <Flask 'tests.test_newsletter'>
    @patch('smtplib.SMTP')
    def test_send_newsletter(self, mock_smtp, app):
        """Test send_newsletter."""
        with app.app_context():
            # Mock settings
            settings_file = os.path.join(app.root_path, "data", "settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump({
                    "ses_smtp_server": "smtp.example.com",
                    "ses_smtp_port": 587,
                    "ses_smtp_username": "user",
                    "ses_smtp_password": "pass",
                    "newsletter_sender_email": "sender@example.com",
                    "newsletter_enabled": True
                }, f)
    
            with app.test_request_context('/'):
                result = newsletter.send_newsletter("Subject", "<p>Body</p>", "Text body")
>               assert result is True
E               assert False is True
tests/test_newsletter.py:141: AssertionError
_________________ TestRootRoutes.test_index_text_comment_post __________________
self = <tests.test_root.TestRootRoutes object at 0x73ff0e4a5d00>
mock_render = <MagicMock name='render_template' id='127539273408368'>
mock_comment_manager = <MagicMock name='comment_manager' id='127539291370224'>
app = <Flask 'tests.test_root'>
client = <FlaskClient <Flask 'tests.test_root'>>
    @patch('lib.routes.root.index.comment_manager')
    @patch('lib.routes.root.index.render_template')
    def test_index_text_comment_post(self, mock_render, mock_comment_manager, app, client):
        """Test index_text comment POST route."""
        mock_comment_manager.add_comment.return_value = "1"
    
        response = client.post('/index-text/1/comment', data={
            'author': 'Test Author',
            'content': 'Test comment'
        })
>       assert response.status_code == 302  # Redirect
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       assert 401 == 302
E        +  where 401 = <WrapperTestResponse streamed [401 UNAUTHORIZED]>.status_code
tests/test_root.py:166: AssertionError
____________________ TestSetupRoutes.test_configure_success ____________________
self = <tests.test_setup.TestSetupRoutes object at 0x73ff0e4a7a70>
mock_jsonify = <MagicMock name='jsonify' id='127538918805904'>
mock_get_settings_file = <MagicMock name='get_settings_file' id='127538918809504'>
mock_get_default = <MagicMock name='get_default_settings' id='127538918750256'>
mock_init_data = <MagicMock name='initialize_data_files' id='127538918745216'>
mock_auth_manager_class = <MagicMock name='IdentitasAuthManager' id='127538918742240'>
mock_is_completed = <MagicMock name='is_setup_completed' id='127538918738880'>
app = <Flask 'tests.test_setup'>
    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.IdentitasAuthManager')
    @patch('lib.routes.setup.index.initialize_data_files')
    @patch('lib.routes.setup.index.get_default_settings')
    @patch('lib.routes.setup.index.get_settings_file')
    @patch('lib.routes.setup.index.jsonify')
    def test_configure_success(self, mock_jsonify, mock_get_settings_file, mock_get_default, mock_init_data,
                              mock_auth_manager_class, mock_is_completed, app):
        """Test configure with valid data."""
        mock_is_completed.return_value = False
        mock_get_default.return_value = {"default": "settings"}
        mock_get_settings_file.return_value = "/tmp/settings.json"
        mock_auth = MagicMock()
        mock_auth.create_user.return_value = (True, "Success")
        mock_auth_manager_class.return_value = mock_auth
        mock_jsonify.return_value = {"success": True}
    
        with app.app_context():
>           with patch('flask.request') as mock_request:
                 ^^^^^^^^^^^^^^^^^^^^^^
tests/test_setup.py:161: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/unittest/mock.py:1494: in __enter__
    elif spec is None and _is_async_obj(original):
                          ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:56: in _is_async_obj
    if hasattr(obj, '__func__'):
       ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:318: in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    def _get_current_object() -> T:
        try:
            obj = local.get()
        except LookupError:
>           raise RuntimeError(unbound_message) from None
E           RuntimeError: Working outside of request context.
E           
E           This typically means that you attempted to use functionality that needed
E           an active HTTP request. Consult the documentation on testing for
E           information about how to avoid this problem.
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:519: RuntimeError
________________ TestSetupRoutes.test_configure_missing_fields _________________
self = <tests.test_setup.TestSetupRoutes object at 0x73ff0e35c1a0>
mock_jsonify = <MagicMock name='jsonify' id='127539273708224'>
mock_is_completed = <MagicMock name='is_setup_completed' id='127539273678480'>
app = <Flask 'tests.test_setup'>
    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.jsonify')
    def test_configure_missing_fields(self, mock_jsonify, mock_is_completed, app):
        """Test configure with missing required fields."""
        mock_is_completed.return_value = False
        mock_jsonify.return_value = {"success": False}
    
        with app.app_context():
>           with patch('flask.request') as mock_request:
                 ^^^^^^^^^^^^^^^^^^^^^^
tests/test_setup.py:193: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/unittest/mock.py:1494: in __enter__
    elif spec is None and _is_async_obj(original):
                          ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:56: in _is_async_obj
    if hasattr(obj, '__func__'):
       ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:318: in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    def _get_current_object() -> T:
        try:
            obj = local.get()
        except LookupError:
>           raise RuntimeError(unbound_message) from None
E           RuntimeError: Working outside of request context.
E           
E           This typically means that you attempted to use functionality that needed
E           an active HTTP request. Consult the documentation on testing for
E           information about how to avoid this problem.
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:519: RuntimeError
______________________ TestUserManager.test_get_all_users ______________________
self = <tests.test_user_manager.TestUserManager object at 0x73ff0e4a5a60>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='127539273704192'>
user_manager = <lib.data.user_manager.UserManager object at 0x73ff0d1a1070>
    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_get_all_users(self, mock_auth_class, user_manager):
        """Test get_all_users."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.engine = MagicMock()
        mock_auth._get_user_role.return_value = "user"
        mock_auth.has_git_access.return_value = True
    
        # Mock SQLAlchemy session and User model
        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.created_at = "2023-01-01"
        mock_session.query.return_value.all.return_value = [mock_user]
    
        with patch('sqlalchemy.orm.Session', return_value=mock_session):
            users = user_manager.get_all_users()
>           assert len(users) == 1
E           assert 0 == 1
E            +  where 0 = len([])
tests/test_user_manager.py:49: AssertionError
____________________ TestUserManager.test_update_user_role _____________________
self = <tests.test_user_manager.TestUserManager object at 0x73ff0e4a65d0>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='127539273413312'>
user_manager = <lib.data.user_manager.UserManager object at 0x73ff0d0c69c0>
    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_update_user_role(self, mock_auth_class, user_manager):
        """Test update_user_role."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.update_user_role.return_value = True
    
        result = user_manager.update_user_role("testuser", "admin")
>       assert result is True
E       assert False is True
tests/test_user_manager.py:60: AssertionError
_________________ TestUserManager.test_update_user_git_access __________________
self = <tests.test_user_manager.TestUserManager object at 0x73ff0e4a6780>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='127538918737104'>
user_manager = <lib.data.user_manager.UserManager object at 0x73fef7f27e90>
    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_update_user_git_access(self, mock_auth_class, user_manager):
        """Test update_user_git_access."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.update_user_git_access.return_value = True
    
        result = user_manager.update_user_git_access("testuser", True)
        assert result is True
>       mock_auth.update_user_git_access.assert_called_once_with("testuser", True)
tests/test_user_manager.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <MagicMock name='IdentitasAuthManager().update_user_git_access' id='127538918678336'>
args = ('testuser', True), kwargs = {}
msg = "Expected 'update_user_git_access' to be called once. Called 0 times."
    def assert_called_once_with(self, /, *args, **kwargs):
        """assert that the mock was called exactly once and that that call was
        with the specified arguments."""
        if not self.call_count == 1:
            msg = ("Expected '%s' to be called once. Called %s times.%s"
                   % (self._mock_name or 'mock',
                      self.call_count,
                      self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'update_user_git_access' to be called once. Called 0 times.
/usr/local/lib/python3.12/unittest/mock.py:960: AssertionError
_______________________ TestUserManager.test_delete_user _______________________
self = <tests.test_user_manager.TestUserManager object at 0x73ff0e35c2f0>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='127539291623584'>
user_manager = <lib.data.user_manager.UserManager object at 0x73ff0e2c07d0>
    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_delete_user(self, mock_auth_class, user_manager):
        """Test delete_user."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.delete_user.return_value = True
    
        result = user_manager.delete_user("testuser")
>       assert result is True
E       AssertionError: assert (False, 'User not found') is True
tests/test_user_manager.py:82: AssertionError
=============================== warnings summary ===============================
../../../usr/local/lib/python3.12/site-packages/sqlalchemy/sql/schema.py:3624: 8 warnings
tests/test_user_manager.py: 40 warnings
  /usr/local/lib/python3.12/site-packages/sqlalchemy/sql/schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
tests/test_encryption.py::test_encryption
  /usr/local/lib/python3.12/site-packages/_pytest/python.py:170: PytestReturnNotNoneWarning: Test functions should return None, but tests/test_encryption.py::test_encryption returned <class 'bool'>.
  Did you mean to use `assert` instead of `return`?
  See https://docs.pytest.org/en/stable/how-to/assert.html#return-not-none for more information.
    warnings.warn(
tests/test_secure_config.py::test_security_logger_methods
  /builds/latin-ai-software/latinmagazine/lib/security/secure_config.py:117: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    security_logger.warning(f"Failed login attempt: username={username}, ip={ip_address}, time={datetime.utcnow()}")
tests/test_secure_config.py::test_security_logger_methods
  /builds/latin-ai-software/latinmagazine/lib/security/secure_config.py:122: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    security_logger.warning(f"Rate limit exceeded: endpoint={endpoint}, ip={ip_address}, time={datetime.utcnow()}")
tests/test_secure_config.py::test_security_logger_methods
  /builds/latin-ai-software/latinmagazine/lib/security/secure_config.py:127: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    security_logger.warning(f"Unauthorized access: user={user}, endpoint={endpoint}, ip={ip_address}, time={datetime.utcnow()}")
tests/test_secure_config.py::test_security_logger_methods
  /builds/latin-ai-software/latinmagazine/lib/security/secure_config.py:132: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    security_logger.info(f"File upload: user={username}, file={filename}, size={size}, status={status}, time={datetime.utcnow()}")
tests/test_secure_config.py::test_security_logger_methods
  /builds/latin-ai-software/latinmagazine/lib/security/secure_config.py:137: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    security_logger.warning(f"Config changed: user={username}, setting={setting}, old={old_value}, new={new_value}, time={datetime.utcnow()}")
tests/test_secure_config.py::test_security_logger_methods
  /builds/latin-ai-software/latinmagazine/lib/security/secure_config.py:142: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    security_logger.warning(f"Privilege changed: user={username}, old_role={old_role}, new_role={new_role}, time={datetime.utcnow()}")
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.13-final-0 _______________
Name                                         Stmts   Miss  Cover
----------------------------------------------------------------
lib/cache_utils.py                              68     37    46%
lib/data/comment_manager.py                     78     11    86%
lib/data/file_manager.py                        89     13    85%
lib/data/media_manager.py                       95     69    27%
lib/data/post_manager.py                       254     79    69%
lib/data/settings.py                            11      7    36%
lib/data/user_manager.py                        68     11    84%
lib/netdefense/auth/identitas_auth.py          213    110    48%
lib/netdefense/check.py                         25      6    76%
lib/newsletter.py                              104     44    58%
lib/routes/admin/manage/analytics/index.py      75     52    31%
lib/routes/admin/manage/backup.py               67     47    30%
lib/routes/admin/manage/media/index.py          82     55    33%
lib/routes/admin/manage/posts/index.py         173    138    20%
lib/routes/admin/manage/settings/index.py      207    165    20%
lib/routes/admin/manage/templates/index.py     144    108    25%
lib/routes/admin/manage/theme_creator.py        59     47    20%
lib/routes/admin/manage/users/index.py          51     28    45%
lib/routes/create/post/index.py                125     92    26%
lib/routes/data/youtube.py                      26     18    31%
lib/routes/root/auth.py                         98     77    21%
lib/routes/root/index.py                       169     51    70%
lib/routes/setup/index.py                      120     50    58%
lib/security/__init__.py                         6      0   100%
lib/security/encrypted_files.py                 34     17    50%
lib/security/encryption.py                     154     74    52%
lib/security/headers.py                         70      4    94%
lib/security/ratelimiter.py                    114     30    74%
lib/security/secure_config.py                  121     13    89%
lib/theme_creator/generator.py                  18     12    33%
lib/youtube_helper.py                           88     12    86%
----------------------------------------------------------------
TOTAL                                         3006   1477    51%
Coverage HTML written to dir htmlcov
Coverage XML written to file htmlcov/cobertura.xml
=========================== short test summary info ============================
FAILED tests/test_newsletter.py::TestNewsletter::test_send_newsletter - assert False is True
FAILED tests/test_root.py::TestRootRoutes::test_index_text_comment_post - assert 401 == 302
 +  where 401 = <WrapperTestResponse streamed [401 UNAUTHORIZED]>.status_code
FAILED tests/test_setup.py::TestSetupRoutes::test_configure_success - RuntimeError: Working outside of request context.
This typically means that you attempted to use functionality that needed
an active HTTP request. Consult the documentation on testing for
information about how to avoid this problem.
FAILED tests/test_setup.py::TestSetupRoutes::test_configure_missing_fields - RuntimeError: Working outside of request context.
This typically means that you attempted to use functionality that needed
an active HTTP request. Consult the documentation on testing for
information about how to avoid this problem.
FAILED tests/test_user_manager.py::TestUserManager::test_get_all_users - assert 0 == 1
 +  where 0 = len([])
FAILED tests/test_user_manager.py::TestUserManager::test_update_user_role - assert False is True
FAILED tests/test_user_manager.py::TestUserManager::test_update_user_git_access - AssertionError: Expected 'update_user_git_access' to be called once. Called 0 times.
FAILED tests/test_user_manager.py::TestUserManager::test_delete_user - AssertionError: assert (False, 'User not found') is True
============ 8 failed, 131 passed, 8 skipped, 55 warnings in 13.31s ============