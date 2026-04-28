"""Extended tests for iterm2.app.App class covering uncovered code paths."""
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, call

import pytest
import iterm2
import iterm2.app
import iterm2.window
import iterm2.tab
import iterm2.session
import iterm2.broadcast
import iterm2.util
import iterm2.api_pb2
import iterm2.rpc
import iterm2.connection
import iterm2.notifications


def _make_mock_session(session_id, buried=False):
    """Create a mock session with given ID."""
    sess = Mock(spec=iterm2.session.Session)
    sess.session_id = session_id
    sess.buried = buried
    sess.name = f"Session-{session_id}"
    sess.connection = Mock()
    return sess


def _make_mock_tab(tab_id, session_ids=None):
    """Create a mock tab with given ID and sessions."""
    tab = Mock(spec=iterm2.tab.Tab)
    tab.tab_id = tab_id
    sessions = [_make_mock_session(sid) for sid in (session_ids or [])]
    tab.all_sessions = sessions
    tab.sessions = sessions
    tab.active_session_id = session_ids[0] if session_ids else None
    return tab


def _make_mock_window(window_id, tab_ids=None, session_ids_per_tab=None):
    """Create a mock window with given ID and tabs."""
    win = Mock(spec=iterm2.window.Window)
    win.window_id = window_id
    if tab_ids is None:
        win.tabs = []
        return win
    if session_ids_per_tab is None:
        session_ids_per_tab = [[] for _ in tab_ids]
    tabs = []
    for tid, sids in zip(tab_ids, session_ids_per_tab):
        tabs.append(_make_mock_tab(tid, sids))
    win.tabs = tabs
    return win


def _make_list_sessions_response_proto(window_id="w1", window_number=1,
                                        tab_id="t1", session_id="s1",
                                        buried_session_ids=None):
    """Build a mock ListSessionsResponse protobuf structure."""
    # Build session summary for buried sessions
    buried_summaries = []
    if buried_session_ids:
        for sid in buried_session_ids:
            summary = Mock()
            summary.unique_identifier = sid
            summary.title = f"Buried-{sid}"
            buried_summaries.append(summary)

    # Build window proto
    win_proto = Mock()
    win_proto.window_id = window_id
    win_proto.number = window_number
    win_proto.frame = iterm2.util.Frame()

    # Build tab proto
    tab_proto = Mock()
    tab_proto.tab_id = tab_id
    tab_proto.root = Mock()
    tab_proto.root.vertical = False
    tab_proto.root.links = []
    tab_proto.tmux_window_id = ""
    tab_proto.tmux_connection_id = ""
    tab_proto.minimized_sessions = []
    tab_proto.HasField = Mock(return_value=False)
    win_proto.tabs = [tab_proto]

    # Build response
    response = Mock()
    response.windows = [win_proto]
    response.buried_sessions = buried_summaries
    return response


def _make_focus_response_proto(notifications=None):
    """Build a mock FocusResponse with notifications."""
    focus_resp = Mock()
    focus_resp.focus_response = Mock(
        notifications=notifications or [])
    return focus_resp


def _make_broadcast_domains_response_proto(domains=None):
    """Build a mock GetBroadcastDomainsResponse."""
    resp = Mock()
    resp.get_broadcast_domains_response = Mock(
        broadcast_domains=domains or [])
    return resp


def _make_variable_response_proto(status_str="OK", values=None):
    """Build a mock VariableResponse."""
    resp = Mock()
    status_val = iterm2.api_pb2.VariableResponse.Status.Value(status_str)
    resp.variable_response = Mock(
        status=status_val,
        values=values or []
    )
    return resp


def _make_invoke_function_response_proto(which="success", status_str="OK",
                                          error_reason="", json_result="{}"):
    """Build a mock InvokeFunctionResponse."""
    resp = Mock()
    if which == "success":
        if isinstance(json_result, str):
            json_str = json_result
        else:
            json_str = json.dumps(json_result)
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value="success"),
            success=Mock(json_result=json_str)
        )
    else:
        status_val = iterm2.api_pb2.InvokeFunctionResponse.Status.Value(status_str)
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value="error"),
            error=Mock(status=status_val, error_reason=error_reason)
        )
    return resp


# ---------- Fixtures ----------

@pytest.fixture(autouse=True)
def cleanup_app_instance():
    """Reset App.instance and delegate references after each test."""
    original_instance = iterm2.app.App.instance
    original_session_delegate = iterm2.session.Session.delegate
    original_tab_delegate = iterm2.tab.Tab.delegate
    original_window_delegate = iterm2.window.Window.delegate
    original_tmux_delegate = iterm2.tmux.DELEGATE
    original_disconnect_callbacks = list(iterm2.connection.gDisconnectCallbacks)
    yield
    iterm2.app.App.instance = original_instance
    iterm2.session.Session.delegate = original_session_delegate
    iterm2.tab.Tab.delegate = original_tab_delegate
    iterm2.window.Window.delegate = original_window_delegate
    iterm2.tmux.DELEGATE = original_tmux_delegate
    iterm2.connection.gDisconnectCallbacks[:] = original_disconnect_callbacks


class TestAppInit:
    """Tests for App.__init__."""

    def test_init_stores_connection(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        assert app.connection is conn

    def test_init_stores_windows(self):
        conn = Mock()
        win = Mock()
        win.window_id = "w1"
        app = iterm2.app.App(conn, [win], [])
        assert app.windows == [win]

    def test_init_stores_buried_sessions(self):
        conn = Mock()
        sess = _make_mock_session("buried1", buried=True)
        app = iterm2.app.App(conn, [], [sess])
        assert app.buried_sessions == [sess]

    def test_init_tokens_empty(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        assert app.tokens == []

    def test_init_broadcast_domains_empty(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        assert app.broadcast_domains == []

    def test_init_app_active_none(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        assert app.app_active is None

    def test_init_current_terminal_window_id_none(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        assert app.current_terminal_window_id is None

    def test_init_terminal_windows_alias(self):
        conn = Mock()
        win = Mock()
        win.window_id = "w1"
        app = iterm2.app.App(conn, [win], [])
        assert app.terminal_windows == [win]


class TestAppAsyncConstruct:
    """Tests for App.async_construct."""

    @pytest.mark.asyncio
    async def test_async_construct_happy_path(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        list_resp = _make_list_sessions_response_proto()
        list_wrapper = Mock()
        list_wrapper.list_sessions_response = list_resp

        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])
        broadcast_resp = _make_broadcast_domains_response_proto([])

        with patch.object(iterm2.rpc, 'async_list_sessions',
                          new=AsyncMock(return_value=list_wrapper)), \
             patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)), \
             patch.object(iterm2.rpc, 'async_get_broadcast_domains',
                          new=AsyncMock(return_value=broadcast_resp)), \
             patch.object(iterm2.window.Window, 'create_from_proto',
                          return_value=Mock(window_id="w1", tabs=[])), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_new_session_notification',
                          new=AsyncMock(return_value="tok1")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_terminate_session_notification',
                          new=AsyncMock(return_value="tok2")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_layout_change_notification',
                          new=AsyncMock(return_value="tok3")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_focus_change_notification',
                          new=AsyncMock(return_value="tok4")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_broadcast_domains_change_notification',
                          new=AsyncMock(return_value="tok5")):
            app = await iterm2.app.App.async_construct(conn)

        assert app is not None
        assert app.connection is conn
        assert iterm2.session.Session.delegate is app
        assert iterm2.tab.Tab.delegate is app
        assert iterm2.window.Window.delegate is app
        assert iterm2.tmux.DELEGATE is app
        assert len(app.tokens) == 5


class TestAppAsyncActivate:
    """Tests for App.async_activate."""

    @pytest.mark.asyncio
    async def test_activate_defaults(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await app.async_activate()
            call_kwargs = iterm2.rpc.async_activate.await_args[1]
            assert iterm2.rpc.ACTIVATE_RAISE_ALL_WINDOWS in call_kwargs['activate_app_opts']
            assert iterm2.rpc.ACTIVATE_IGNORING_OTHER_APPS not in call_kwargs['activate_app_opts']

    @pytest.mark.asyncio
    async def test_activate_raise_all_false(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await app.async_activate(raise_all_windows=False)
            call_kwargs = iterm2.rpc.async_activate.await_args[1]
            assert iterm2.rpc.ACTIVATE_RAISE_ALL_WINDOWS not in call_kwargs['activate_app_opts']

    @pytest.mark.asyncio
    async def test_activate_ignoring_other_apps(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await app.async_activate(ignoring_other_apps=True)
            call_kwargs = iterm2.rpc.async_activate.await_args[1]
            assert iterm2.rpc.ACTIVATE_IGNORING_OTHER_APPS in call_kwargs['activate_app_opts']

    @pytest.mark.asyncio
    async def test_activate_both_flags(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()):
            await app.async_activate(raise_all_windows=True, ignoring_other_apps=True)
            call_kwargs = iterm2.rpc.async_activate.await_args[1]
            opts = call_kwargs['activate_app_opts']
            assert iterm2.rpc.ACTIVATE_RAISE_ALL_WINDOWS in opts
            assert iterm2.rpc.ACTIVATE_IGNORING_OTHER_APPS in opts


class TestAppWindowsFromListSessionsResponse:
    """Tests for App._windows_from_list_sessions_response."""

    def test_empty_windows(self):
        conn = Mock()
        resp = Mock()
        resp.windows = []
        result = iterm2.app.App._windows_from_list_sessions_response(conn, resp)
        assert result == []

    def test_filters_none_windows(self):
        conn = Mock()
        win_proto = Mock()
        resp = Mock()
        resp.windows = [win_proto, None, win_proto]

        def side_effect(connection, window):
            if window is None:
                return None
            return Mock(window_id="w1", tabs=[])

        with patch.object(iterm2.window.Window, 'create_from_proto',
                          side_effect=side_effect):
            result = iterm2.app.App._windows_from_list_sessions_response(conn, resp)
            assert len(result) == 2

    def test_filters_none_from_create_from_proto(self):
        conn = Mock()
        win_proto = Mock()
        resp = Mock()
        resp.windows = [win_proto, win_proto, win_proto]

        with patch.object(iterm2.window.Window, 'create_from_proto',
                          side_effect=[Mock(window_id="w1", tabs=[]), None,
                                       Mock(window_id="w2", tabs=[])]):
            result = iterm2.app.App._windows_from_list_sessions_response(conn, resp)
            assert len(result) == 2


class TestAppBuriedSessionsFromListSessionsResponse:
    """Tests for App._buried_sessions_from_list_sessions_response."""

    def test_empty_buried(self):
        conn = Mock()
        resp = Mock()
        resp.buried_sessions = []
        result = iterm2.app.App._buried_sessions_from_list_sessions_response(conn, resp)
        assert result == []

    def test_creates_buried_sessions(self):
        conn = Mock()
        summary1 = Mock()
        summary1.unique_identifier = "buried1"
        summary1.title = "Buried 1"
        summary2 = Mock()
        summary2.unique_identifier = "buried2"
        summary2.title = "Buried 2"
        resp = Mock()
        resp.buried_sessions = [summary1, summary2]

        result = iterm2.app.App._buried_sessions_from_list_sessions_response(conn, resp)
        assert len(result) == 2
        assert result[0].session_id == "buried1"
        assert result[1].session_id == "buried2"
        assert result[0].buried is True
        assert result[1].buried is True


class TestAppPrettyStr:
    """Tests for App.pretty_str."""

    def test_empty_app(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        result = app.pretty_str()
        assert result == ""

    def test_single_window(self):
        conn = Mock()
        win = Mock()
        win.window_id = "w1"
        win.pretty_str = Mock(return_value="Window w1\n")
        app = iterm2.app.App(conn, [win], [])
        result = app.pretty_str()
        assert result == "Window w1\n"
        win.pretty_str.assert_called_once_with(indent="")

    def test_multiple_windows(self):
        conn = Mock()
        win1 = Mock()
        win1.pretty_str = Mock(return_value="Window w1\n")
        win2 = Mock()
        win2.pretty_str = Mock(return_value="Window w2\n")
        app = iterm2.app.App(conn, [win1, win2], [])
        result = app.pretty_str()
        assert result == "Window w1\n\nWindow w2\n"


class TestAppSearchForSessionId:
    """Tests for App._search_for_session_id."""

    def test_active_returns_proxy(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        result = app._search_for_session_id("active", False)
        assert result is not None
        assert repr(result).startswith("<ProxySession")

    def test_all_returns_proxy(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        result = app._search_for_session_id("all", False)
        assert result is not None
        assert repr(result).startswith("<ProxySession")

    def test_found_in_window_tab(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1", "s2"]])
        app = iterm2.app.App(conn, [win], [])
        result = app.get_session_by_id("s2", include_buried=False)
        assert result is not None
        assert result.session_id == "s2"

    def test_not_found_in_windows(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        app = iterm2.app.App(conn, [win], [])
        result = app.get_session_by_id("nonexistent", include_buried=False)
        assert result is None

    def test_found_in_buried_when_include_buried_true(self):
        conn = Mock()
        buried = _make_mock_session("buried1", buried=True)
        app = iterm2.app.App(conn, [], [buried])
        result = app.get_session_by_id("buried1", include_buried=True)
        assert result is buried

    def test_not_found_in_buried_when_include_buried_false(self):
        conn = Mock()
        buried = _make_mock_session("buried1", buried=True)
        app = iterm2.app.App(conn, [], [buried])
        result = app.get_session_by_id("buried1", include_buried=False)
        assert result is None

    def test_searches_windows_before_buried(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        buried = _make_mock_session("s1", buried=True)
        app = iterm2.app.App(conn, [win], [buried])
        result = app.get_session_by_id("s1", include_buried=True)
        # Should return the window session, not the buried one
        assert result.session_id == "s1"


class TestAppSearchForTabId:
    """Tests for App._search_for_tab_id."""

    def test_found(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1", "t2"])
        app = iterm2.app.App(conn, [win], [])
        result = app.get_tab_by_id("t2")
        assert result is not None
        assert result.tab_id == "t2"

    def test_not_found(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1"])
        app = iterm2.app.App(conn, [win], [])
        result = app.get_tab_by_id("nonexistent")
        assert result is None

    def test_searches_multiple_windows(self):
        conn = Mock()
        win1 = _make_mock_window("w1", tab_ids=["t1"])
        win2 = _make_mock_window("w2", tab_ids=["t2"])
        app = iterm2.app.App(conn, [win1, win2], [])
        result = app.get_tab_by_id("t2")
        assert result is not None
        assert result.tab_id == "t2"


class TestAppSearchForWindowId:
    """Tests for App._search_for_window_id."""

    def test_found(self):
        conn = Mock()
        win1 = _make_mock_window("w1")
        win2 = _make_mock_window("w2")
        app = iterm2.app.App(conn, [win1, win2], [])
        result = app.get_window_by_id("w2")
        assert result is not None
        assert result.window_id == "w2"

    def test_not_found(self):
        conn = Mock()
        win = _make_mock_window("w1")
        app = iterm2.app.App(conn, [win], [])
        result = app.get_window_by_id("nonexistent")
        assert result is None


class TestAppAsyncRefreshFocus:
    """Tests for App.async_refresh_focus."""

    @pytest.mark.asyncio
    async def test_refresh_focus(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])
        with patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)):
            await app.async_refresh_focus()
            iterm2.rpc.async_get_focus_info.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_refresh_focus_no_notifications(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        focus_resp = _make_focus_response_proto([])
        with patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)):
            await app.async_refresh_focus()


class TestAppAsyncRefreshBroadcastDomains:
    """Tests for App.async_refresh_broadcast_domains."""

    @pytest.mark.asyncio
    async def test_refresh_broadcast_domains(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        broadcast_resp = _make_broadcast_domains_response_proto([])
        with patch.object(iterm2.rpc, 'async_get_broadcast_domains',
                          new=AsyncMock(return_value=broadcast_resp)):
            await app.async_refresh_broadcast_domains()
            iterm2.rpc.async_get_broadcast_domains.assert_awaited_once()


class TestAppGetWindowForTab:
    """Tests for App.get_window_for_tab and _search_for_window_with_tab."""

    def test_found(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1", "t2"])
        app = iterm2.app.App(conn, [win], [])
        result = app.get_window_for_tab("t2")
        assert result is not None
        assert result.window_id == "w1"

    def test_not_found(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1"])
        app = iterm2.app.App(conn, [win], [])
        result = app.get_window_for_tab("nonexistent")
        assert result is None

    def test_searches_multiple_windows(self):
        conn = Mock()
        win1 = _make_mock_window("w1", tab_ids=["t1"])
        win2 = _make_mock_window("w2", tab_ids=["t2"])
        app = iterm2.app.App(conn, [win1, win2], [])
        result = app.get_window_for_tab("t2")
        assert result is not None
        assert result.window_id == "w2"


class TestAppAsyncRefresh:
    """Tests for App.async_refresh."""

    @pytest.mark.asyncio
    async def test_async_refresh(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        win = _make_mock_window("w1")
        app = iterm2.app.App(conn, [win], [])

        list_resp = _make_list_sessions_response_proto()
        list_wrapper = Mock()
        list_wrapper.list_sessions_response = list_resp

        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])

        with patch.object(iterm2.rpc, 'async_list_sessions',
                          new=AsyncMock(return_value=list_wrapper)), \
             patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)), \
             patch.object(iterm2.window.Window, 'create_from_proto',
                          return_value=Mock(window_id="w1", tabs=[])):
            await app.async_refresh()
            iterm2.rpc.async_list_sessions.assert_awaited_once()


class TestAppAsyncHandleLayoutChange:
    """Tests for App._async_handle_layout_change."""

    @pytest.mark.asyncio
    async def test_new_window_added(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        app = iterm2.app.App(conn, [], [])

        list_resp = _make_list_sessions_response_proto(window_id="new_w1")
        list_wrapper = Mock()
        list_wrapper.list_sessions_response = list_resp

        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])

        new_win = Mock(window_id="new_w1", tabs=[])
        with patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)), \
             patch.object(iterm2.window.Window, 'create_from_proto',
                          return_value=new_win):
            await app._async_handle_layout_change(conn, list_wrapper)
            assert len(app.windows) == 1
            assert app.windows[0].window_id == "new_w1"

    @pytest.mark.asyncio
    async def test_existing_window_updated(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        old_win = Mock(window_id="w1", tabs=[])
        old_win.update_from = Mock()
        app = iterm2.app.App(conn, [old_win], [])

        list_resp = _make_list_sessions_response_proto(window_id="w1")
        list_wrapper = Mock()
        list_wrapper.list_sessions_response = list_resp

        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])

        new_win = Mock(window_id="w1", tabs=[])
        with patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)), \
             patch.object(iterm2.window.Window, 'create_from_proto',
                          return_value=new_win):
            await app._async_handle_layout_change(conn, list_wrapper)
            old_win.update_from.assert_called_once_with(new_win)

    @pytest.mark.asyncio
    async def test_buried_sessions_handled(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        app = iterm2.app.App(conn, [], [])

        buried_summary = Mock()
        buried_summary.unique_identifier = "buried_new"
        buried_summary.title = "New Buried"

        list_resp = _make_list_sessions_response_proto(window_id="w1",
                                                        buried_session_ids=["buried_new"])
        # Override buried_sessions with our mock
        list_resp.buried_sessions = [buried_summary]
        list_wrapper = Mock()
        list_wrapper.list_sessions_response = list_resp

        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])

        new_win = Mock(window_id="w1", tabs=[])
        with patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)), \
             patch.object(iterm2.window.Window, 'create_from_proto',
                          return_value=new_win):
            await app._async_handle_layout_change(conn, list_wrapper)
            assert len(app.buried_sessions) == 1
            assert app.buried_sessions[0].session_id == "buried_new"


class TestAppAsyncFocusChange:
    """Tests for App._async_focus_change."""

    @pytest.mark.asyncio
    async def test_application_active_field(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "application_active")
        notif.application_active = True
        await app._async_focus_change(conn, notif)
        assert app.app_active is True

    @pytest.mark.asyncio
    async def test_window_field_sets_window_id(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "window")
        notif.window = Mock(
            window_id="w_focused",
            window_status=iterm2.api_pb2.FocusChangedNotification.Window.WindowStatus.Value(
                "TERMINAL_WINDOW_BECAME_KEY"))
        await app._async_focus_change(conn, notif)
        assert app.current_terminal_window_id == "w_focused"

    @pytest.mark.asyncio
    async def test_window_resigned_key_ignored(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        app.current_terminal_window_id = "w_existing"
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "window")
        notif.window = Mock(
            window_id="w_other",
            window_status=iterm2.api_pb2.FocusChangedNotification.Window.WindowStatus.Value(
                "TERMINAL_WINDOW_RESIGNED_KEY"))
        await app._async_focus_change(conn, notif)
        assert app.current_terminal_window_id == "w_existing"

    @pytest.mark.asyncio
    async def test_selected_tab_field_window_found(self):
        conn = Mock()
        win = _make_mock_window("w1", tab_ids=["t1", "t2"])
        app = iterm2.app.App(conn, [win], [])
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "selected_tab")
        notif.selected_tab = "t2"
        await app._async_focus_change(conn, notif)
        assert win.selected_tab_id == "t2"

    @pytest.mark.asyncio
    async def test_selected_tab_field_window_not_found_refreshes(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "selected_tab")
        notif.selected_tab = "nonexistent"
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            await app._async_focus_change(conn, notif)
            app.async_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_session_field_found(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        # Reconstruct so tab.all_sessions contains the same session object
        tab = win.tabs[0]
        sess_in_tab = tab.all_sessions[0]
        app = iterm2.app.App(conn, [win], [])
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "session")
        notif.session = "s1"
        await app._async_focus_change(conn, notif)
        assert tab.active_session_id == "s1"

    @pytest.mark.asyncio
    async def test_session_field_not_found_refreshes(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        notif = Mock()
        notif.HasField = Mock(side_effect=lambda f: f == "session")
        notif.session = "nonexistent"
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            await app._async_focus_change(conn, notif)
            app.async_refresh.assert_awaited_once()


class TestAppAsyncBroadcastDomainsChange:
    """Tests for App._async_broadcast_domains_change."""

    @pytest.mark.asyncio
    async def test_broadcast_domains_change(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        domain_proto = Mock()
        domain_proto.session_ids = ["s1"]
        notif = Mock()
        notif.broadcast_domains_changed = Mock(broadcast_domains=[domain_proto])
        await app._async_broadcast_domains_change(conn, notif)
        assert len(app.broadcast_domains) == 1


class TestAppSetBroadcastDomains:
    """Tests for App._set_broadcast_domains."""

    def test_set_broadcast_domains(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        domain_proto = Mock()
        domain_proto.session_ids = []
        app._set_broadcast_domains([domain_proto])
        assert len(app.broadcast_domains) == 1
        assert isinstance(app.broadcast_domains[0], iterm2.broadcast.BroadcastDomain)


class TestAppParseBroadcastDomains:
    """Tests for App.parse_broadcast_domains."""

    def test_empty_list(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        result = app.parse_broadcast_domains([])
        assert result == []

    def test_domain_with_resolved_session(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        # Replace the session in the tab with our mock
        win.tabs[0].all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        domain_proto = Mock()
        domain_proto.session_ids = ["s1"]
        result = app.parse_broadcast_domains([domain_proto])
        assert len(result) == 1
        bd = result[0]
        assert len(bd.sessions) == 1
        assert bd.sessions[0] is sess

    def test_domain_with_unresolved_session(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        domain_proto = Mock()
        domain_proto.session_ids = ["nonexistent"]
        result = app.parse_broadcast_domains([domain_proto])
        assert len(result) == 1
        bd = result[0]
        # The unresolved session won't appear in sessions list until resolved
        assert len(bd.sessions) == 0

    def test_multiple_domains(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        domain1 = Mock()
        domain1.session_ids = []
        domain2 = Mock()
        domain2.session_ids = []
        result = app.parse_broadcast_domains([domain1, domain2])
        assert len(result) == 2


class TestAppProperties:
    """Tests for App properties."""

    def test_current_window_none(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        assert app.current_window is None

    def test_current_window_found(self):
        conn = Mock()
        win = _make_mock_window("w1")
        app = iterm2.app.App(conn, [win], [])
        app.current_terminal_window_id = "w1"
        assert app.current_window is win

    def test_current_terminal_window_alias(self):
        conn = Mock()
        win = _make_mock_window("w1")
        app = iterm2.app.App(conn, [win], [])
        app.current_terminal_window_id = "w1"
        assert app.current_terminal_window is win

    def test_windows_property(self):
        conn = Mock()
        w1 = _make_mock_window("w1")
        w2 = _make_mock_window("w2")
        app = iterm2.app.App(conn, [w1, w2], [])
        assert len(app.windows) == 2

    def test_terminal_windows_aliases_windows(self):
        conn = Mock()
        w1 = _make_mock_window("w1")
        app = iterm2.app.App(conn, [w1], [])
        assert app.terminal_windows is app.windows

    def test_buried_sessions_property(self):
        conn = Mock()
        buried = _make_mock_session("b1", buried=True)
        app = iterm2.app.App(conn, [], [buried])
        assert len(app.buried_sessions) == 1
        assert app.buried_sessions[0] is buried

    def test_broadcast_domains_property(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        app._set_broadcast_domains([])
        assert app.broadcast_domains == []


class TestAppGetTabAndWindowForSession:
    """Tests for get_tab_and_window_for_session and get_window_and_tab_for_session."""

    def test_get_window_and_tab_for_session_found(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        w, t = app.get_window_and_tab_for_session(sess)
        assert w is win
        assert t is tab

    def test_get_window_and_tab_for_session_not_found(self):
        conn = Mock()
        sess = _make_mock_session("s_unknown")
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        app = iterm2.app.App(conn, [win], [])
        w, t = app.get_window_and_tab_for_session(sess)
        assert w is None
        assert t is None

    def test_get_tab_and_window_for_session_delegates(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        w, t = app.get_tab_and_window_for_session(sess)
        assert w is win
        assert t is tab

    def test_get_tab_and_window_returns_none_none(self):
        conn = Mock()
        sess = _make_mock_session("s_unknown")
        app = iterm2.app.App(conn, [], [])
        w, t = app.get_tab_and_window_for_session(sess)
        assert w is None
        assert t is None


class TestAppAsyncMoveSession:
    """Tests for App.async_move_session."""

    @pytest.mark.asyncio
    async def test_async_move_session(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        app = iterm2.app.App(conn, [], [])
        source = _make_mock_session("s1")
        dest = _make_mock_session("s2")
        with patch.object(iterm2.capabilities, 'check_supports_move_session'), \
             patch.object(iterm2.app, 'async_invoke_function', new=AsyncMock()):
            await app.async_move_session(source, dest, split_vertically=True, before=False)
            iterm2.app.async_invoke_function.assert_awaited_once()
            call_args = iterm2.app.async_invoke_function.await_args
            invocation = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]['invocation']
            assert "iterm2.move_session" in invocation
            assert "s1" in invocation
            assert "s2" in invocation


class TestAppAsyncSetVariable:
    """Tests for App.async_set_variable."""

    @pytest.mark.asyncio
    async def test_set_variable_success(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        resp = _make_variable_response_proto("OK")
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            await app.async_set_variable("user.myvar", "hello")
            iterm2.rpc.async_variable.assert_awaited_once()
            call_kwargs = iterm2.rpc.async_variable.await_args[1]
            assert call_kwargs['sets'] == [("user.myvar", '"hello"')]

    @pytest.mark.asyncio
    async def test_set_variable_error(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        resp = _make_variable_response_proto("SESSION_NOT_FOUND")
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await app.async_set_variable("user.myvar", "hello")


class TestAppAsyncGetVariable:
    """Tests for App.async_get_variable."""

    @pytest.mark.asyncio
    async def test_get_variable_success(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        resp = _make_variable_response_proto("OK", values=[json.dumps("myvalue")])
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            result = await app.async_get_variable("myvar")
            assert result == "myvalue"

    @pytest.mark.asyncio
    async def test_get_variable_error(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        resp = _make_variable_response_proto("SESSION_NOT_FOUND")
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await app.async_get_variable("myvar")

    @pytest.mark.asyncio
    async def test_get_variable_complex_value(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        complex_val = {"key": [1, 2, 3]}
        resp = _make_variable_response_proto("OK", values=[json.dumps(complex_val)])
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            result = await app.async_get_variable("myvar")
            assert result == complex_val


class TestAppAsyncGetTheme:
    """Tests for App.async_get_theme."""

    @pytest.mark.asyncio
    async def test_get_theme_single(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_get_variable', new=AsyncMock(return_value="dark")):
            result = await app.async_get_theme()
            assert result == ["dark"]

    @pytest.mark.asyncio
    async def test_get_theme_multiple(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_get_variable', new=AsyncMock(return_value="dark automatic")):
            result = await app.async_get_theme()
            assert result == ["dark", "automatic"]


class TestAppDelegateSession:
    """Tests for App Session delegate methods."""

    def test_session_delegate_get_tab(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        result = app.session_delegate_get_tab(sess)
        assert result is tab

    def test_session_delegate_get_tab_not_found(self):
        conn = Mock()
        sess = _make_mock_session("unknown")
        app = iterm2.app.App(conn, [], [])
        result = app.session_delegate_get_tab(sess)
        assert result is None

    def test_session_delegate_get_window(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        result = app.session_delegate_get_window(sess)
        assert result is win

    def test_session_delegate_get_window_not_found(self):
        conn = Mock()
        sess = _make_mock_session("unknown")
        app = iterm2.app.App(conn, [], [])
        result = app.session_delegate_get_window(sess)
        assert result is None

    @pytest.mark.asyncio
    async def test_session_delegate_create_session(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        app = iterm2.app.App(conn, [], [])
        new_sess = _make_mock_session("new_sess")
        with patch.object(app, 'async_refresh', new=AsyncMock()), \
             patch.object(app, 'get_session_by_id', return_value=new_sess):
            result = await app.session_delegate_create_session("new_sess")
            assert result is new_sess
            app.async_refresh.assert_awaited_once()


class TestAppDelegateTab:
    """Tests for App Tab delegate methods."""

    def test_tab_delegate_get_window(self):
        conn = Mock()
        tab = _make_mock_tab("t1")
        win = _make_mock_window("w1", tab_ids=["t1"])
        app = iterm2.app.App(conn, [win], [])
        result = app.tab_delegate_get_window(tab)
        assert result is win

    def test_tab_delegate_get_window_not_found(self):
        conn = Mock()
        tab = _make_mock_tab("nonexistent")
        app = iterm2.app.App(conn, [], [])
        result = app.tab_delegate_get_window(tab)
        assert result is None

    @pytest.mark.asyncio
    async def test_tab_delegate_get_window_by_id(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        win = _make_mock_window("w1")
        app = iterm2.app.App(conn, [win], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.tab_delegate_get_window_by_id("w1")
            assert result is win
            app.async_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_tab_delegate_get_window_by_id_not_found(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.tab_delegate_get_window_by_id("nonexistent")
            assert result is None


class TestAppDelegateWindow:
    """Tests for App Window delegate methods."""

    @pytest.mark.asyncio
    async def test_window_delegate_get_window_with_session_id_found(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.window_delegate_get_window_with_session_id("s1")
            assert result is win

    @pytest.mark.asyncio
    async def test_window_delegate_get_window_with_session_id_not_found(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.window_delegate_get_window_with_session_id("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_window_delegate_get_tab_by_id(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        win = _make_mock_window("w1", tab_ids=["t1"])
        app = iterm2.app.App(conn, [win], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.window_delegate_get_tab_by_id("t1")
            assert result is not None
            assert result.tab_id == "t1"

    @pytest.mark.asyncio
    async def test_window_delegate_get_tab_by_id_not_found(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.window_delegate_get_tab_by_id("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_window_delegate_get_tab_with_session_id_found(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.window_delegate_get_tab_with_session_id("s1")
            assert result is tab

    @pytest.mark.asyncio
    async def test_window_delegate_get_tab_with_session_id_not_found(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.window_delegate_get_tab_with_session_id("nonexistent")
            assert result is None


class TestAppDelegateTmux:
    """Tests for App tmux delegate methods."""

    @pytest.mark.asyncio
    async def test_tmux_delegate_async_get_window_for_tab_id(self):
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)
        win = _make_mock_window("w1", tab_ids=["t1"])
        app = iterm2.app.App(conn, [win], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.tmux_delegate_async_get_window_for_tab_id("t1")
            assert result is win

    @pytest.mark.asyncio
    async def test_tmux_delegate_async_get_window_for_tab_id_not_found(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with patch.object(app, 'async_refresh', new=AsyncMock()):
            result = await app.tmux_delegate_async_get_window_for_tab_id("nonexistent")
            assert result is None

    def test_tmux_delegate_get_session_by_id(self):
        conn = Mock()
        sess = _make_mock_session("s1")
        tab = _make_mock_tab("t1", ["s1"])
        win = _make_mock_window("w1", tab_ids=["t1"], session_ids_per_tab=[["s1"]])
        tab = win.tabs[0]
        tab.all_sessions = [sess]
        app = iterm2.app.App(conn, [win], [])
        result = app.tmux_delegate_get_session_by_id("s1")
        assert result is sess

    def test_tmux_delegate_get_session_by_id_not_found(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        result = app.tmux_delegate_get_session_by_id("nonexistent")
        assert result is None

    def test_tmux_delegate_get_connection(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        result = app.tmux_delegate_get_connection()
        assert result is conn


class TestAsyncGetApp:
    """Tests for async_get_app module function."""

    @pytest.mark.asyncio
    async def test_create_if_needed_true_creates_new(self):
        iterm2.app.App.instance = None
        conn = Mock()
        conn.iterm2_protocol_version = (1, 0)

        list_resp = _make_list_sessions_response_proto()
        list_wrapper = Mock()
        list_wrapper.list_sessions_response = list_resp
        notif = Mock()
        notif.HasField = Mock(return_value=False)
        focus_resp = _make_focus_response_proto([notif])
        broadcast_resp = _make_broadcast_domains_response_proto([])

        with patch.object(iterm2.rpc, 'async_list_sessions',
                          new=AsyncMock(return_value=list_wrapper)), \
             patch.object(iterm2.rpc, 'async_get_focus_info',
                          new=AsyncMock(return_value=focus_resp)), \
             patch.object(iterm2.rpc, 'async_get_broadcast_domains',
                          new=AsyncMock(return_value=broadcast_resp)), \
             patch.object(iterm2.window.Window, 'create_from_proto',
                          return_value=Mock(window_id="w1", tabs=[])), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_new_session_notification',
                          new=AsyncMock(return_value="tok")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_terminate_session_notification',
                          new=AsyncMock(return_value="tok")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_layout_change_notification',
                          new=AsyncMock(return_value="tok")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_focus_change_notification',
                          new=AsyncMock(return_value="tok")), \
             patch.object(iterm2.notifications,
                          'async_subscribe_to_broadcast_domains_change_notification',
                          new=AsyncMock(return_value="tok")):
            result = await iterm2.app.async_get_app(conn, create_if_needed=True)
            assert result is not None
            assert iterm2.app.App.instance is result

    @pytest.mark.asyncio
    async def test_create_if_needed_false_returns_none(self):
        iterm2.app.App.instance = None
        conn = Mock()
        result = await iterm2.app.async_get_app(conn, create_if_needed=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_existing_instance_refreshes(self):
        conn = Mock()
        existing_app = iterm2.app.App(conn, [], [])
        iterm2.app.App.instance = existing_app
        with patch.object(existing_app, 'async_refresh', new=AsyncMock()):
            result = await iterm2.app.async_get_app(conn, create_if_needed=True)
            assert result is existing_app
            existing_app.async_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_existing_instance_refreshes_with_false(self):
        conn = Mock()
        existing_app = iterm2.app.App(conn, [], [])
        iterm2.app.App.instance = existing_app
        with patch.object(existing_app, 'async_refresh', new=AsyncMock()):
            result = await iterm2.app.async_get_app(conn, create_if_needed=False)
            assert result is existing_app
            existing_app.async_refresh.assert_awaited_once()


class TestModuleAsyncGetVariable:
    """Tests for module-level async_get_variable."""

    @pytest.mark.asyncio
    async def test_success(self):
        conn = Mock()
        resp = _make_variable_response_proto("OK", values=[json.dumps(42)])
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            result = await iterm2.app.async_get_variable(conn, "myvar")
            assert result == 42

    @pytest.mark.asyncio
    async def test_error(self):
        conn = Mock()
        resp = _make_variable_response_proto("SESSION_NOT_FOUND")
        with patch.object(iterm2.rpc, 'async_variable', new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await iterm2.app.async_get_variable(conn, "myvar")


class TestModuleAsyncInvokeFunction:
    """Tests for module-level async_invoke_function."""

    @pytest.mark.asyncio
    async def test_success(self):
        conn = Mock()
        resp = _make_invoke_function_response_proto(
            which="success", json_result={"result": "ok"})
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)):
            result = await iterm2.app.async_invoke_function(
                conn, "myFunc()", timeout=30)
            assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_error_timeout(self):
        conn = Mock()
        resp = _make_invoke_function_response_proto(
            which="error", status_str="TIMEOUT", error_reason="Timed out")
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException, match="Timeout"):
                await iterm2.app.async_invoke_function(conn, "slowFunc()")

    @pytest.mark.asyncio
    async def test_error_failed(self):
        conn = Mock()
        resp = _make_invoke_function_response_proto(
            which="error", status_str="FAILED", error_reason="Function not found")
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException) as exc_info:
                await iterm2.app.async_invoke_function(conn, "missingFunc()")
            assert "FAILED" in str(exc_info.value)
            assert "Function not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_default_timeout(self):
        conn = Mock()
        resp = _make_invoke_function_response_proto(
            which="success", json_result=None)
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await iterm2.app.async_invoke_function(conn, "myFunc()")
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['timeout'] == -1


class TestAppGetSessionByIdEdgeCases:
    """Edge cases for get_session_by_id."""

    def test_assertion_on_empty_id(self):
        conn = Mock()
        app = iterm2.app.App(conn, [], [])
        with pytest.raises(AssertionError):
            app.get_session_by_id("", include_buried=False)

    def test_default_include_buried_true(self):
        conn = Mock()
        buried = _make_mock_session("buried1", buried=True)
        app = iterm2.app.App(conn, [], [buried])
        result = app.get_session_by_id("buried1")
        assert result is buried


class TestAppInvalidateApp:
    """Tests for invalidate_app."""

    def test_sets_instance_none(self):
        iterm2.app.App.instance = Mock()
        iterm2.app.invalidate_app()
        assert iterm2.app.App.instance is None

    def test_idempotent(self):
        iterm2.app.App.instance = None
        iterm2.app.invalidate_app()
        assert iterm2.app.App.instance is None


class TestAppCreateWindowException:
    """Tests for CreateWindowException alias."""

    def test_is_window_exception(self):
        assert iterm2.app.CreateWindowException is iterm2.window.CreateWindowException


class TestAppDelegateFactory:
    """Tests for DELEGATE_FACTORY assignments."""

    def test_window_delegate_factory_set(self):
        assert iterm2.window.DELEGATE_FACTORY is not None

    def test_tmux_delegate_factory_set(self):
        assert iterm2.tmux.DELEGATE_FACTORY is not None
