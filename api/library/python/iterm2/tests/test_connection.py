import pytest
import iterm2.connection
import iterm2
import os


class TestGetenv:
    def test_existing_env_var(self):
        os.environ['TEST_ITERM2_VAR'] = 'test_value'
        try:
            result = iterm2.connection._getenv('TEST_ITERM2_VAR')
            assert result == 'test_value'
        finally:
            del os.environ['TEST_ITERM2_VAR']

    def test_missing_env_var(self):
        result = iterm2.connection._getenv('NONEXISTENT_ITERM2_VAR_12345')
        assert result is None


class TestCookieAndKey:
    def test_no_env_vars(self):
        saved_cookie = os.environ.pop('ITERM2_COOKIE', None)
        saved_key = os.environ.pop('ITERM2_KEY', None)
        try:
            cookie, key = iterm2.connection._cookie_and_key()
            assert cookie is None
            assert key is None
        finally:
            if saved_cookie is not None:
                os.environ['ITERM2_COOKIE'] = saved_cookie
            if saved_key is not None:
                os.environ['ITERM2_KEY'] = saved_key

    def test_with_env_vars(self):
        os.environ['ITERM2_COOKIE'] = 'mycookie'
        os.environ['ITERM2_KEY'] = 'mykey'
        try:
            cookie, key = iterm2.connection._cookie_and_key()
            assert cookie == 'mycookie'
            assert key == 'mykey'
        finally:
            del os.environ['ITERM2_COOKIE']
            del os.environ['ITERM2_KEY']


class TestUri:
    def test_returns_default_uri(self):
        uri = iterm2.connection._uri()
        assert uri == "ws://localhost:1912"


class TestSubprotocols:
    def test_returns_subprotocols(self):
        protos = iterm2.connection._subprotocols()
        assert protos == ['api.iterm2.com']


class TestHeaders:
    def test_has_required_headers(self):
        saved_cookie = os.environ.pop('ITERM2_COOKIE', None)
        saved_key = os.environ.pop('ITERM2_KEY', None)
        try:
            headers = iterm2.connection._headers()
            assert "origin" in headers
            assert headers["origin"] == "ws://localhost/"
            assert "x-iterm2-library-version" in headers
            assert "x-iterm2-disable-auth-ui" in headers
            assert headers["x-iterm2-disable-auth-ui"] == "true"
            assert "x-iterm2-advisory-name" in headers
        finally:
            if saved_cookie is not None:
                os.environ['ITERM2_COOKIE'] = saved_cookie
            if saved_key is not None:
                os.environ['ITERM2_KEY'] = saved_key

    def test_with_cookie(self):
        os.environ['ITERM2_COOKIE'] = 'testcookie'
        try:
            headers = iterm2.connection._headers()
            assert headers["x-iterm2-cookie"] == "testcookie"
        finally:
            del os.environ['ITERM2_COOKIE']

    def test_with_key(self):
        os.environ['ITERM2_KEY'] = 'testkey'
        try:
            headers = iterm2.connection._headers()
            assert headers["x-iterm2-key"] == "testkey"
        finally:
            del os.environ['ITERM2_KEY']


class TestDisconnectCallbacks:
    def test_add_disconnect_callback(self):
        callback_called = []

        def my_callback():
            callback_called.append(True)

        iterm2.connection.gDisconnectCallbacks.append(my_callback)
        try:
            assert my_callback in iterm2.connection.gDisconnectCallbacks
        finally:
            iterm2.connection.gDisconnectCallbacks.remove(my_callback)

    def test_add_disconnect_callback_helper(self):
        callback_called = []

        def my_callback():
            callback_called.append(True)

        iterm2.connection.add_disconnect_callback(my_callback)
        try:
            assert my_callback in iterm2.connection.gDisconnectCallbacks
        finally:
            iterm2.connection.gDisconnectCallbacks.remove(my_callback)


class TestConnectionHelpers:
    def test_helpers_is_list(self):
        assert isinstance(iterm2.connection.Connection.helpers, list)

    def test_register_helper(self):
        initial_len = len(iterm2.connection.Connection.helpers)

        async def my_helper(conn, msg):
            pass

        iterm2.connection.Connection.register_helper(my_helper)
        try:
            assert len(iterm2.connection.Connection.helpers) == initial_len + 1
            assert my_helper in iterm2.connection.Connection.helpers
        finally:
            iterm2.connection.Connection.helpers.remove(my_helper)


class TestRemoveAuth:
    def test_removes_cookie_and_key(self):
        conn = iterm2.connection.Connection()
        os.environ['ITERM2_COOKIE'] = 'cookie123'
        os.environ['ITERM2_KEY'] = 'key123'
        conn._remove_auth()
        assert 'ITERM2_COOKIE' not in os.environ
        assert 'ITERM2_KEY' not in os.environ

    def test_safe_when_env_vars_missing(self):
        saved_cookie = os.environ.pop('ITERM2_COOKIE', None)
        saved_key = os.environ.pop('ITERM2_KEY', None)
        try:
            conn = iterm2.connection.Connection()
            conn._remove_auth()
        finally:
            if saved_cookie is not None:
                os.environ['ITERM2_COOKIE'] = saved_cookie
            if saved_key is not None:
                os.environ['ITERM2_KEY'] = saved_key

    def test_only_removes_set_vars(self):
        conn = iterm2.connection.Connection()
        os.environ['ITERM2_COOKIE'] = 'cookie123'
        saved_key = os.environ.pop('ITERM2_KEY', None)
        try:
            conn._remove_auth()
            assert 'ITERM2_COOKIE' not in os.environ
        finally:
            if saved_key is not None:
                os.environ['ITERM2_KEY'] = saved_key


class TestUnixDomainSocketPath:
    def test_default_path(self):
        saved = os.environ.pop('IT2_SUITE', None)
        try:
            conn = iterm2.connection.Connection()
            path = conn._unix_domain_socket_path()
            assert 'iTerm2' in path
            assert path.endswith('private/socket')
        finally:
            if saved is not None:
                os.environ['IT2_SUITE'] = saved

    def test_custom_suite(self):
        os.environ['IT2_SUITE'] = 'CustomApp'
        try:
            conn = iterm2.connection.Connection()
            path = conn._unix_domain_socket_path()
            assert 'CustomApp' in path
            assert path.endswith('private/socket')
        finally:
            del os.environ['IT2_SUITE']


class TestConnectionInit:
    def test_initial_state(self):
        conn = iterm2.connection.Connection()
        assert conn.websocket is None
        assert conn.loop is None
