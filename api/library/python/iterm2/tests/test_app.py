import pytest
import iterm2.app
import iterm2.window
import iterm2


class TestCreateWindowExceptionAlias:
    def test_is_window_exception(self):
        assert iterm2.app.CreateWindowException is iterm2.window.CreateWindowException


class TestInvalidateApp:
    def test_sets_instance_to_none(self):
        iterm2.app.App.instance = object()
        iterm2.app.invalidate_app()
        assert iterm2.app.App.instance is None

    def test_idempotent(self):
        iterm2.app.App.instance = None
        iterm2.app.invalidate_app()
        assert iterm2.app.App.instance is None


class TestAppInstance:
    def test_default_is_none(self):
        iterm2.app.App.instance = None

    def test_async_get_app_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.app.async_get_app)

    def test_async_construct_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.app.App.async_construct)


class TestAppStaticMethods:
    def test_windows_from_list_sessions_response_exists(self):
        assert hasattr(iterm2.app.App, '_windows_from_list_sessions_response')
        assert callable(iterm2.app.App._windows_from_list_sessions_response)

    def test_buried_sessions_from_list_sessions_response_exists(self):
        assert hasattr(iterm2.app.App, '_buried_sessions_from_list_sessions_response')
        assert callable(iterm2.app.App._buried_sessions_from_list_sessions_response)
