"""Extended tests for iterm2.tab.Tab class."""
import json
from unittest.mock import Mock, AsyncMock, patch

import pytest
import iterm2
import iterm2.tab
import iterm2.session
import iterm2.util
import iterm2.api_pb2


class TestTabInit:
    """Tests for Tab.__init__."""

    def test_init_minimal(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.tab_id == "t1"
        assert t.root is root
        assert t.active_session_id is None
        assert t.tmux_window_id is None
        assert t.tmux_connection_id is None
        assert t.minimized_sessions == []

    def test_init_all_params(self):
        conn = Mock()
        root = iterm2.session.Splitter(vertical=True)
        min_sess = Mock(spec=iterm2.session.Session)
        min_sess.session_id = "min-sess-1"
        t = iterm2.tab.Tab(
            conn, "t2", root,
            tmux_window_id="-1",
            tmux_connection_id="conn-abc",
            minimized_sessions=[min_sess]
        )
        assert t.tab_id == "t2"
        assert t.tmux_window_id == "-1"
        assert t.tmux_connection_id == "conn-abc"
        assert len(t.minimized_sessions) == 1
        assert t.minimized_sessions[0].session_id == "min-sess-1"

    def test_init_stores_connection(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.connection is conn

    def test_init_minimized_sessions_is_copy(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        sess = Mock(spec=iterm2.session.Session)
        sess.session_id = "s1"
        original = [sess]
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=original)
        original.append(Mock(spec=iterm2.session.Session))
        assert len(t.minimized_sessions) == 1


class TestTabRepr:
    """Tests for Tab.__repr__."""

    def test_repr_basic(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "tab-123", root)
        r = repr(t)
        assert "tab-123" in r
        assert "Tab" in r

    def test_repr_with_sessions(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        sess = Mock(spec=iterm2.session.Session)
        sess.session_id = "s1"
        root.add_child(sess)
        t = iterm2.tab.Tab(conn, "t1", root)
        r = repr(t)
        assert "t1" in r


class TestTabProperties:
    """Tests for Tab property accessors."""

    def test_tab_id(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "unique-tab-id", root)
        assert t.tab_id == "unique-tab-id"

    def test_sessions(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "s1"
        root.add_child(s1)
        t = iterm2.tab.Tab(conn, "t1", root)
        assert len(t.sessions) == 1
        assert t.sessions[0].session_id == "s1"

    def test_sessions_empty(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.sessions == []

    def test_sessions_nested_splitter(self):
        conn = Mock()
        root = iterm2.session.Splitter(vertical=False)
        inner = iterm2.session.Splitter(vertical=True)
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "s1"
        inner.add_child(s1)
        root.add_child(inner)
        t = iterm2.tab.Tab(conn, "t1", root)
        assert len(t.sessions) == 1
        assert t.sessions[0].session_id == "s1"

    def test_root(self):
        conn = Mock()
        root = iterm2.session.Splitter(vertical=True)
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.root is root
        assert t.root.vertical is True

    def test_minimized_sessions(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "min1"
        s2 = Mock(spec=iterm2.session.Session)
        s2.session_id = "min2"
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=[s1, s2])
        assert len(t.minimized_sessions) == 2
        assert t.minimized_sessions[0].session_id == "min1"

    def test_minimized_sessions_returns_copy(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "min1"
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=[s1])
        result = t.minimized_sessions
        result.append(Mock(spec=iterm2.session.Session))
        assert len(t.minimized_sessions) == 1

    def test_all_sessions_combined(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        visible = Mock(spec=iterm2.session.Session)
        visible.session_id = "vis"
        root.add_child(visible)
        minimized = Mock(spec=iterm2.session.Session)
        minimized.session_id = "min"
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=[minimized])
        all_sess = t.all_sessions
        assert len(all_sess) == 2
        ids = [s.session_id for s in all_sess]
        assert "vis" in ids
        assert "min" in ids

    def test_all_sessions_no_minimized(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s = Mock(spec=iterm2.session.Session)
        s.session_id = "only"
        root.add_child(s)
        t = iterm2.tab.Tab(conn, "t1", root)
        assert len(t.all_sessions) == 1

    def test_tmux_window_id(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root, tmux_window_id="-5")
        assert t.tmux_window_id == "-5"

    def test_tmux_window_id_none(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.tmux_window_id is None

    def test_tmux_connection_id(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root, tmux_connection_id="conn-xyz")
        assert t.tmux_connection_id == "conn-xyz"

    def test_tmux_connection_id_none(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.tmux_connection_id is None


class TestTabActiveSessionId:
    """Tests for Tab.active_session_id getter/setter."""

    def test_active_session_id_default_none(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.active_session_id is None

    def test_active_session_id_setter(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        t.active_session_id = "sess-42"
        assert t.active_session_id == "sess-42"

    def test_active_session_id_overwrite(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        t.active_session_id = "first"
        t.active_session_id = "second"
        assert t.active_session_id == "second"


class TestTabCurrentSession:
    """Tests for Tab.current_session."""

    def test_current_session_found(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "s1"
        s2 = Mock(spec=iterm2.session.Session)
        s2.session_id = "s2"
        root.add_child(s1)
        root.add_child(s2)
        t = iterm2.tab.Tab(conn, "t1", root)
        t.active_session_id = "s2"
        assert t.current_session is s2

    def test_current_session_not_found(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "s1"
        root.add_child(s1)
        t = iterm2.tab.Tab(conn, "t1", root)
        t.active_session_id = "nonexistent"
        assert t.current_session is None

    def test_current_session_none_when_no_active_id(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "s1"
        root.add_child(s1)
        t = iterm2.tab.Tab(conn, "t1", root)
        assert t.current_session is None

    def test_current_session_empty_sessions(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        t.active_session_id = "anything"
        assert t.current_session is None


class TestTabUpdateFrom:
    """Tests for Tab.update_from."""

    def test_update_from_copies_root(self):
        conn = Mock()
        root1 = iterm2.session.Splitter()
        root2 = iterm2.session.Splitter(vertical=True)
        t1 = iterm2.tab.Tab(conn, "t1", root1)
        t2 = iterm2.tab.Tab(conn, "t2", root2)
        t1.update_from(t2)
        assert t1.root is root2
        assert t1.root.vertical is True

    def test_update_from_copies_minimized_sessions(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        min_sess = Mock(spec=iterm2.session.Session)
        min_sess.session_id = "min-sess"
        t1 = iterm2.tab.Tab(conn, "t1", root)
        t2 = iterm2.tab.Tab(conn, "t2", root, minimized_sessions=[min_sess])
        t1.update_from(t2)
        assert len(t1.minimized_sessions) == 1
        assert t1.minimized_sessions[0].session_id == "min-sess"

    def test_update_from_minimized_is_copy(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        min_sess = Mock(spec=iterm2.session.Session)
        min_sess.session_id = "ms"
        t1 = iterm2.tab.Tab(conn, "t1", root)
        t2 = iterm2.tab.Tab(conn, "t2", root, minimized_sessions=[min_sess])
        t1.update_from(t2)
        t1.minimized_sessions.append(Mock(spec=iterm2.session.Session))
        assert len(t2.minimized_sessions) == 1


class TestTabUpdateSession:
    """Tests for Tab.update_session."""

    def test_update_session_in_root(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        old_sess = Mock(spec=iterm2.session.Session)
        old_sess.session_id = "s1"
        root.add_child(old_sess)
        new_sess = Mock(spec=iterm2.session.Session)
        new_sess.session_id = "s1"
        t = iterm2.tab.Tab(conn, "t1", root)
        t.update_session(new_sess)
        assert root.children[0] is new_sess

    def test_update_session_in_minimized(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        old_min = Mock(spec=iterm2.session.Session)
        old_min.session_id = "min-sess"
        new_min = Mock(spec=iterm2.session.Session)
        new_min.session_id = "min-sess"
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=[old_min])
        t.update_session(new_min)
        assert t.minimized_sessions[0] is new_min

    def test_update_session_not_found(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        s1 = Mock(spec=iterm2.session.Session)
        s1.session_id = "s1"
        root.add_child(s1)
        other = Mock(spec=iterm2.session.Session)
        other.session_id = "other"
        t = iterm2.tab.Tab(conn, "t1", root)
        t.update_session(other)
        assert root.children[0] is s1

    def test_update_session_prefers_root_over_minimized(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        root_sess = Mock(spec=iterm2.session.Session)
        root_sess.session_id = "shared-id"
        root.add_child(root_sess)
        min_sess = Mock(spec=iterm2.session.Session)
        min_sess.session_id = "shared-id"
        new_sess = Mock(spec=iterm2.session.Session)
        new_sess.session_id = "shared-id"
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=[min_sess])
        t.update_session(new_sess)
        assert root.children[0] is new_sess
        assert t.minimized_sessions[0] is min_sess

    def test_update_session_multiple_minimized(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        m1 = Mock(spec=iterm2.session.Session)
        m1.session_id = "m1"
        m2 = Mock(spec=iterm2.session.Session)
        m2.session_id = "m2"
        m3 = Mock(spec=iterm2.session.Session)
        m3.session_id = "m3"
        new_m2 = Mock(spec=iterm2.session.Session)
        new_m2.session_id = "m2"
        t = iterm2.tab.Tab(conn, "t1", root, minimized_sessions=[m1, m2, m3])
        t.update_session(new_m2)
        assert t.minimized_sessions[0] is m1
        assert t.minimized_sessions[1] is new_m2
        assert t.minimized_sessions[2] is m3


class TestTabPrettyStr:
    """Tests for Tab.pretty_str."""

    def test_pretty_str_basic(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "tab-id", root)
        result = t.pretty_str()
        assert "Tab" in result
        assert "tab-id" in result
        assert result.endswith("\n")

    def test_pretty_str_with_indent(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        result = t.pretty_str(indent="  ")
        assert result.startswith("  Tab")

    def test_pretty_str_includes_root(self):
        conn = Mock()
        root = iterm2.session.Splitter(vertical=True)
        t = iterm2.tab.Tab(conn, "t1", root)
        result = t.pretty_str()
        assert "|" in result


class TestTabDelegate:
    """Tests for Tab.Delegate abstract class."""

    def test_delegate_is_abstract(self):
        with pytest.raises(TypeError):
            iterm2.tab.Tab.Delegate()

    def test_delegate_has_required_methods(self):
        assert hasattr(iterm2.tab.Tab.Delegate, 'tab_delegate_get_window')
        assert hasattr(iterm2.tab.Tab.Delegate, 'tab_delegate_get_window_by_id')


class TestTabWindowProperty:
    """Tests for Tab.window property."""

    def test_window_via_delegate(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        t = iterm2.tab.Tab(conn, "t1", root)
        mock_window = Mock()
        delegate = Mock()
        delegate.tab_delegate_get_window = Mock(return_value=mock_window)
        iterm2.tab.Tab.delegate = delegate
        try:
            result = t.window
            assert result is mock_window
        finally:
            iterm2.tab.Tab.delegate = None


class TestTabAsyncMethods:
    """Tests for Tab async methods using mocks."""

    @pytest.fixture
    def tab(self):
        conn = Mock()
        root = iterm2.session.Splitter()
        return iterm2.tab.Tab(conn, "t1", root)

    @pytest.fixture
    def ok_close_response(self):
        resp = Mock()
        resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("OK")]
        )
        return resp

    @pytest.fixture
    def ok_variable_response(self):
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("OK"),
            values=[json.dumps("tab_value")]
        )
        return resp

    @pytest.fixture
    def ok_set_layout_response(self):
        resp = Mock()
        resp.set_tab_layout_response = Mock(
            status=iterm2.api_pb2.SetTabLayoutResponse.Status.Value("OK")
        )
        return resp

    @pytest.mark.asyncio
    async def test_async_activate(self, tab):
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await tab.async_activate()
            iterm2.rpc.async_activate.assert_awaited_once()
            call_kwargs = iterm2.rpc.async_activate.await_args[1]
            assert call_kwargs['tab_id'] == "t1"

    @pytest.mark.asyncio
    async def test_async_activate_order_window_front_false(self, tab):
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await tab.async_activate(order_window_front=False)
            call_args = iterm2.rpc.async_activate.await_args[0]
            assert call_args[3] is False

    @pytest.mark.asyncio
    async def test_async_select_delegates_to_activate(self, tab):
        with patch.object(tab, 'async_activate', new=AsyncMock()) as mock_act:
            await tab.async_select()
            mock_act.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_close_ok(self, tab, ok_close_response):
        with patch.object(iterm2.rpc, 'async_close', new=AsyncMock(return_value=ok_close_response)):
            await tab.async_close()
            call_kwargs = iterm2.rpc.async_close.await_args[1]
            assert call_kwargs['tabs'] == ["t1"]
            assert call_kwargs['force'] is False

    @pytest.mark.asyncio
    async def test_async_close_force(self, tab, ok_close_response):
        with patch.object(iterm2.rpc, 'async_close', new=AsyncMock(return_value=ok_close_response)):
            await tab.async_close(force=True)
            call_kwargs = iterm2.rpc.async_close.await_args[1]
            assert call_kwargs['force'] is True

    @pytest.mark.asyncio
    async def test_async_close_error(self, tab):
        resp = Mock()
        resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("USER_DECLINED")]
        )
        with patch.object(iterm2.rpc, 'async_close', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await tab.async_close()

    @pytest.mark.asyncio
    async def test_async_get_variable_ok(self, tab, ok_variable_response):
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=ok_variable_response)):
            result = await tab.async_get_variable("user.tabvar")
            assert result == "tab_value"

    @pytest.mark.asyncio
    async def test_async_get_variable_error(self, tab):
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("SESSION_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await tab.async_get_variable("user.var")

    @pytest.mark.asyncio
    async def test_async_set_variable_ok(self, tab, ok_variable_response):
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=ok_variable_response)) as mock_rpc:
            await tab.async_set_variable("user.tabvar", [1, 2, 3])
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['tab_id'] == "t1"
            sets = call_kwargs['sets']
            assert sets[0][0] == "user.tabvar"
            assert json.loads(sets[0][1]) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_async_set_variable_error(self, tab):
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("SESSION_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await tab.async_set_variable("user.var", "val")

    @pytest.mark.asyncio
    async def test_async_set_title(self, tab):
        with patch.object(iterm2.rpc, 'async_invoke_method', new=AsyncMock()):
            await tab.async_set_title("Tab Title")
            iterm2.rpc.async_invoke_method.assert_awaited_once()
            call_args = iterm2.rpc.async_invoke_method.await_args[0]
            assert call_args[1] == "t1"
            invocation = call_args[2]
            assert "iterm2.set_title" in invocation
            assert "Tab Title" in invocation

    @pytest.mark.asyncio
    async def test_async_set_title_empty(self, tab):
        with patch.object(iterm2.rpc, 'async_invoke_method', new=AsyncMock()):
            await tab.async_set_title("")
            invocation = iterm2.rpc.async_invoke_method.await_args[0][2]
            assert "iterm2.set_title" in invocation

    @pytest.mark.asyncio
    async def test_async_invoke_function_success(self, tab):
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='success')
        )
        resp.invoke_function_response.success = Mock(
            json_result=json.dumps({"status": "ok"})
        )
        with patch.object(iterm2.rpc, 'async_invoke_function', new=AsyncMock(return_value=resp)):
            result = await tab.async_invoke_function("testFunc()", timeout=5.0)
            assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_async_invoke_function_timeout(self, tab):
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
                await tab.async_invoke_function("slowFunc()")

    @pytest.mark.asyncio
    async def test_async_invoke_function_error(self, tab):
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("FAILED"),
            error_reason="No such function"
        )
        with patch.object(iterm2.rpc, 'async_invoke_function', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await tab.async_invoke_function("missing()")

    @pytest.mark.asyncio
    async def test_async_update_layout_ok(self, tab, ok_set_layout_response):
        with patch.object(iterm2.rpc, 'async_set_tab_layout', new=AsyncMock(return_value=ok_set_layout_response)):
            await tab.async_update_layout()
            iterm2.rpc.async_set_tab_layout.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_update_layout_error(self, tab):
        resp = Mock()
        resp.set_tab_layout_response = Mock(
            status=iterm2.api_pb2.SetTabLayoutResponse.Status.Value("BAD_TAB_ID")
        )
        with patch.object(iterm2.rpc, 'async_set_tab_layout', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await tab.async_update_layout()

    @pytest.mark.asyncio
    async def test_async_select_pane_in_direction(self, tab):
        with patch.object(iterm2.capabilities, 'supports_select_pane_in_direction', return_value=True):
            with patch.object(iterm2.rpc, 'async_invoke_method', new=AsyncMock(return_value="new-session-id")):
                result = await tab.async_select_pane_in_direction(iterm2.tab.NavigationDirection.LEFT)
                assert result == "new-session-id"
                invocation = iterm2.rpc.async_invoke_method.await_args[0][2]
                assert "iterm2.select_pane_in_direction" in invocation
                assert "left" in invocation

    @pytest.mark.asyncio
    async def test_async_select_pane_in_direction_all_directions(self, tab):
        directions = [
            (iterm2.tab.NavigationDirection.LEFT, "left"),
            (iterm2.tab.NavigationDirection.RIGHT, "right"),
            (iterm2.tab.NavigationDirection.ABOVE, "above"),
            (iterm2.tab.NavigationDirection.BELOW, "below"),
        ]
        for direction, expected_str in directions:
            with patch.object(iterm2.capabilities, 'supports_select_pane_in_direction', return_value=True):
                with patch.object(iterm2.rpc, 'async_invoke_method', new=AsyncMock(return_value=None)):
                    await tab.async_select_pane_in_direction(direction)
                    invocation = iterm2.rpc.async_invoke_method.await_args[0][2]
                    assert expected_str in invocation

    @pytest.mark.asyncio
    async def test_async_select_pane_in_direction_not_supported(self, tab):
        with patch.object(iterm2.capabilities, 'supports_select_pane_in_direction', return_value=False):
            with pytest.raises(iterm2.capabilities.AppVersionTooOld):
                await tab.async_select_pane_in_direction(iterm2.tab.NavigationDirection.LEFT)

    @pytest.mark.asyncio
    async def test_async_move_to_window_success(self, tab):
        mock_window = Mock()
        delegate = Mock()
        delegate.tab_delegate_get_window_by_id = AsyncMock(return_value=mock_window)
        iterm2.tab.Tab.delegate = delegate

        try:
            with patch.object(tab, 'async_invoke_function', new=AsyncMock(return_value="new-window-id")):
                result = await tab.async_move_to_window()
                assert result is mock_window
                delegate.tab_delegate_get_window_by_id.assert_awaited_once_with("new-window-id")
        finally:
            iterm2.tab.Tab.delegate = None

    @pytest.mark.asyncio
    async def test_async_move_to_window_no_window_found(self, tab):
        delegate = Mock()
        delegate.tab_delegate_get_window_by_id = AsyncMock(return_value=None)
        iterm2.tab.Tab.delegate = delegate

        try:
            with patch.object(tab, 'async_invoke_function', new=AsyncMock(return_value="missing-window")):
                with pytest.raises(iterm2.rpc.RPCException, match="No such window"):
                    await tab.async_move_to_window()
        finally:
            iterm2.tab.Tab.delegate = None
