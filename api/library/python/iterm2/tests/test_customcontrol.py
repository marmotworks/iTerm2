import pytest
import re
import iterm2.customcontrol


class TestCustomControlSequenceMonitor:
    def test_async_get_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.customcontrol.CustomControlSequenceMonitor.async_get)

    def test_class_exists(self):
        assert iterm2.customcontrol.CustomControlSequenceMonitor is not None

    def test_init_with_session(self):
        mon = iterm2.customcontrol.CustomControlSequenceMonitor(None, "secret", r"^test$", "session123")
        assert mon._CustomControlSequenceMonitor__identity == "secret"
        assert mon._CustomControlSequenceMonitor__regex == r"^test$"
        assert mon._CustomControlSequenceMonitor__session_id == "session123"

    def test_init_without_session(self):
        mon = iterm2.customcontrol.CustomControlSequenceMonitor(None, "secret", r"^test$")
        assert mon._CustomControlSequenceMonitor__session_id is None

    def test_init_stores_connection(self):
        conn = object()
        mon = iterm2.customcontrol.CustomControlSequenceMonitor(conn, "secret", r"^test$")
        assert mon._CustomControlSequenceMonitor__connection is conn
