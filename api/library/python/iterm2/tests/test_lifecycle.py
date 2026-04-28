import pytest
import iterm2.lifecycle
import iterm2


class TestEachSessionOnceMonitor:
    def test_class_exists(self):
        assert iterm2.lifecycle.EachSessionOnceMonitor is not None

    def test_async_foreach_session_create_task_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(
            iterm2.lifecycle.EachSessionOnceMonitor.async_foreach_session_create_task)

    def test_async_get_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.lifecycle.EachSessionOnceMonitor.async_get)


class TestSessionTerminationMonitor:
    def test_class_exists(self):
        assert iterm2.lifecycle.SessionTerminationMonitor is not None

    def test_async_get_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.lifecycle.SessionTerminationMonitor.async_get)


class TestLayoutChangeMonitor:
    def test_class_exists(self):
        assert iterm2.lifecycle.LayoutChangeMonitor is not None

    def test_async_get_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.lifecycle.LayoutChangeMonitor.async_get)


class TestNewSessionMonitor:
    def test_class_exists(self):
        assert iterm2.lifecycle.NewSessionMonitor is not None

    def test_async_get_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.lifecycle.NewSessionMonitor.async_get)
