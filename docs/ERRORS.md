$ python -m pytest --cov=lib --cov-report=html --cov-report=term --cov-report=xml:htmlcov/cobertura.xml
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0
rootdir: /builds/latin-ai-software/latinmagazine
configfile: pytest.ini
plugins: cov-7.1.0
collected 147 items
tests/test_admin_settings.py FFFFFFFF                                    [  5%]
tests/test_app.py [Updater] Already up to date
..                                                     [  6%]
tests/test_cache_utils.py ...                                            [  8%]
tests/test_comment_manager.py ............                               [ 17%]
tests/test_encryption.py .                                               [ 17%]
tests/test_file_manager.py ......F.FF.....                               [ 27%]
tests/test_install_update.py ..                                          [ 29%]
tests/test_newsletter.py ..........FF.                                   [ 38%]
tests/test_post_manager.py ..........................                    [ 55%]
tests/test_ratelimiter.py ...                                            [ 57%]
tests/test_root.py .......FF.F..                                         [ 66%]
tests/test_secure_config.py ............                                 [ 74%]
tests/test_security_headers.py ......                                    [ 78%]
tests/test_setup.py ...FF.....F.F                                        [ 87%]
tests/test_user_manager.py .FFFF.                                        [ 91%]
tests/test_youtube_helper.py .....FF.FFF.                                [100%]
=================================== FAILURES ===================================
______________ TestAdminSettingsRoutes.test_admin_settings_index _______________
self = <tests.test_admin_settings.TestAdminSettingsRoutes object at 0x797811266420>
mock_render = <MagicMock name='render_template' id='133556558212096'>
mock_auth = <MagicMock name='auth' id='133556537560144'>
app = <Flask 'tests.test_admin_settings'>
    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.render_template')
    def test_admin_settings_index(self, mock_render, mock_auth, app):
        """Test admin_settings_index."""
        mock_auth.require_admin = lambda: None  # Mock decorator
    
        with app.app_context():
            # Create settings file
            settings_file = os.path.join(app.root_path, "data", "settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump({"site_title": "Test"}, f)
    
            from lib.routes.admin.manage.settings.index import admin_settings_index
>           admin_settings_index()
tests/test_admin_settings.py:50: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
lib/netdefense/auth/identitas_auth.py:336: in wrapper
    username = self.current_user()
               ^^^^^^^^^^^^^^^^^^^
lib/netdefense/auth/identitas_auth.py:230: in current_user
    username = session.get(self._session_user_key)
               ^^^^^^^^^^^
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
______________ TestAdminSettingsRoutes.test_save_settings_success ______________
self = <tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036dbe0>
mock_schedule = <MagicMock name='schedule_restart' id='133556537570416'>
mock_jsonify = <MagicMock name='jsonify' id='133556538253984'>
mock_security_logger = <MagicMock name='SecurityLogger' id='133556538257632'>
mock_input_validator = <MagicMock name='InputValidator' id='133556538261424'>
mock_validate_input = <MagicMock name='validate_input' id='133556538117824'>
mock_csrf = <MagicMock name='CSRFProtection' id='133556538121616'>
mock_rate_limiter = <MagicMock name='rate_limiter' id='133556562539584'>
mock_auth = <MagicMock name='auth' id='133556538129152'>
app = <Flask 'tests.test_admin_settings'>
    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.rate_limiter')
    @patch('lib.routes.admin.manage.settings.index.CSRFProtection')
    @patch('lib.routes.admin.manage.settings.index.validate_input')
    @patch('lib.routes.admin.manage.settings.index.InputValidator')
    @patch('lib.routes.admin.manage.settings.index.SecurityLogger')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    @patch('lib.routes.admin.manage.settings.index.schedule_restart')
    def test_save_settings_success(self, mock_schedule, mock_jsonify, mock_security_logger,
                                  mock_input_validator, mock_validate_input, mock_csrf,
                                  mock_rate_limiter, mock_auth, app):
        """Test save_settings with valid data."""
        mock_auth.require_admin = lambda: None
        mock_rate_limiter.is_rate_limited.return_value = False
        mock_csrf.validate_token.return_value = True
        mock_validate_input.return_value = "test"
        mock_input_validator.validate_email.return_value = True
        mock_jsonify.return_value = {"status": "success"}
    
        with app.app_context():
>           with patch('flask.request') as mock_request:
                 ^^^^^^^^^^^^^^^^^^^^^^
tests/test_admin_settings.py:73: 
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
________________ TestAdminSettingsRoutes.test_encryption_status ________________
self = <tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036dee0>
mock_jsonify = <MagicMock name='jsonify' id='133556539968304'>
mock_auth = <MagicMock name='auth' id='133556537722544'>
app = <Flask 'tests.test_admin_settings'>
client = <FlaskClient <Flask 'tests.test_admin_settings'>>
    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_encryption_status(self, mock_jsonify, mock_auth, app, client):
        """Test encryption_status route."""
        mock_auth.require_admin = lambda: None
        mock_jsonify.return_value = {"encryption_enabled": False}
    
>       response = client.get('/admin/settings/encryption/status')
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_admin_settings.py:101: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1162: in get
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
lib/netdefense/auth/identitas_auth.py:338: in wrapper
    return redirect(url_for("auth.login_page"))
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/helpers.py:239: in url_for
    return current_app.url_for(
/usr/local/lib/python3.12/site-packages/flask/app.py:1121: in url_for
    return self.handle_url_build_error(error, endpoint, values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1110: in url_for
    rv = url_adapter.build(  # type: ignore[union-attr]
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <werkzeug.routing.map.MapAdapter object at 0x79780dfd1910>
endpoint = 'auth.login_page', values = {}, method = None, force_external = False
append_unknown = True, url_scheme = None
    def build(
        self,
        endpoint: t.Any,
        values: t.Mapping[str, t.Any] | None = None,
        method: str | None = None,
        force_external: bool = False,
        append_unknown: bool = True,
        url_scheme: str | None = None,
    ) -> str:
        """Build a URL by filling in any variable slots in the endpoint's rule
        with the provided values.
    
        This produces relative URLs (path only, no host) by default, which is
        appropriate for most use cases. When using subdomain or host matching,
        the URL will be absolute if the endpoint is not on the same host as the
        current request. If you need an absolute URL no matter what, such as
        when adding a link to an email, pass ``force_external=True``.
    
        Characters that are not allowed directly in URLs will be percent-encoded
        using UTF-8.
    
        Additional values that don't match any rule parts are added to the query
        (``?key=value``) part of the URL.
    
        If a rule is not found, an :exc:`.BuildError` is raised. Converters may
        also raise exceptions when preparing a value.
    
        Unlike matching, building does not perform comprehensive validation of
        the values, it's assumed that they are trusted and correct. It's also
        possible to build a URL for one endpoint that will be matched by
        another, or will not match. This is very unlikely to happen or to matter
        in most applications, especially with testing. If you need a
        stronger guarantee, you can use a helper to verify that
        ``match(build(endpoint)) == endpoint``.
    
        :param endpoint: The endpoint for the rule to build.
        :param values: Values for the variable parts of the rule, which will be
            converted using the part's converter's
            :meth:`~.BaseConverter.to_url` method. Keys that don't match
            variable parts will be converted to a query string unless
            ``append_unknown`` is disabled.
        :param method: Further match the rule to build by this HTTP method, for
            when there are multiple rules for the same endpoint that vary based
            on method.
        :param force_external: Always produce an absolute URL, for external use.
            If ``scheme`` is not set, this produces a protocol-relative URL.
        :param append_unknown: Convert values that don't match any rule parts
            to a query string. Disable to ignore such values.
        :param url_scheme: Scheme to use for absolute URLs. Defaults to
            :attr:`url_scheme`.
    
        .. versionchanged:: 2.0
            Added the ``url_scheme`` parameter.
    
        .. versionadded:: 0.6
           Added the ``append_unknown`` parameter.
        """
        self.map.update()
    
        if values:
            if isinstance(values, MultiDict):
                values = {
                    k: (v[0] if len(v) == 1 else v)
                    for k, v in dict.items(values)
                    if len(v) != 0
                }
            else:  # plain dict
                values = {k: v for k, v in values.items() if v is not None}
        else:
            values = {}
    
        rv = self._partial_build(endpoint, values, method, append_unknown)
        if rv is None:
>           raise BuildError(endpoint, values, method, self)
E           werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'auth.login_page'. Did you mean 'admin_settings.flush_cache' instead?
/usr/local/lib/python3.12/site-packages/werkzeug/routing/map.py:901: BuildError
___________________ TestAdminSettingsRoutes.test_cache_flush ___________________
self = <tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036e1b0>
mock_jsonify = <MagicMock name='jsonify' id='133556532286560'>
mock_file_manager = <MagicMock name='file_manager' id='133556532290736'>
mock_auth = <MagicMock name='auth' id='133556532294720'>
app = <Flask 'tests.test_admin_settings'>
client = <FlaskClient <Flask 'tests.test_admin_settings'>>
    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.file_manager')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_cache_flush(self, mock_jsonify, mock_file_manager, mock_auth, app, client):
        """Test cache_flush route."""
        mock_auth.require_admin = lambda: None
        mock_file_manager.flush_cache.return_value = True
        mock_jsonify.return_value = {"status": "success"}
    
>       response = client.post('/admin/settings/cache/flush')
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_admin_settings.py:113: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1167: in post
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
lib/netdefense/auth/identitas_auth.py:338: in wrapper
    return redirect(url_for("auth.login_page"))
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/helpers.py:239: in url_for
    return current_app.url_for(
/usr/local/lib/python3.12/site-packages/flask/app.py:1121: in url_for
    return self.handle_url_build_error(error, endpoint, values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1110: in url_for
    rv = url_adapter.build(  # type: ignore[union-attr]
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <werkzeug.routing.map.MapAdapter object at 0x79780dcfd4c0>
endpoint = 'auth.login_page', values = {}, method = None, force_external = False
append_unknown = True, url_scheme = None
    def build(
        self,
        endpoint: t.Any,
        values: t.Mapping[str, t.Any] | None = None,
        method: str | None = None,
        force_external: bool = False,
        append_unknown: bool = True,
        url_scheme: str | None = None,
    ) -> str:
        """Build a URL by filling in any variable slots in the endpoint's rule
        with the provided values.
    
        This produces relative URLs (path only, no host) by default, which is
        appropriate for most use cases. When using subdomain or host matching,
        the URL will be absolute if the endpoint is not on the same host as the
        current request. If you need an absolute URL no matter what, such as
        when adding a link to an email, pass ``force_external=True``.
    
        Characters that are not allowed directly in URLs will be percent-encoded
        using UTF-8.
    
        Additional values that don't match any rule parts are added to the query
        (``?key=value``) part of the URL.
    
        If a rule is not found, an :exc:`.BuildError` is raised. Converters may
        also raise exceptions when preparing a value.
    
        Unlike matching, building does not perform comprehensive validation of
        the values, it's assumed that they are trusted and correct. It's also
        possible to build a URL for one endpoint that will be matched by
        another, or will not match. This is very unlikely to happen or to matter
        in most applications, especially with testing. If you need a
        stronger guarantee, you can use a helper to verify that
        ``match(build(endpoint)) == endpoint``.
    
        :param endpoint: The endpoint for the rule to build.
        :param values: Values for the variable parts of the rule, which will be
            converted using the part's converter's
            :meth:`~.BaseConverter.to_url` method. Keys that don't match
            variable parts will be converted to a query string unless
            ``append_unknown`` is disabled.
        :param method: Further match the rule to build by this HTTP method, for
            when there are multiple rules for the same endpoint that vary based
            on method.
        :param force_external: Always produce an absolute URL, for external use.
            If ``scheme`` is not set, this produces a protocol-relative URL.
        :param append_unknown: Convert values that don't match any rule parts
            to a query string. Disable to ignore such values.
        :param url_scheme: Scheme to use for absolute URLs. Defaults to
            :attr:`url_scheme`.
    
        .. versionchanged:: 2.0
            Added the ``url_scheme`` parameter.
    
        .. versionadded:: 0.6
           Added the ``append_unknown`` parameter.
        """
        self.map.update()
    
        if values:
            if isinstance(values, MultiDict):
                values = {
                    k: (v[0] if len(v) == 1 else v)
                    for k, v in dict.items(values)
                    if len(v) != 0
                }
            else:  # plain dict
                values = {k: v for k, v in values.items() if v is not None}
        else:
            values = {}
    
        rv = self._partial_build(endpoint, values, method, append_unknown)
        if rv is None:
>           raise BuildError(endpoint, values, method, self)
E           werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'auth.login_page'. Did you mean 'admin_settings.flush_cache' instead?
/usr/local/lib/python3.12/site-packages/werkzeug/routing/map.py:901: BuildError
___________________ TestAdminSettingsRoutes.test_cache_stats ___________________
args = (<tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036e4e0>,)
keywargs = {'app': <Flask 'tests.test_admin_settings'>, 'client': <FlaskClient <Flask 'tests.test_admin_settings'>>}
    @wraps(func)
    def patched(*args, **keywargs):
>       with self.decoration_helper(patched,
                                    args,
                                    keywargs) as (newargs, newkeywargs):
/usr/local/lib/python3.12/unittest/mock.py:1393: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/contextlib.py:137: in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:1375: in decoration_helper
    arg = exit_stack.enter_context(patching)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/contextlib.py:526: in enter_context
    result = _enter(cm)
             ^^^^^^^^^^
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
E           RuntimeError: Working outside of application context.
E           
E           This typically means that you attempted to use functionality that needed
E           the current application. To solve this, set up an application context
E           with app.app_context(). See the documentation for more information.
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:519: RuntimeError
__________________ TestAdminSettingsRoutes.test_update_check ___________________
args = (<tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036e7b0>,)
keywargs = {'app': <Flask 'tests.test_admin_settings'>, 'client': <FlaskClient <Flask 'tests.test_admin_settings'>>}
    @wraps(func)
    def patched(*args, **keywargs):
>       with self.decoration_helper(patched,
                                    args,
                                    keywargs) as (newargs, newkeywargs):
/usr/local/lib/python3.12/unittest/mock.py:1393: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/contextlib.py:137: in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:1375: in decoration_helper
    arg = exit_stack.enter_context(patching)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/contextlib.py:526: in enter_context
    result = _enter(cm)
             ^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <unittest.mock._patch object at 0x79781036d010>
    def get_original(self):
        target = self.getter()
        name = self.attribute
    
        original = DEFAULT
        local = False
    
        try:
            original = target.__dict__[name]
        except (AttributeError, KeyError):
            original = getattr(target, name, DEFAULT)
        else:
            local = True
    
        if name in _builtins and isinstance(target, ModuleType):
            self.create = True
    
        if not self.create and original is DEFAULT:
>           raise AttributeError(
                "%s does not have the attribute %r" % (target, name)
            )
E           AttributeError: <module 'lib.routes.admin.manage.settings.index' from '/builds/latin-ai-software/latinmagazine/lib/routes/admin/manage/settings/index.py'> does not have the attribute 'requests'
/usr/local/lib/python3.12/unittest/mock.py:1437: AttributeError
__________________ TestAdminSettingsRoutes.test_update_status __________________
self = <tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036ea80>
mock_jsonify = <MagicMock name='jsonify' id='133556537723408'>
mock_auth = <MagicMock name='auth' id='133556540105376'>
app = <Flask 'tests.test_admin_settings'>
client = <FlaskClient <Flask 'tests.test_admin_settings'>>
    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_update_status(self, mock_jsonify, mock_auth, app, client):
        """Test update_status route."""
        mock_auth.require_admin = lambda: None
        mock_jsonify.return_value = {"status": "idle"}
    
>       response = client.get('/admin/settings/update/status')
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_admin_settings.py:150: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1162: in get
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
lib/netdefense/auth/identitas_auth.py:338: in wrapper
    return redirect(url_for("auth.login_page"))
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/helpers.py:239: in url_for
    return current_app.url_for(
/usr/local/lib/python3.12/site-packages/flask/app.py:1121: in url_for
    return self.handle_url_build_error(error, endpoint, values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1110: in url_for
    rv = url_adapter.build(  # type: ignore[union-attr]
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <werkzeug.routing.map.MapAdapter object at 0x79780dcf6930>
endpoint = 'auth.login_page', values = {}, method = None, force_external = False
append_unknown = True, url_scheme = None
    def build(
        self,
        endpoint: t.Any,
        values: t.Mapping[str, t.Any] | None = None,
        method: str | None = None,
        force_external: bool = False,
        append_unknown: bool = True,
        url_scheme: str | None = None,
    ) -> str:
        """Build a URL by filling in any variable slots in the endpoint's rule
        with the provided values.
    
        This produces relative URLs (path only, no host) by default, which is
        appropriate for most use cases. When using subdomain or host matching,
        the URL will be absolute if the endpoint is not on the same host as the
        current request. If you need an absolute URL no matter what, such as
        when adding a link to an email, pass ``force_external=True``.
    
        Characters that are not allowed directly in URLs will be percent-encoded
        using UTF-8.
    
        Additional values that don't match any rule parts are added to the query
        (``?key=value``) part of the URL.
    
        If a rule is not found, an :exc:`.BuildError` is raised. Converters may
        also raise exceptions when preparing a value.
    
        Unlike matching, building does not perform comprehensive validation of
        the values, it's assumed that they are trusted and correct. It's also
        possible to build a URL for one endpoint that will be matched by
        another, or will not match. This is very unlikely to happen or to matter
        in most applications, especially with testing. If you need a
        stronger guarantee, you can use a helper to verify that
        ``match(build(endpoint)) == endpoint``.
    
        :param endpoint: The endpoint for the rule to build.
        :param values: Values for the variable parts of the rule, which will be
            converted using the part's converter's
            :meth:`~.BaseConverter.to_url` method. Keys that don't match
            variable parts will be converted to a query string unless
            ``append_unknown`` is disabled.
        :param method: Further match the rule to build by this HTTP method, for
            when there are multiple rules for the same endpoint that vary based
            on method.
        :param force_external: Always produce an absolute URL, for external use.
            If ``scheme`` is not set, this produces a protocol-relative URL.
        :param append_unknown: Convert values that don't match any rule parts
            to a query string. Disable to ignore such values.
        :param url_scheme: Scheme to use for absolute URLs. Defaults to
            :attr:`url_scheme`.
    
        .. versionchanged:: 2.0
            Added the ``url_scheme`` parameter.
    
        .. versionadded:: 0.6
           Added the ``append_unknown`` parameter.
        """
        self.map.update()
    
        if values:
            if isinstance(values, MultiDict):
                values = {
                    k: (v[0] if len(v) == 1 else v)
                    for k, v in dict.items(values)
                    if len(v) != 0
                }
            else:  # plain dict
                values = {k: v for k, v in values.items() if v is not None}
        else:
            values = {}
    
        rv = self._partial_build(endpoint, values, method, append_unknown)
        if rv is None:
>           raise BuildError(endpoint, values, method, self)
E           werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'auth.login_page'. Did you mean 'admin_settings.flush_cache' instead?
/usr/local/lib/python3.12/site-packages/werkzeug/routing/map.py:901: BuildError
_________________ TestAdminSettingsRoutes.test_update_install __________________
args = (<tests.test_admin_settings.TestAdminSettingsRoutes object at 0x79781036ec90>,)
keywargs = {'app': <Flask 'tests.test_admin_settings'>, 'client': <FlaskClient <Flask 'tests.test_admin_settings'>>}
    @wraps(func)
    def patched(*args, **keywargs):
>       with self.decoration_helper(patched,
                                    args,
                                    keywargs) as (newargs, newkeywargs):
/usr/local/lib/python3.12/unittest/mock.py:1393: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/contextlib.py:137: in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:1375: in decoration_helper
    arg = exit_stack.enter_context(patching)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/contextlib.py:526: in enter_context
    result = _enter(cm)
             ^^^^^^^^^^
/usr/local/lib/python3.12/unittest/mock.py:1467: in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <unittest.mock._patch object at 0x79781036d3a0>
    def get_original(self):
        target = self.getter()
        name = self.attribute
    
        original = DEFAULT
        local = False
    
        try:
            original = target.__dict__[name]
        except (AttributeError, KeyError):
            original = getattr(target, name, DEFAULT)
        else:
            local = True
    
        if name in _builtins and isinstance(target, ModuleType):
            self.create = True
    
        if not self.create and original is DEFAULT:
>           raise AttributeError(
                "%s does not have the attribute %r" % (target, name)
            )
E           AttributeError: <module 'lib.routes.admin.manage.settings.index' from '/builds/latin-ai-software/latinmagazine/lib/routes/admin/manage/settings/index.py'> does not have the attribute 'updater'
/usr/local/lib/python3.12/unittest/mock.py:1437: AttributeError
____________________ TestFileManager.test_save_file_success ____________________
self = <tests.test_file_manager.TestFileManager object at 0x79780e194b00>
mock_malware_checker = <MagicMock name='MalwareChecker' id='133556534194784'>
file_manager = <lib.data.file_manager.FileManager object at 0x79780dc73fe0>
    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_success(self, mock_malware_checker, file_manager):
        """Test save_file with successful upload."""
        mock_checker = MagicMock()
        mock_checker.scan_file.return_value = (True, "")
        mock_malware_checker.return_value = mock_checker
    
        # Create a mock file
        file_content = b"test file content"
        file = FileStorage(
            stream=BytesIO(file_content),
            filename="test.txt",
            content_type="text/plain"
        )
    
>       result = file_manager.save_file(file)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_file_manager.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <lib.data.file_manager.FileManager object at 0x79780dc73fe0>
file = <FileStorage: 'test.txt' ('text/plain')>, max_size_mb = 10
    def save_file(self, file, max_size_mb=10):
        """
        Save uploaded file with security checks
        Returns: (success, filename_or_error_message, file_info)
        """
        if not file or not file.filename:
            return False, "No file provided", None
    
        filename = secure_filename(file.filename)
    
        # Check file size (max 10MB by default)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
    
        if file_size > max_size_mb * 1024 * 1024:
            return False, f"File too large (max {max_size_mb}MB)", None
    
        # Check file extension
        if not self._is_allowed_file(filename):
            return False, "File type not allowed", None
    
        # Security scan - skip text scanning for binary media files
        file_content = file.read()
    
        # Malware scan
>       malware_ok, malware_message = self.security.scan_file(file_content)
                                      ^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'MalwareChecker' object has no attribute 'scan_file'
lib/data/file_manager.py:81: AttributeError
_______________ TestFileManager.test_save_file_malware_detected ________________
self = <tests.test_file_manager.TestFileManager object at 0x79780e197650>
mock_malware_checker = <MagicMock name='MalwareChecker' id='133556534353632'>
file_manager = <lib.data.file_manager.FileManager object at 0x79780dc9bad0>
    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_malware_detected(self, mock_malware_checker, file_manager):
        """Test save_file with malware detected."""
        mock_checker = MagicMock()
        mock_checker.scan_file.return_value = (False, "Malware detected")
        mock_malware_checker.return_value = mock_checker
    
        file = FileStorage(
            stream=BytesIO(b"malware content"),
            filename="malware.txt",
            content_type="text/plain"
        )
    
>       result = file_manager.save_file(file)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_file_manager.py:112: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
self = <lib.data.file_manager.FileManager object at 0x79780dc9bad0>
file = <FileStorage: 'malware.txt' ('text/plain')>, max_size_mb = 10
    def save_file(self, file, max_size_mb=10):
        """
        Save uploaded file with security checks
        Returns: (success, filename_or_error_message, file_info)
        """
        if not file or not file.filename:
            return False, "No file provided", None
    
        filename = secure_filename(file.filename)
    
        # Check file size (max 10MB by default)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
    
        if file_size > max_size_mb * 1024 * 1024:
            return False, f"File too large (max {max_size_mb}MB)", None
    
        # Check file extension
        if not self._is_allowed_file(filename):
            return False, "File type not allowed", None
    
        # Security scan - skip text scanning for binary media files
        file_content = file.read()
    
        # Malware scan
>       malware_ok, malware_message = self.security.scan_file(file_content)
                                      ^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'MalwareChecker' object has no attribute 'scan_file'
lib/data/file_manager.py:81: AttributeError
__________________ TestFileManager.test_save_file_not_allowed __________________
self = <tests.test_file_manager.TestFileManager object at 0x79780e197e00>
mock_malware_checker = <MagicMock name='MalwareChecker' id='133556534353920'>
file_manager = <lib.data.file_manager.FileManager object at 0x79780dc9b680>
    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_not_allowed(self, mock_malware_checker, file_manager):
        """Test save_file with not allowed file type."""
        mock_checker = MagicMock()
        mock_malware_checker.return_value = mock_checker
    
        file = FileStorage(
            stream=BytesIO(b"content"),
            filename="test.exe",
            content_type="application/x-msdownload"
        )
    
        result = file_manager.save_file(file)
>       assert "error" in result
E       AssertionError: assert 'error' in (False, 'File type not allowed', None)
tests/test_file_manager.py:129: AssertionError
_______________________ TestNewsletter.test_get_base_url _______________________
self = <tests.test_newsletter.TestNewsletter object at 0x79780e1f5df0>
app = <Flask 'tests.test_newsletter'>
    def test_get_base_url(self, app):
        """Test get_base_url."""
        with app.app_context():
            with app.test_request_context('/'):
                base_url = newsletter.get_base_url()
>               assert base_url == "http://localhost:5000"
E               AssertionError: assert 'http://localhost' == 'http://localhost:5000'
E                 
E                 - http://localhost:5000
E                 ?                 -----
E                 + http://localhost
tests/test_newsletter.py:120: AssertionError
_____________________ TestNewsletter.test_send_newsletter ______________________
self = <tests.test_newsletter.TestNewsletter object at 0x79780e1f6120>
mock_smtp = <MagicMock name='SMTP' id='133556534163024'>
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
                    "newsletter_sender_email": "sender@example.com"
                }, f)
    
            with app.test_request_context('/'):
                result = newsletter.send_newsletter("Subject", "<p>Body</p>", "Text body")
>               assert result is True
E               assert False is True
tests/test_newsletter.py:140: AssertionError
_________________ TestRootRoutes.test_newsletter_post_success __________________
self = <tests.test_root.TestRootRoutes object at 0x79780e25ba10>
mock_render = <MagicMock name='render_template' id='133556534778656'>
mock_subscribe = <MagicMock name='subscribe_email' id='133556534781344'>
app = <Flask 'tests.test_root'>
client = <FlaskClient <Flask 'tests.test_root'>>
    @patch('lib.routes.root.index.subscribe_email')
    @patch('lib.routes.root.index.render_template')
    def test_newsletter_post_success(self, mock_render, mock_subscribe, app, client):
        """Test newsletter POST route with success."""
        mock_subscribe.return_value = True
    
>       response = client.post('/newsletter', data={'email': 'test@example.com'})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_root.py:135: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1167: in post
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    @root_bp.route("/newsletter", methods=["GET", "POST"])
    def newsletter_signup():
        message = None
        success = False
        if request.method == "POST":
            email = request.form.get("email", "").strip()
>           ok, message = subscribe_email(email)
            ^^^^^^^^^^^
E           TypeError: cannot unpack non-iterable bool object
lib/routes/root/index.py:98: TypeError
______________ TestRootRoutes.test_newsletter_post_invalid_email _______________
self = <tests.test_root.TestRootRoutes object at 0x79780e2588f0>
mock_render = <MagicMock name='render_template' id='133556532295488'>
mock_subscribe = <MagicMock name='subscribe_email' id='133556532291120'>
app = <Flask 'tests.test_root'>
client = <FlaskClient <Flask 'tests.test_root'>>
    @patch('lib.routes.root.index.subscribe_email')
    @patch('lib.routes.root.index.render_template')
    def test_newsletter_post_invalid_email(self, mock_render, mock_subscribe, app, client):
        """Test newsletter POST route with invalid email."""
        mock_subscribe.return_value = False
    
>       response = client.post('/newsletter', data={'email': 'invalid-email'})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_root.py:144: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1167: in post
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    @root_bp.route("/newsletter", methods=["GET", "POST"])
    def newsletter_signup():
        message = None
        success = False
        if request.method == "POST":
            email = request.form.get("email", "").strip()
>           ok, message = subscribe_email(email)
            ^^^^^^^^^^^
E           TypeError: cannot unpack non-iterable bool object
lib/routes/root/index.py:98: TypeError
_________________ TestRootRoutes.test_index_text_comment_post __________________
self = <tests.test_root.TestRootRoutes object at 0x79780e25af90>
mock_render = <MagicMock name='render_template' id='133556538291840'>
mock_comment_manager = <MagicMock name='comment_manager' id='133556604619328'>
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
____________________ TestSetupFunctions.test_load_settings _____________________
self = <tests.test_setup.TestSetupFunctions object at 0x79780e25a720>
temp_dir = '/tmp/tmpdt_ulicx'
    def test_load_settings(self, temp_dir):
        """Test load_settings."""
        # Create settings file
        settings_file = get_settings_file(temp_dir)
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        test_settings = {"test": "value"}
        with open(settings_file, 'w') as f:
            json.dump(test_settings, f)
    
        settings = load_settings(temp_dir)
>       assert settings == test_settings
E       AssertionError: assert {'allow_passw...ays': 30, ...} == {'test': 'value'}
E         
E         Omitting 1 identical items, use -vv to show
E         Left contains 29 more items:
E         {'allow_password_change': False,
E          'allow_registration': True,
E          'allow_robot_indexing': False,
E          'analytics_period_days': 30,
E          'analytics_provider': 'builtin',
E          'analytics_tracking_id': '',
E          'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
E          'domain': 'http://localhost',
E          'embed_favicon_in_html': True,
E          'enable_analytics': False,
E          'enabled_plugins': {},
E          'facebook_page': '',
E          'header_background_enabled': False,
E          'imprint_enabled': False,
E          'newsletter_enabled': False,
E          'newsletter_sender_email': '',
E          'posts_per_page': 10,
E          'require_comment_approval': True,
E          'require_cookie_consent': True,
E          'robot_user_agents': '*',
E          'ses_smtp_host': '',
E          'ses_smtp_password': '',
E          'ses_smtp_port': 587,
E          'ses_smtp_username': '',
E          'setup_completed': False,
E          'show_social_links': False,
E          'site_description': 'Welcome to my site',
E          'site_title': 'My Awesome Site',
E          'twitter_handle': ''}
E         
E         Full diff:
E           {
E         +     'allow_password_change': False,
E         +     'allow_registration': True,
E         +     'allow_robot_indexing': False,
E         +     'analytics_period_days': 30,
E         +     'analytics_provider': 'builtin',
E         +     'analytics_tracking_id': '',
E         +     'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
E         +     'domain': 'http://localhost',
E         +     'embed_favicon_in_html': True,
E         +     'enable_analytics': False,
E         +     'enabled_plugins': {},
E         +     'facebook_page': '',
E         +     'header_background_enabled': False,
E         +     'imprint_enabled': False,
E         +     'newsletter_enabled': False,
E         +     'newsletter_sender_email': '',
E         +     'posts_per_page': 10,
E         +     'require_comment_approval': True,
E         +     'require_cookie_consent': True,
E         +     'robot_user_agents': '*',
E         +     'ses_smtp_host': '',
E         +     'ses_smtp_password': '',
E         +     'ses_smtp_port': 587,
E         +     'ses_smtp_username': '',
E         +     'setup_completed': False,
E         +     'show_social_links': False,
E         +     'site_description': 'Welcome to my site',
E         +     'site_title': 'My Awesome Site',
E               'test': 'value',
E         +     'twitter_handle': '',
E           }
tests/test_setup.py:70: AssertionError
________________ TestSetupFunctions.test_load_settings_no_file _________________
self = <tests.test_setup.TestSetupFunctions object at 0x79780e25ad20>
temp_dir = '/tmp/tmp1ibz12k8'
    def test_load_settings_no_file(self, temp_dir):
        """Test load_settings with no file."""
        settings = load_settings(temp_dir)
>       assert settings == {}
E       AssertionError: assert {'allow_passw...ays': 30, ...} == {}
E         
E         Left contains 29 more items:
E         {'allow_password_change': False,
E          'allow_registration': True,
E          'allow_robot_indexing': False,
E          'analytics_period_days': 30,
E          'analytics_provider': 'builtin',
E          'analytics_tracking_id': '',
E          'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
E          'domain': 'http://localhost',
E          'embed_favicon_in_html': True,
E          'enable_analytics': False,
E          'enabled_plugins': {},
E          'facebook_page': '',
E          'header_background_enabled': False,
E          'imprint_enabled': False,
E          'newsletter_enabled': False,
E          'newsletter_sender_email': '',
E          'posts_per_page': 10,
E          'require_comment_approval': True,
E          'require_cookie_consent': True,
E          'robot_user_agents': '*',
E          'ses_smtp_host': '',
E          'ses_smtp_password': '',
E          'ses_smtp_port': 587,
E          'ses_smtp_username': '',
E          'setup_completed': False,
E          'show_social_links': False,
E          'site_description': 'Welcome to my site',
E          'site_title': 'My Awesome Site',
E          'twitter_handle': ''}
E         
E         Full diff:
E         - {}
E         + {
E         +     'allow_password_change': False,
E         +     'allow_registration': True,
E         +     'allow_robot_indexing': False,
E         +     'analytics_period_days': 30,
E         +     'analytics_provider': 'builtin',
E         +     'analytics_tracking_id': '',
E         +     'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
E         +     'domain': 'http://localhost',
E         +     'embed_favicon_in_html': True,
E         +     'enable_analytics': False,
E         +     'enabled_plugins': {},
E         +     'facebook_page': '',
E         +     'header_background_enabled': False,
E         +     'imprint_enabled': False,
E         +     'newsletter_enabled': False,
E         +     'newsletter_sender_email': '',
E         +     'posts_per_page': 10,
E         +     'require_comment_approval': True,
E         +     'require_cookie_consent': True,
E         +     'robot_user_agents': '*',
E         +     'ses_smtp_host': '',
E         +     'ses_smtp_password': '',
E         +     'ses_smtp_port': 587,
E         +     'ses_smtp_username': '',
E         +     'setup_completed': False,
E         +     'show_social_links': False,
E         +     'site_description': 'Welcome to my site',
E         +     'site_title': 'My Awesome Site',
E         +     'twitter_handle': '',
E         + }
tests/test_setup.py:75: AssertionError
____________________ TestSetupRoutes.test_configure_success ____________________
self = <tests.test_setup.TestSetupRoutes object at 0x79780e214ce0>
mock_jsonify = <MagicMock name='jsonify' id='133556534197472'>
mock_get_settings_file = <MagicMock name='get_settings_file' id='133556604637152'>
mock_get_default = <MagicMock name='get_default_settings' id='133556575470080'>
mock_init_data = <MagicMock name='initialize_data_files' id='133556538289056'>
mock_auth_manager_class = <MagicMock name='IdentitasAuthManager' id='133556538285744'>
mock_is_completed = <MagicMock name='is_setup_completed' id='133556538283968'>
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
tests/test_setup.py:159: 
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
self = <tests.test_setup.TestSetupRoutes object at 0x79780e2146e0>
mock_jsonify = <MagicMock name='jsonify' id='133556532297120'>
mock_is_completed = <MagicMock name='is_setup_completed' id='133556540255328'>
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
tests/test_setup.py:191: 
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
self = <tests.test_user_manager.TestUserManager object at 0x79780e258830>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='133556604633984'>
user_manager = <lib.data.user_manager.UserManager object at 0x79780e059b20>
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
self = <tests.test_user_manager.TestUserManager object at 0x79780e214500>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='133556534348112'>
user_manager = <lib.data.user_manager.UserManager object at 0x79780dfa9670>
    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_update_user_role(self, mock_auth_class, user_manager):
        """Test update_user_role."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.update_user_role.return_value = True
    
        result = user_manager.update_user_role("testuser", "admin")
>       assert result is True
E       AssertionError: assert (False, 'User not found') is True
tests/test_user_manager.py:60: AssertionError
_________________ TestUserManager.test_update_user_git_access __________________
self = <tests.test_user_manager.TestUserManager object at 0x79780e214230>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='133556534120752'>
user_manager = <lib.data.user_manager.UserManager object at 0x79780dc61670>
    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_update_user_git_access(self, mock_auth_class, user_manager):
        """Test update_user_git_access."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.update_user_git_access.return_value = True
    
        result = user_manager.update_user_git_access("testuser", True)
>       assert result is True
E       AssertionError: assert (True, 'Git access updated') is True
tests/test_user_manager.py:71: AssertionError
_______________________ TestUserManager.test_delete_user _______________________
self = <tests.test_user_manager.TestUserManager object at 0x79780e217350>
mock_auth_class = <MagicMock name='IdentitasAuthManager' id='133556534153904'>
user_manager = <lib.data.user_manager.UserManager object at 0x79780dc68710>
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
____________ TestYouTubeHelper.test_extract_channel_id_user_format _____________
self = <tests.test_youtube_helper.TestYouTubeHelper object at 0x79780e2162d0>
    def test_extract_channel_id_user_format(self):
        """Test extract_channel_id with /user/ format."""
        url = "https://youtube.com/user/ChannelName"
        result = YouTubeHelper.extract_channel_id(url)
>       assert result == "ChannelName"
E       AssertionError: assert 'https://yout...r/ChannelName' == 'ChannelName'
E         
E         - ChannelName
E         + https://youtube.com/user/ChannelName
tests/test_youtube_helper.py:41: AssertionError
______________ TestYouTubeHelper.test_extract_channel_id_invalid _______________
self = <tests.test_youtube_helper.TestYouTubeHelper object at 0x79780e216690>
    def test_extract_channel_id_invalid(self):
        """Test extract_channel_id with invalid URL."""
        url = "https://example.com"
        result = YouTubeHelper.extract_channel_id(url)
>       assert result is None
E       AssertionError: assert 'https://example.com' is None
tests/test_youtube_helper.py:47: AssertionError
___________________ TestYouTubeHelper.test_get_latest_videos ___________________
self = <tests.test_youtube_helper.TestYouTubeHelper object at 0x79780e216cc0>
mock_get = <MagicMock name='get' id='133556534157072'>
    @patch('requests.get')
    def test_get_latest_videos(self, mock_get):
        """Test get_latest_videos."""
        # Mock XML response
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>yt:video:VIDEO_ID_1</id>
                <title>Video Title 1</title>
                <published>2023-01-01T00:00:00+00:00</published>
                <media:thumbnail url="http://example.com/thumb1.jpg"/>
            </entry>
            <entry>
                <id>yt:video:VIDEO_ID_2</id>
                <title>Video Title 2</title>
                <published>2023-01-02T00:00:00+00:00</published>
                <media:thumbnail url="http://example.com/thumb2.jpg"/>
            </entry>
        </feed>"""
        mock_get.return_value = mock_response
    
        helper = YouTubeHelper()
>       videos = helper.get_latest_videos("UC123", max_results=2)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_youtube_helper.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
lib/youtube_helper.py:140: in get_latest_videos
    current_app.logger.error(f"YouTube RSS error: {e}")
    ^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:318: in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    def _get_current_object() -> T:
        try:
            obj = local.get()
        except LookupError:
>           raise RuntimeError(unbound_message) from None
E           RuntimeError: Working outside of application context.
E           
E           This typically means that you attempted to use functionality that needed
E           the current application. To solve this, set up an application context
E           with app.app_context(). See the documentation for more information.
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:519: RuntimeError
________________ TestYouTubeHelper.test_get_latest_videos_error ________________
self = <tests.test_youtube_helper.TestYouTubeHelper object at 0x79780e217020>
mock_get = <MagicMock name='get' id='133556534120128'>
    @patch('requests.get')
    def test_get_latest_videos_error(self, mock_get):
        """Test get_latest_videos with request error."""
        mock_get.side_effect = Exception("Network error")
    
        helper = YouTubeHelper()
>       videos = helper.get_latest_videos("UC123")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_youtube_helper.py:88: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
lib/youtube_helper.py:140: in get_latest_videos
    current_app.logger.error(f"YouTube RSS error: {e}")
    ^^^^^^^^^^^^^^^^^^
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:318: in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    def _get_current_object() -> T:
        try:
            obj = local.get()
        except LookupError:
>           raise RuntimeError(unbound_message) from None
E           RuntimeError: Working outside of application context.
E           
E           This typically means that you attempted to use functionality that needed
E           the current application. To solve this, set up an application context
E           with app.app_context(). See the documentation for more information.
/usr/local/lib/python3.12/site-packages/werkzeug/local.py:519: RuntimeError
______________________ TestYouTubeHelper.test_format_date ______________________
self = <tests.test_youtube_helper.TestYouTubeHelper object at 0x79780e217380>
    def test_format_date(self):
        """Test format_date."""
        date_string = "2023-01-01T00:00:00+00:00"
        result = YouTubeHelper.format_date(date_string)
>       assert result == "2023-01-01"
E       AssertionError: assert '01. Jan 2023' == '2023-01-01'
E         
E         - 2023-01-01
E         + 01. Jan 2023
tests/test_youtube_helper.py:95: AssertionError
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
lib/data/file_manager.py                        90     28    69%
lib/data/media_manager.py                       95     69    27%
lib/data/post_manager.py                       254     79    69%
lib/data/settings.py                            11      7    36%
lib/data/user_manager.py                        68     11    84%
lib/netdefense/auth/identitas_auth.py          213    107    50%
lib/netdefense/check.py                         20     12    40%
lib/newsletter.py                              104     47    55%
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
lib/routes/root/index.py                       169     52    69%
lib/routes/setup/index.py                      120     50    58%
lib/security/__init__.py                         6      0   100%
lib/security/encrypted_files.py                 34     17    50%
lib/security/encryption.py                     154     74    52%
lib/security/headers.py                         70      4    94%
lib/security/ratelimiter.py                    114     30    74%
lib/security/secure_config.py                  121     13    89%
lib/theme_creator/generator.py                  18     12    33%
lib/youtube_helper.py                           82     37    55%
----------------------------------------------------------------
TOTAL                                         2996   1524    49%
Coverage HTML written to dir htmlcov
Coverage XML written to file htmlcov/cobertura.xml
=========================== short test summary info ============================
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_admin_settings_index - RuntimeError: Working outside of request context.
This typically means that you attempted to use functionality that needed
an active HTTP request. Consult the documentation on testing for
information about how to avoid this problem.
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_save_settings_success - RuntimeError: Working outside of request context.
This typically means that you attempted to use functionality that needed
an active HTTP request. Consult the documentation on testing for
information about how to avoid this problem.
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_encryption_status - werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'auth.login_page'. Did you mean 'admin_settings.flush_cache' instead?
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_cache_flush - werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'auth.login_page'. Did you mean 'admin_settings.flush_cache' instead?
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_cache_stats - RuntimeError: Working outside of application context.
This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_update_check - AttributeError: <module 'lib.routes.admin.manage.settings.index' from '/builds/latin-ai-software/latinmagazine/lib/routes/admin/manage/settings/index.py'> does not have the attribute 'requests'
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_update_status - werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'auth.login_page'. Did you mean 'admin_settings.flush_cache' instead?
FAILED tests/test_admin_settings.py::TestAdminSettingsRoutes::test_update_install - AttributeError: <module 'lib.routes.admin.manage.settings.index' from '/builds/latin-ai-software/latinmagazine/lib/routes/admin/manage/settings/index.py'> does not have the attribute 'updater'
FAILED tests/test_file_manager.py::TestFileManager::test_save_file_success - AttributeError: 'MalwareChecker' object has no attribute 'scan_file'
FAILED tests/test_file_manager.py::TestFileManager::test_save_file_malware_detected - AttributeError: 'MalwareChecker' object has no attribute 'scan_file'
FAILED tests/test_file_manager.py::TestFileManager::test_save_file_not_allowed - AssertionError: assert 'error' in (False, 'File type not allowed', None)
FAILED tests/test_newsletter.py::TestNewsletter::test_get_base_url - AssertionError: assert 'http://localhost' == 'http://localhost:5000'
  
  - http://localhost:5000
  ?                 -----
  + http://localhost
FAILED tests/test_newsletter.py::TestNewsletter::test_send_newsletter - assert False is True
FAILED tests/test_root.py::TestRootRoutes::test_newsletter_post_success - TypeError: cannot unpack non-iterable bool object
FAILED tests/test_root.py::TestRootRoutes::test_newsletter_post_invalid_email - TypeError: cannot unpack non-iterable bool object
FAILED tests/test_root.py::TestRootRoutes::test_index_text_comment_post - assert 401 == 302
 +  where 401 = <WrapperTestResponse streamed [401 UNAUTHORIZED]>.status_code
FAILED tests/test_setup.py::TestSetupFunctions::test_load_settings - AssertionError: assert {'allow_passw...ays': 30, ...} == {'test': 'value'}
  
  Omitting 1 identical items, use -vv to show
  Left contains 29 more items:
  {'allow_password_change': False,
   'allow_registration': True,
   'allow_robot_indexing': False,
   'analytics_period_days': 30,
   'analytics_provider': 'builtin',
   'analytics_tracking_id': '',
   'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
   'domain': 'http://localhost',
   'embed_favicon_in_html': True,
   'enable_analytics': False,
   'enabled_plugins': {},
   'facebook_page': '',
   'header_background_enabled': False,
   'imprint_enabled': False,
   'newsletter_enabled': False,
   'newsletter_sender_email': '',
   'posts_per_page': 10,
   'require_comment_approval': True,
   'require_cookie_consent': True,
   'robot_user_agents': '*',
   'ses_smtp_host': '',
   'ses_smtp_password': '',
   'ses_smtp_port': 587,
   'ses_smtp_username': '',
   'setup_completed': False,
   'show_social_links': False,
   'site_description': 'Welcome to my site',
   'site_title': 'My Awesome Site',
   'twitter_handle': ''}
  
  Full diff:
    {
  +     'allow_password_change': False,
  +     'allow_registration': True,
  +     'allow_robot_indexing': False,
  +     'analytics_period_days': 30,
  +     'analytics_provider': 'builtin',
  +     'analytics_tracking_id': '',
  +     'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
  +     'domain': 'http://localhost',
  +     'embed_favicon_in_html': True,
  +     'enable_analytics': False,
  +     'enabled_plugins': {},
  +     'facebook_page': '',
  +     'header_background_enabled': False,
  +     'imprint_enabled': False,
  +     'newsletter_enabled': False,
  +     'newsletter_sender_email': '',
  +     'posts_per_page': 10,
  +     'require_comment_approval': True,
  +     'require_cookie_consent': True,
  +     'robot_user_agents': '*',
  +     'ses_smtp_host': '',
  +     'ses_smtp_password': '',
  +     'ses_smtp_port': 587,
  +     'ses_smtp_username': '',
  +     'setup_completed': False,
  +     'show_social_links': False,
  +     'site_description': 'Welcome to my site',
  +     'site_title': 'My Awesome Site',
        'test': 'value',
  +     'twitter_handle': '',
    }
FAILED tests/test_setup.py::TestSetupFunctions::test_load_settings_no_file - AssertionError: assert {'allow_passw...ays': 30, ...} == {}
  
  Left contains 29 more items:
  {'allow_password_change': False,
   'allow_registration': True,
   'allow_robot_indexing': False,
   'analytics_period_days': 30,
   'analytics_provider': 'builtin',
   'analytics_tracking_id': '',
   'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
   'domain': 'http://localhost',
   'embed_favicon_in_html': True,
   'enable_analytics': False,
   'enabled_plugins': {},
   'facebook_page': '',
   'header_background_enabled': False,
   'imprint_enabled': False,
   'newsletter_enabled': False,
   'newsletter_sender_email': '',
   'posts_per_page': 10,
   'require_comment_approval': True,
   'require_cookie_consent': True,
   'robot_user_agents': '*',
   'ses_smtp_host': '',
   'ses_smtp_password': '',
   'ses_smtp_port': 587,
   'ses_smtp_username': '',
   'setup_completed': False,
   'show_social_links': False,
   'site_description': 'Welcome to my site',
   'site_title': 'My Awesome Site',
   'twitter_handle': ''}
  
  Full diff:
  - {}
  + {
  +     'allow_password_change': False,
  +     'allow_registration': True,
  +     'allow_robot_indexing': False,
  +     'analytics_period_days': 30,
  +     'analytics_provider': 'builtin',
  +     'analytics_tracking_id': '',
  +     'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
  +     'domain': 'http://localhost',
  +     'embed_favicon_in_html': True,
  +     'enable_analytics': False,
  +     'enabled_plugins': {},
  +     'facebook_page': '',
  +     'header_background_enabled': False,
  +     'imprint_enabled': False,
  +     'newsletter_enabled': False,
  +     'newsletter_sender_email': '',
  +     'posts_per_page': 10,
  +     'require_comment_approval': True,
  +     'require_cookie_consent': True,
  +     'robot_user_agents': '*',
  +     'ses_smtp_host': '',
  +     'ses_smtp_password': '',
  +     'ses_smtp_port': 587,
  +     'ses_smtp_username': '',
  +     'setup_completed': False,
  +     'show_social_links': False,
  +     'site_description': 'Welcome to my site',
  +     'site_title': 'My Awesome Site',
  +     'twitter_handle': '',
  + }
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
FAILED tests/test_user_manager.py::TestUserManager::test_update_user_role - AssertionError: assert (False, 'User not found') is True
FAILED tests/test_user_manager.py::TestUserManager::test_update_user_git_access - AssertionError: assert (True, 'Git access updated') is True
FAILED tests/test_user_manager.py::TestUserManager::test_delete_user - AssertionError: assert (False, 'User not found') is True
FAILED tests/test_youtube_helper.py::TestYouTubeHelper::test_extract_channel_id_user_format - AssertionError: assert 'https://yout...r/ChannelName' == 'ChannelName'
  
  - ChannelName
  + https://youtube.com/user/ChannelName
FAILED tests/test_youtube_helper.py::TestYouTubeHelper::test_extract_channel_id_invalid - AssertionError: assert 'https://example.com' is None
FAILED tests/test_youtube_helper.py::TestYouTubeHelper::test_get_latest_videos - RuntimeError: Working outside of application context.
This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.
FAILED tests/test_youtube_helper.py::TestYouTubeHelper::test_get_latest_videos_error - RuntimeError: Working outside of application context.
This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.
FAILED tests/test_youtube_helper.py::TestYouTubeHelper::test_format_date - AssertionError: assert '01. Jan 2023' == '2023-01-01'
  
  - 2023-01-01
  + 01. Jan 2023
================= 29 failed, 118 passed, 55 warnings in 20.31s =================