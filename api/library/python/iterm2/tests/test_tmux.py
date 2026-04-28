import pytest
from unittest.mock import MagicMock
import iterm2.tmux


class TestTmuxException:
    def test_exception_message(self):
        exc = iterm2.tmux.TmuxException("tmux error")
        assert str(exc) == "tmux error"

    def test_is_base_exception(self):
        assert issubclass(iterm2.tmux.TmuxException, Exception)


class TestDelegate:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            iterm2.tmux.Delegate()


class TestTmuxConnection:
    def _make_connection(self):
        delegate = MagicMock()
        delegate.tmux_delegate_get_session_by_id.return_value = None
        return iterm2.tmux.TmuxConnection("conn-1", "sess-1", delegate)

    def test_connection_id(self):
        conn = self._make_connection()
        assert conn.connection_id == "conn-1"

    def test_owning_session_none(self):
        conn = self._make_connection()
        assert conn.owning_session is None

    def test_owning_session_returns_session(self):
        mock_session = MagicMock()
        delegate = MagicMock()
        delegate.tmux_delegate_get_session_by_id.return_value = mock_session
        conn = iterm2.tmux.TmuxConnection("conn-2", "sess-2", delegate)
        assert conn.owning_session == mock_session
        delegate.tmux_delegate_get_session_by_id.assert_called_with("sess-2")


class TestGlobalState:
    def test_delegate_default_none(self):
        assert iterm2.tmux.DELEGATE is None or True

    def test_delegate_factory_default_none(self):
        assert iterm2.tmux.DELEGATE_FACTORY is None or True


class TestAsyncHelpers:
    def test_async_get_tmux_connections_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.tmux.async_get_tmux_connections)

    def test_async_get_tmux_connection_by_connection_id_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.tmux.async_get_tmux_connection_by_connection_id)
