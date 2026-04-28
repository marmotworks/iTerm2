"""Extended tests for iterm2.window.Window class."""
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, PropertyMock

import pytest
import iterm2
import iterm2.window
import iterm2.tab
import iterm2.session
import iterm2.util
import iterm2.api_pb2


class TestWindowInit:
    """Tests for Window.__init__."""

    def test_init_basic(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        tabs = []
        w = iterm2.window.Window(conn, "w1", tabs, frame, 1)
        assert w.window_id == "w1"
        assert w.window_number == 1
        assert w.tabs == []
        assert w.frame is frame
        assert w.selected_tab_id is None

    def test_init_with_tabs(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        tab = Mock(spec=iterm2.tab.Tab)
        tab.tab_id = "t1"
        w = iterm2.window.Window(conn, "w2", [tab], frame, 5)
        assert len(w.tabs) == 1
        assert w.tabs[0].tab_id == "t1"

    def test_init_selected_tab_id_none_by_default(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        w = iterm2.window.Window(conn, "w3", [], frame, 1)
        assert w.selected_tab_id is None

    def test_init_stores_connection(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        w = iterm2.window.Window(conn, "w4", [], frame, 1)
        assert w.connection is conn


class TestWindowRepr:
    """Tests for Window.__repr__."""

    def test_repr_basic(self):
        conn = Mock()
        frame = iterm2.util.Frame(iterm2.util.Point(10, 20), iterm2.util.Size(100, 200))
        w = iterm2.window.Window(conn, "w1", [], frame, 1)
        r = repr(w)
        assert "w1" in r
        assert "Window" in r

    def test_repr_with_frame(self):
        conn = Mock()
        frame = iterm2.util.Frame(iterm2.util.Point(0, 0), iterm2.util.Size(800, 600))
        w = iterm2.window.Window(conn, "wx", [], frame, 3)
        r = repr(w)
        assert "800" in r
        assert "600" in r

    def test_repr_with_none_frame(self):
        conn = Mock()
        w = iterm2.window.Window(conn, "wn", [], None, 1)
        r = repr(w)
        assert "wn" in r
        assert "[Undefined]" in r


class TestWindowProperties:
    """Tests for Window property accessors."""

    def test_window_id(self):
        conn = Mock()
        w = iterm2.window.Window(conn, "unique-id-123", [], None, 1)
        assert w.window_id == "unique-id-123"

    def test_window_number(self):
        conn = Mock()
        w = iterm2.window.Window(conn, "w", [], None, 7)
        assert w.window_number == 7

    def test_window_number_zero(self):
        conn = Mock()
        w = iterm2.window.Window(conn, "w", [], None, 0)
        assert w.window_number == 0

    def test_tabs_returns_list(self):
        conn = Mock()
        tabs = [Mock(), Mock()]
        w = iterm2.window.Window(conn, "w", tabs, None, 1)
        assert isinstance(w.tabs, list)
        assert len(w.tabs) == 2

    def test_current_tab_none_when_no_selected(self):
        conn = Mock()
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        w = iterm2.window.Window(conn, "w", [tab1], None, 1)
        assert w.current_tab is None

    def test_current_tab_found(self):
        conn = Mock()
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        tab2 = Mock(spec=iterm2.tab.Tab)
        tab2.tab_id = "t2"
        w = iterm2.window.Window(conn, "w", [tab1, tab2], None, 1)
        w.selected_tab_id = "t2"
        assert w.current_tab is tab2

    def test_current_tab_first_tab(self):
        conn = Mock()
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        w = iterm2.window.Window(conn, "w", [tab1], None, 1)
        w.selected_tab_id = "t1"
        assert w.current_tab is tab1

    def test_current_tab_not_found(self):
        conn = Mock()
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        w = iterm2.window.Window(conn, "w", [tab1], None, 1)
        w.selected_tab_id = "nonexistent"
        assert w.current_tab is None

    def test_selected_tab_id_setter(self):
        conn = Mock()
        w = iterm2.window.Window(conn, "w", [], None, 1)
        w.selected_tab_id = "new-id"
        assert w.selected_tab_id == "new-id"


class TestWindowUpdateFrom:
    """Tests for Window.update_from."""

    def test_update_from_copies_tabs(self):
        conn = Mock()
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        tab2 = Mock(spec=iterm2.tab.Tab)
        tab2.tab_id = "t2"
        w1 = iterm2.window.Window(conn, "w1", [tab1], None, 1)
        w2 = iterm2.window.Window(conn, "w2", [tab2], None, 2)
        w1.update_from(w2)
        assert w1.tabs == w2.tabs

    def test_update_from_copies_frame(self):
        conn = Mock()
        frame1 = iterm2.util.Frame()
        frame2 = iterm2.util.Frame(iterm2.util.Point(5, 5), iterm2.util.Size(50, 50))
        w1 = iterm2.window.Window(conn, "w1", [], frame1, 1)
        w2 = iterm2.window.Window(conn, "w2", [], frame2, 2)
        w1.update_from(w2)
        assert w1.frame is frame2

    def test_update_from_does_not_change_id(self):
        conn = Mock()
        w1 = iterm2.window.Window(conn, "original", [], None, 1)
        w2 = iterm2.window.Window(conn, "other", [], None, 2)
        w1.update_from(w2)
        assert w1.window_id == "original"


class TestWindowUpdateTab:
    """Tests for Window.update_tab."""

    def test_update_tab_found(self):
        conn = Mock()
        old_tab = Mock(spec=iterm2.tab.Tab)
        old_tab.tab_id = "t1"
        new_tab = Mock(spec=iterm2.tab.Tab)
        new_tab.tab_id = "t1"
        w = iterm2.window.Window(conn, "w", [old_tab], None, 1)
        w.update_tab(new_tab)
        assert w.tabs[0] is new_tab

    def test_update_tab_not_found(self):
        conn = Mock()
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        other_tab = Mock(spec=iterm2.tab.Tab)
        other_tab.tab_id = "t99"
        w = iterm2.window.Window(conn, "w", [tab1], None, 1)
        w.update_tab(other_tab)
        assert w.tabs[0] is tab1

    def test_update_tab_middle_position(self):
        conn = Mock()
        t1 = Mock(spec=iterm2.tab.Tab)
        t1.tab_id = "t1"
        t2 = Mock(spec=iterm2.tab.Tab)
        t2.tab_id = "t2"
        t3 = Mock(spec=iterm2.tab.Tab)
        t3.tab_id = "t3"
        new_t2 = Mock(spec=iterm2.tab.Tab)
        new_t2.tab_id = "t2"
        w = iterm2.window.Window(conn, "w", [t1, t2, t3], None, 1)
        w.update_tab(new_t2)
        assert w.tabs[0] is t1
        assert w.tabs[1] is new_t2
        assert w.tabs[2] is t3

    def test_update_tab_empty_list(self):
        conn = Mock()
        new_tab = Mock(spec=iterm2.tab.Tab)
        new_tab.tab_id = "t1"
        w = iterm2.window.Window(conn, "w", [], None, 1)
        w.update_tab(new_tab)
        assert w.tabs == []


class TestWindowPrettyStr:
    """Tests for Window.pretty_str."""

    def test_pretty_str_basic(self):
        conn = Mock()
        frame = iterm2.util.Frame(iterm2.util.Point(0, 0), iterm2.util.Size(100, 100))
        w = iterm2.window.Window(conn, "w1", [], frame, 1)
        result = w.pretty_str()
        assert "Window" in result
        assert "w1" in result
        assert result.endswith("\n")

    def test_pretty_str_with_indent(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        w = iterm2.window.Window(conn, "w1", [], frame, 1)
        result = w.pretty_str(indent=">>")
        assert result.startswith(">>Window")

    def test_pretty_str_with_tab(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        tab = Mock(spec=iterm2.tab.Tab)
        tab.tab_id = "t1"
        tab.pretty_str = Mock(return_value="  TabContent\n")
        w = iterm2.window.Window(conn, "w1", [tab], frame, 1)
        result = w.pretty_str()
        tab.pretty_str.assert_called_once_with(indent="  ")
        assert "TabContent" in result


class TestWindowCreateFromProto:
    """Tests for Window.create_from_proto."""

    def _make_proto_window(self, window_id="wid", number=1, tabs=None):
        """Build a minimal protobuf window message."""
        win = Mock()
        win.window_id = window_id
        win.number = number
        win.frame = iterm2.util.Frame()
        if tabs is None:
            win.tabs = []
        else:
            win.tabs = tabs
        return win

    def _make_proto_tab(self, tab_id="tid", root_node=None, tmux_window_id=None,
                        tmux_connection_id=None, minimized_summaries=None):
        """Build a minimal protobuf tab message."""
        tab = Mock()
        tab.tab_id = tab_id
        tab.root = root_node or Mock()
        tab.tmux_window_id = tmux_window_id or ""
        tab.tmux_connection_id = tmux_connection_id or ""
        tab.minimized_sessions = minimized_summaries or []
        # HasField returns True for non-empty string
        tab.HasField = Mock(side_effect=lambda f: f == "tmux_window_id" and bool(tmux_window_id))
        return tab

    def test_create_from_proto_empty_tabs_returns_none(self):
        conn = Mock()
        win_proto = self._make_proto_window()
        result = iterm2.window.Window.create_from_proto(conn, win_proto)
        assert result is None

    def test_create_from_proto_with_one_tab(self):
        conn = Mock()
        root_node = Mock()
        root_node.vertical = False
        root_node.links = []
        tab_proto = self._make_proto_tab(tab_id="t1", root_node=root_node)
        win_proto = self._make_proto_window(window_id="w1", tabs=[tab_proto])

        with patch.object(iterm2.session.Splitter, 'from_node') as mock_from_node:
            splitter = iterm2.session.Splitter()
            mock_from_node.return_value = splitter

            result = iterm2.window.Window.create_from_proto(conn, win_proto)

        assert result is not None
        assert result.window_id == "w1"
        assert len(result.tabs) == 1
        assert result.tabs[0].tab_id == "t1"

    def test_create_from_proto_with_tmux_window_id(self):
        conn = Mock()
        root_node = Mock()
        root_node.vertical = False
        root_node.links = []
        tab_proto = self._make_proto_tab(
            tab_id="t1",
            root_node=root_node,
            tmux_window_id="-1",
            tmux_connection_id="conn123"
        )
        win_proto = self._make_proto_window(tabs=[tab_proto])

        with patch.object(iterm2.session.Splitter, 'from_node') as mock_from_node:
            splitter = iterm2.session.Splitter()
            mock_from_node.return_value = splitter

            result = iterm2.window.Window.create_from_proto(conn, win_proto)

        assert result.tabs[0].tmux_window_id == "-1"
        assert result.tabs[0].tmux_connection_id == "conn123"

    def test_create_from_proto_without_tmux_window_id(self):
        conn = Mock()
        root_node = Mock()
        root_node.vertical = False
        root_node.links = []
        tab_proto = self._make_proto_tab(
            tab_id="t1",
            root_node=root_node,
            tmux_window_id=None
        )
        win_proto = self._make_proto_window(tabs=[tab_proto])

        with patch.object(iterm2.session.Splitter, 'from_node') as mock_from_node:
            splitter = iterm2.session.Splitter()
            mock_from_node.return_value = splitter

            result = iterm2.window.Window.create_from_proto(conn, win_proto)

        assert result.tabs[0].tmux_window_id is None

    def test_create_from_proto_with_minimized_sessions(self):
        conn = Mock()
        root_node = Mock()
        root_node.vertical = False
        root_node.links = []

        summary = Mock()
        summary.unique_identifier = "minimized-sess-1"
        summary.title = "Minimized Session"
        summary.grid_size = Mock()
        summary.grid_size.width = 80
        summary.grid_size.height = 24

        tab_proto = self._make_proto_tab(
            tab_id="t1",
            root_node=root_node,
            minimized_summaries=[summary]
        )
        win_proto = self._make_proto_window(tabs=[tab_proto])

        with patch.object(iterm2.session.Splitter, 'from_node') as mock_from_node:
            splitter = iterm2.session.Splitter()
            mock_from_node.return_value = splitter

            result = iterm2.window.Window.create_from_proto(conn, win_proto)

        assert len(result.tabs[0].minimized_sessions) == 1
        assert result.tabs[0].minimized_sessions[0].session_id == "minimized-sess-1"

    def test_create_from_proto_multiple_tabs(self):
        conn = Mock()
        root_node = Mock()
        root_node.vertical = False
        root_node.links = []

        tab1_proto = self._make_proto_tab(tab_id="t1", root_node=root_node)
        tab2_proto = self._make_proto_tab(tab_id="t2", root_node=root_node)
        win_proto = self._make_proto_window(window_id="w1", tabs=[tab1_proto, tab2_proto])

        with patch.object(iterm2.session.Splitter, 'from_node') as mock_from_node:
            splitter = iterm2.session.Splitter()
            mock_from_node.return_value = splitter

            result = iterm2.window.Window.create_from_proto(conn, win_proto)

        assert len(result.tabs) == 2
        assert result.tabs[0].tab_id == "t1"
        assert result.tabs[1].tab_id == "t2"

    def test_create_from_proto_window_number_and_frame(self):
        conn = Mock()
        frame = iterm2.util.Frame(iterm2.util.Point(100, 200), iterm2.util.Size(400, 300))
        root_node = Mock()
        root_node.vertical = False
        root_node.links = []
        tab_proto = self._make_proto_tab(tab_id="t1", root_node=root_node)

        win_proto = self._make_proto_window(window_id="w1", number=5, tabs=[tab_proto])
        win_proto.frame = frame

        with patch.object(iterm2.session.Splitter, 'from_node') as mock_from_node:
            splitter = iterm2.session.Splitter()
            mock_from_node.return_value = splitter

            result = iterm2.window.Window.create_from_proto(conn, win_proto)

        assert result.window_number == 5
        assert result.frame is frame


class TestWindowDelegateFactory:
    """Tests for DELEGATE_FACTORY constant."""

    def test_delegate_factory_is_callable(self):
        assert iterm2.window.DELEGATE_FACTORY is not None
        assert callable(iterm2.window.DELEGATE_FACTORY)

    def test_delegate_factory_is_settable(self):
        original = iterm2.window.DELEGATE_FACTORY
        try:
            iterm2.window.DELEGATE_FACTORY = lambda c: asyncio.coroutine(lambda: None)()
            assert iterm2.window.DELEGATE_FACTORY is not original
        finally:
            iterm2.window.DELEGATE_FACTORY = original


class TestWindowDelegate:
    """Tests for Window.Delegate abstract class."""

    def test_delegate_is_abstract(self):
        with pytest.raises(TypeError):
            iterm2.window.Window.Delegate()

    def test_delegate_has_required_methods(self):
        assert hasattr(iterm2.window.Window.Delegate, 'window_delegate_get_window_with_session_id')
        assert hasattr(iterm2.window.Window.Delegate, 'window_delegate_get_tab_by_id')
        assert hasattr(iterm2.window.Window.Delegate, 'window_delegate_get_tab_with_session_id')


class TestWindowAsyncMethods:
    """Tests for Window async methods using mocks."""

    @pytest.fixture
    def window(self):
        conn = Mock()
        frame = iterm2.util.Frame()
        return iterm2.window.Window(conn, "w1", [], frame, 1)

    @pytest.fixture
    def ok_get_property_response(self):
        resp = Mock()
        status_val = iterm2.api_pb2.GetPropertyResponse.Status.Value("OK")
        resp.get_property_response = Mock(
            status=status_val,
            json_value=json.dumps({"origin": {"x": 10, "y": 20}, "size": {"width": 800, "height": 600}})
        )
        return resp

    @pytest.fixture
    def ok_set_property_response(self):
        resp = Mock()
        setattr(resp, 'set_property_response', Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("OK")
        ))
        return resp

    @pytest.fixture
    def ok_variable_response(self):
        resp = Mock()
        status_val = iterm2.api_pb2.VariableResponse.Status.Value("OK")
        resp.variable_response = Mock(
            status=status_val,
            values=[json.dumps("test_value")]
        )
        return resp

    @pytest.fixture
    def ok_saved_arrangement_response(self):
        resp = Mock()
        ok_status = iterm2.api_pb2.CreateTabResponse.Status.Value("OK")
        resp.create_tab_response = Mock(status=ok_status)
        resp.saved_arrangement_response = Mock(
            status=iterm2.api_pb2.SavedArrangementResponse.Status.Value("OK")
        )
        return resp

    @pytest.mark.asyncio
    async def test_async_activate(self, window):
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await window.async_activate()
            iterm2.rpc.async_activate.assert_awaited_once()
            call_kwargs = iterm2.rpc.async_activate.await_args[1]
            assert call_kwargs['window_id'] == "w1"

    @pytest.mark.asyncio
    async def test_async_close_default(self, window):
        mock_resp = Mock()
        mock_resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("OK")]
        )
        with patch.object(iterm2.rpc, 'async_close', new=AsyncMock(return_value=mock_resp)):
            await window.async_close()
            iterm2.rpc.async_close.assert_awaited_once()
            call_kwargs = iterm2.rpc.async_close.await_args[1]
            assert call_kwargs['windows'] == ["w1"]
            assert call_kwargs['force'] is False

    @pytest.mark.asyncio
    async def test_async_close_force(self, window):
        mock_resp = Mock()
        mock_resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("OK")]
        )
        with patch.object(iterm2.rpc, 'async_close', new=AsyncMock(return_value=mock_resp)):
            await window.async_close(force=True)
            call_kwargs = iterm2.rpc.async_close.await_args[1]
            assert call_kwargs['force'] is True

    @pytest.mark.asyncio
    async def test_async_close_error(self, window):
        mock_resp = Mock()
        err_status = iterm2.api_pb2.CloseResponse.Status.Value("USER_DECLINED")
        mock_resp.close_response = Mock(statuses=[err_status])
        with patch.object(iterm2.rpc, 'async_close', new=AsyncMock(return_value=mock_resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await window.async_close()

    @pytest.mark.asyncio
    async def test_async_get_frame_ok(self, window, ok_get_property_response):
        with patch.object(iterm2.rpc, 'async_get_property', new=AsyncMock(return_value=ok_get_property_response)):
            frame = await window.async_get_frame()
            assert frame.origin.x == 10
            assert frame.origin.y == 20
            assert frame.size.width == 800
            assert frame.size.height == 600

    @pytest.mark.asyncio
    async def test_async_get_frame_error(self, window):
        resp = Mock()
        resp.get_property_response = Mock(
            status=iterm2.api_pb2.GetPropertyResponse.Status.Value("UNRECOGNIZED_NAME")
        )
        with patch.object(iterm2.rpc, 'async_get_property', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.window.GetPropertyException):
                await window.async_get_frame()

    @pytest.mark.asyncio
    async def test_async_set_frame_ok(self, window, ok_set_property_response):
        frame = iterm2.util.Frame(iterm2.util.Point(0, 0), iterm2.util.Size(100, 200))
        with patch.object(iterm2.rpc, 'async_set_property', new=AsyncMock(return_value=ok_set_property_response)):
            await window.async_set_frame(frame)
            iterm2.rpc.async_set_property.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_set_frame_error(self, window):
        resp = Mock()
        resp.set_property_response = Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("UNRECOGNIZED_NAME")
        )
        resp.get_property_response = Mock(status=1)
        frame = iterm2.util.Frame()
        with patch.object(iterm2.rpc, 'async_set_property', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.window.SetPropertyException):
                await window.async_set_frame(frame)

    @pytest.mark.asyncio
    async def test_async_get_fullscreen_true(self, window):
        resp = Mock()
        resp.get_property_response = Mock(
            status=iterm2.api_pb2.GetPropertyResponse.Status.Value("OK"),
            json_value=json.dumps(True)
        )
        with patch.object(iterm2.rpc, 'async_get_property', new=AsyncMock(return_value=resp)):
            result = await window.async_get_fullscreen()
            assert result is True

    @pytest.mark.asyncio
    async def test_async_get_fullscreen_false(self, window):
        resp = Mock()
        resp.get_property_response = Mock(
            status=iterm2.api_pb2.GetPropertyResponse.Status.Value("OK"),
            json_value=json.dumps(False)
        )
        with patch.object(iterm2.rpc, 'async_get_property', new=AsyncMock(return_value=resp)):
            result = await window.async_get_fullscreen()
            assert result is False

    @pytest.mark.asyncio
    async def test_async_set_fullscreen(self, window, ok_set_property_response):
        with patch.object(iterm2.rpc, 'async_set_property', new=AsyncMock(return_value=ok_set_property_response)):
            await window.async_set_fullscreen(True)
            call_args = iterm2.rpc.async_set_property.await_args
            assert json.loads(call_args[0][2]) is True

    @pytest.mark.asyncio
    async def test_async_get_variable_ok(self, window, ok_variable_response):
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=ok_variable_response)):
            result = await window.async_get_variable("user.myvar")
            assert result == "test_value"

    @pytest.mark.asyncio
    async def test_async_get_variable_error(self, window):
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("WINDOW_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await window.async_get_variable("user.myvar")

    @pytest.mark.asyncio
    async def test_async_set_variable_ok(self, window, ok_variable_response):
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=ok_variable_response)):
            await window.async_set_variable("user.myvar", {"key": "value"})
            call_kwargs = iterm2.rpc.async_variable.await_args[1]
            assert call_kwargs['window_id'] == "w1"
            sets = call_kwargs['sets']
            assert len(sets) == 1
            assert sets[0][0] == "user.myvar"
            assert json.loads(sets[0][1]) == {"key": "value"}

    @pytest.mark.asyncio
    async def test_async_set_title(self, window):
        with patch.object(iterm2.rpc, 'async_invoke_method', new=AsyncMock()):
            await window.async_set_title("My Title")
            iterm2.rpc.async_invoke_method.assert_awaited_once()
            call_args = iterm2.rpc.async_invoke_method.await_args
            invocation = call_args[1]['invocation'] if 'invocation' in call_args[1] else call_args[0][2]
            assert "iterm2.set_title" in invocation
            assert "My Title" in invocation

    @pytest.mark.asyncio
    async def test_async_save_window_as_arrangement_ok(self, window, ok_saved_arrangement_response):
        with patch.object(iterm2.rpc, 'async_save_arrangement', new=AsyncMock(return_value=ok_saved_arrangement_response)):
            await window.async_save_window_as_arrangement("MyLayout")
            iterm2.rpc.async_save_arrangement.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_restore_window_arrangement_ok(self, window, ok_saved_arrangement_response):
        with patch.object(iterm2.rpc, 'async_restore_arrangement', new=AsyncMock(return_value=ok_saved_arrangement_response)):
            await window.async_restore_window_arrangement("MyLayout")
            iterm2.rpc.async_restore_arrangement.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_restore_window_arrangement_error(self, window):
        resp = Mock()
        resp.create_tab_response = Mock(
            status=iterm2.api_pb2.CreateTabResponse.Status.Value("INVALID_WINDOW_ID")
        )
        resp.saved_arrangement_response = Mock(
            status=iterm2.api_pb2.SavedArrangementResponse.Status.Value("ARRANGEMENT_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_restore_arrangement', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.arrangement.SavedArrangementException):
                await window.async_restore_window_arrangement("NonExistent")

    @pytest.mark.asyncio
    async def test_async_invoke_function_success(self, window):
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='success')
        )
        resp.invoke_function_response.success = Mock(
            json_result=json.dumps({"result": 42})
        )
        with patch.object(iterm2.rpc, 'async_invoke_function', new=AsyncMock(return_value=resp)):
            result = await window.async_invoke_function("myFunc()")
            assert result == {"result": 42}

    @pytest.mark.asyncio
    async def test_async_invoke_function_timeout(self, window):
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("TIMEOUT"),
            error_reason=""
        )
        with patch.object(iterm2.rpc, 'async_invoke_function', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException, match="Timeout"):
                await window.async_invoke_function("slowFunc()")

    @pytest.mark.asyncio
    async def test_async_invoke_function_error(self, window):
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("FAILED"),
            error_reason="Function not found"
        )
        with patch.object(iterm2.rpc, 'async_invoke_function', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await window.async_invoke_function("missingFunc()")

    @pytest.mark.asyncio
    async def test_async_create_tab_ok_with_delegate(self, window):
        resp = Mock()
        resp.create_tab_response = Mock(
            status=iterm2.api_pb2.CreateTabResponse.Status.Value("OK"),
            session_id="new-sess"
        )
        new_tab = Mock(spec=iterm2.tab.Tab)
        new_tab.tab_id = "new-tab"
        delegate = Mock()
        delegate.window_delegate_get_tab_with_session_id = AsyncMock(return_value=new_tab)
        iterm2.window.Window.delegate = delegate

        try:
            with patch.object(iterm2.rpc, 'async_create_tab', new=AsyncMock(return_value=resp)):
                result = await window.async_create_tab(profile="Default")
                assert result is new_tab
        finally:
            iterm2.window.Window.delegate = None

    @pytest.mark.asyncio
    async def test_async_create_tab_error(self, window):
        resp = Mock()
        resp.create_tab_response = Mock(
            status=iterm2.api_pb2.CreateTabResponse.Status.Value("INVALID_WINDOW_ID"),
        )
        iterm2.window.Window.delegate = Mock()
        try:
            with patch.object(iterm2.rpc, 'async_create_tab', new=AsyncMock(return_value=resp)):
                with pytest.raises(iterm2.window.CreateTabException):
                    await window.async_create_tab()
        finally:
            iterm2.window.Window.delegate = None

    @pytest.mark.asyncio
    async def test_async_create_tab_with_command(self, window):
        resp = Mock()
        resp.create_tab_response = Mock(
            status=iterm2.api_pb2.CreateTabResponse.Status.Value("OK"),
            session_id="new-sess"
        )
        new_tab = Mock(spec=iterm2.tab.Tab)
        delegate = Mock()
        delegate.window_delegate_get_tab_with_session_id = AsyncMock(return_value=new_tab)
        iterm2.window.Window.delegate = delegate

        try:
            with patch.object(iterm2.rpc, 'async_create_tab', new=AsyncMock(return_value=resp)) as mock_rpc:
                await window.async_create_tab(command="echo hello")
                call_kwargs = mock_rpc.await_args[1]
                assert call_kwargs['profile_customizations'] is not None
        finally:
            iterm2.window.Window.delegate = None

    @pytest.mark.asyncio
    async def test_async_create_tab_with_profile_customizations(self, window):
        resp = Mock()
        resp.create_tab_response = Mock(
            status=iterm2.api_pb2.CreateTabResponse.Status.Value("OK"),
            session_id="new-sess"
        )
        new_tab = Mock(spec=iterm2.tab.Tab)
        delegate = Mock()
        delegate.window_delegate_get_tab_with_session_id = AsyncMock(return_value=new_tab)
        iterm2.window.Window.delegate = delegate

        custom = iterm2.profile.LocalWriteOnlyProfile()
        custom.set_name("Custom")

        try:
            with patch.object(iterm2.rpc, 'async_create_tab', new=AsyncMock(return_value=resp)) as mock_rpc:
                await window.async_create_tab(profile_customizations=custom)
                call_kwargs = mock_rpc.await_args[1]
                assert call_kwargs['profile_customizations'] is not None
        finally:
            iterm2.window.Window.delegate = None

    @pytest.mark.asyncio
    async def test_async_create_tab_with_index(self, window):
        resp = Mock()
        resp.create_tab_response = Mock(
            status=iterm2.api_pb2.CreateTabResponse.Status.Value("OK"),
            session_id="new-sess"
        )
        new_tab = Mock(spec=iterm2.tab.Tab)
        delegate = Mock()
        delegate.window_delegate_get_tab_with_session_id = AsyncMock(return_value=new_tab)
        iterm2.window.Window.delegate = delegate

        try:
            with patch.object(iterm2.rpc, 'async_create_tab', new=AsyncMock(return_value=resp)) as mock_rpc:
                await window.async_create_tab(index=2)
                call_kwargs = mock_rpc.await_args[1]
                assert call_kwargs['index'] == 2
        finally:
            iterm2.window.Window.delegate = None

    @pytest.mark.asyncio
    async def test_async_set_tabs(self, window):
        tab1 = Mock(spec=iterm2.tab.Tab)
        tab1.tab_id = "t1"
        tab2 = Mock(spec=iterm2.tab.Tab)
        tab2.tab_id = "t2"
        with patch.object(iterm2.rpc, 'async_reorder_tabs', new=AsyncMock()):
            await window.async_set_tabs([tab1, tab2])
            iterm2.rpc.async_reorder_tabs.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_create_tmux_tab(self, window):
        tmux_conn = Mock()
        tmux_conn.connection_id = "tmux-conn-1"

        resp = Mock()
        resp.tmux_response = Mock(
            status=iterm2.api_pb2.TmuxResponse.Status.Value("OK")
        )
        resp.tmux_response.create_window = Mock(tab_id="new-tmux-tab")

        delegate = Mock()
        delegate.window_delegate_get_tab_by_id = AsyncMock(return_value=Mock(spec=iterm2.tab.Tab))
        iterm2.window.Window.delegate = None
        iterm2.window.DELEGATE_FACTORY = AsyncMock(return_value=delegate)

        try:
            with patch.object(iterm2.rpc, 'async_rpc_create_tmux_window', new=AsyncMock(return_value=resp)):
                result = await window.async_create_tmux_tab(tmux_conn)
                assert iterm2.window.Window.delegate is not None
                delegate.window_delegate_get_tab_by_id.assert_awaited_once_with("new-tmux-tab")
        finally:
            iterm2.window.Window.delegate = None
            iterm2.window.DELEGATE_FACTORY = None

    @pytest.mark.asyncio
    async def test_async_create_tmux_tab_error(self, window):
        tmux_conn = Mock()
        tmux_conn.connection_id = "tmux-conn-1"

        resp = Mock()
        resp.tmux_response = Mock(
            status=iterm2.api_pb2.TmuxResponse.Status.Value("INVALID_REQUEST")
        )

        with patch.object(iterm2.rpc, 'async_rpc_create_tmux_window', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.window.CreateTabException):
                await window.async_create_tmux_tab(tmux_conn)
