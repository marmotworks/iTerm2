"""Extended tests for iterm2.session module covering uncovered paths."""
import json
from unittest.mock import Mock, AsyncMock, patch

import pytest
import iterm2
import iterm2.session
import iterm2.util
import iterm2.api_pb2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_split_tree_link(session_id="sess-1", title="Test Session",
                          grid_width=80, grid_height=24):
    """Build a SplitTreeLink protobuf with a session."""
    link = iterm2.api_pb2.SplitTreeNode.SplitTreeLink()
    link.session.unique_identifier = session_id
    link.session.title = title
    link.session.grid_size.width = grid_width
    link.session.grid_size.height = grid_height
    link.session.frame.origin.x = 0
    link.session.frame.origin.y = 0
    link.session.frame.size.width = 800
    link.session.frame.size.height = 600
    return link


def _make_session_summary(session_id="sess-buried", title="Buried"):
    """Build a SessionSummary protobuf."""
    summary = iterm2.api_pb2.SessionSummary()
    summary.unique_identifier = session_id
    summary.title = title
    return summary


def _mock_connection():
    """Return a minimal mock Connection."""
    conn = Mock()
    conn.iterm2_protocol_version = (1, 20)
    return conn


def _make_session_from_link(conn=None, session_id="sess-1"):
    """Convenience: create a Session from a SplitTreeLink."""
    if conn is None:
        conn = _mock_connection()
    link = _make_split_tree_link(session_id=session_id)
    return iterm2.session.Session(conn, link)


def _make_session_from_summary(conn=None, session_id="sess-buried"):
    """Convenience: create a Session from a SessionSummary."""
    if conn is None:
        conn = _mock_connection()
    summary = _make_session_summary(session_id=session_id)
    return iterm2.session.Session(conn, None, summary=summary)


# ---------------------------------------------------------------------------
# Splitter.from_node
# ---------------------------------------------------------------------------

class TestSplitterFromNode:
    """Tests for Splitter.from_node."""

    def test_from_node_single_session(self):
        conn = _mock_connection()
        node = iterm2.api_pb2.SplitTreeNode()
        node.vertical = True
        link = iterm2.api_pb2.SplitTreeNode.SplitTreeLink()
        link.session.unique_identifier = "s1"
        link.session.title = "S1"
        link.session.grid_size.width = 80
        link.session.grid_size.height = 24
        node.links.append(link)

        splitter = iterm2.session.Splitter.from_node(node, conn)
        assert splitter.vertical is True
        assert len(splitter.children) == 1
        assert isinstance(splitter.children[0], iterm2.session.Session)
        assert splitter.children[0].session_id == "s1"

    def test_from_node_nested_splitter(self):
        conn = _mock_connection()
        node = iterm2.api_pb2.SplitTreeNode()
        node.vertical = False

        # First link: a session
        link1 = iterm2.api_pb2.SplitTreeNode.SplitTreeLink()
        link1.session.unique_identifier = "s1"
        link1.session.title = "S1"
        link1.session.grid_size.width = 80
        link1.session.grid_size.height = 24
        node.links.append(link1)

        # Second link: a nested node
        sublink = iterm2.api_pb2.SplitTreeNode.SplitTreeLink()
        subnode = iterm2.api_pb2.SplitTreeNode()
        subnode.vertical = True
        sub_sess = iterm2.api_pb2.SplitTreeNode.SplitTreeLink()
        sub_sess.session.unique_identifier = "s2"
        sub_sess.session.title = "S2"
        sub_sess.session.grid_size.width = 40
        sub_sess.session.grid_size.height = 12
        subnode.links.append(sub_sess)
        sublink.node.CopyFrom(subnode)
        node.links.append(sublink)

        splitter = iterm2.session.Splitter.from_node(node, conn)
        assert splitter.vertical is False
        assert len(splitter.children) == 2
        assert isinstance(splitter.children[0], iterm2.session.Session)
        assert isinstance(splitter.children[1], iterm2.session.Splitter)
        assert splitter.children[1].vertical is True
        assert len(splitter.children[1].children) == 1
        assert splitter.children[1].children[0].session_id == "s2"

    def test_from_node_empty(self):
        conn = _mock_connection()
        node = iterm2.api_pb2.SplitTreeNode()
        node.vertical = False
        splitter = iterm2.session.Splitter.from_node(node, conn)
        assert splitter.vertical is False
        assert len(splitter.children) == 0


# ---------------------------------------------------------------------------
# Splitter.sessions
# ---------------------------------------------------------------------------

class TestSplitterSessions:
    """Tests for Splitter.sessions property."""

    def test_sessions_direct_children(self):
        root = iterm2.session.Splitter()
        s1 = _make_session_from_link(session_id="s1")
        s2 = _make_session_from_link(session_id="s2")
        root.add_child(s1)
        root.add_child(s2)
        sessions = root.sessions
        assert len(sessions) == 2
        assert sessions[0].session_id == "s1"
        assert sessions[1].session_id == "s2"

    def test_sessions_nested(self):
        root = iterm2.session.Splitter(vertical=False)
        s1 = _make_session_from_link(session_id="s1")
        inner = iterm2.session.Splitter(vertical=True)
        s2 = _make_session_from_link(session_id="s2")
        s3 = _make_session_from_link(session_id="s3")
        inner.add_child(s2)
        inner.add_child(s3)
        root.add_child(s1)
        root.add_child(inner)
        sessions = root.sessions
        assert len(sessions) == 3
        ids = [s.session_id for s in sessions]
        assert "s1" in ids
        assert "s2" in ids
        assert "s3" in ids

    def test_sessions_deeply_nested(self):
        root = iterm2.session.Splitter()
        level1 = iterm2.session.Splitter()
        level2 = iterm2.session.Splitter()
        s = _make_session_from_link(session_id="deep")
        level2.add_child(s)
        level1.add_child(level2)
        root.add_child(level1)
        assert len(root.sessions) == 1
        assert root.sessions[0].session_id == "deep"


# ---------------------------------------------------------------------------
# Splitter.update_session
# ---------------------------------------------------------------------------

class TestSplitterUpdateSession:
    """Tests for Splitter.update_session."""

    def test_update_at_top_level(self):
        root = iterm2.session.Splitter()
        old = _make_session_from_link(session_id="s1")
        new = _make_session_from_link(session_id="s1")
        root.add_child(old)
        result = root.update_session(new)
        assert result is True
        assert root.children[0] is new

    def test_update_in_nested_splitter(self):
        root = iterm2.session.Splitter()
        s1 = _make_session_from_link(session_id="s1")
        inner = iterm2.session.Splitter()
        old = _make_session_from_link(session_id="s2")
        inner.add_child(old)
        root.add_child(s1)
        root.add_child(inner)
        new = _make_session_from_link(session_id="s2")
        result = root.update_session(new)
        assert result is True
        assert inner.children[0] is new

    def test_update_not_found(self):
        root = iterm2.session.Splitter()
        s1 = _make_session_from_link(session_id="s1")
        root.add_child(s1)
        other = _make_session_from_link(session_id="s99")
        result = root.update_session(other)
        assert result is False

    def test_update_preserves_order(self):
        root = iterm2.session.Splitter()
        s1 = _make_session_from_link(session_id="s1")
        s2 = _make_session_from_link(session_id="s2")
        s3 = _make_session_from_link(session_id="s3")
        root.add_child(s1)
        root.add_child(s2)
        root.add_child(s3)
        new_s2 = _make_session_from_link(session_id="s2")
        root.update_session(new_s2)
        assert root.children[0] is s1
        assert root.children[1] is new_s2
        assert root.children[2] is s3


# ---------------------------------------------------------------------------
# Splitter.to_protobuf with children
# ---------------------------------------------------------------------------

class TestSplitterToProtobuf:
    """Tests for Splitter.to_protobuf with children."""

    def test_to_protobuf_with_session_child(self):
        root = iterm2.session.Splitter(vertical=True)
        s = _make_session_from_link(session_id="s1")
        root.add_child(s)
        proto = root.to_protobuf()
        assert proto.vertical is True
        assert len(proto.links) == 1
        assert proto.links[0].HasField("session")
        assert proto.links[0].session.unique_identifier == "s1"

    def test_to_protobuf_with_splitter_child(self):
        root = iterm2.session.Splitter(vertical=False)
        inner = iterm2.session.Splitter(vertical=True)
        root.add_child(inner)
        proto = root.to_protobuf()
        assert proto.vertical is False
        assert len(proto.links) == 1
        assert proto.links[0].HasField("node")
        assert proto.links[0].node.vertical is True

    def test_to_protobuf_mixed_children(self):
        root = iterm2.session.Splitter()
        s1 = _make_session_from_link(session_id="s1")
        inner = iterm2.session.Splitter(vertical=True)
        s2 = _make_session_from_link(session_id="s2")
        inner.add_child(s2)
        root.add_child(s1)
        root.add_child(inner)
        proto = root.to_protobuf()
        assert len(proto.links) == 2
        assert proto.links[0].HasField("session")
        assert proto.links[1].HasField("node")


# ---------------------------------------------------------------------------
# Session.active_proxy / Session.all_proxy
# ---------------------------------------------------------------------------

class TestSessionProxies:
    """Tests for Session.active_proxy and Session.all_proxy."""

    def test_active_proxy(self):
        conn = _mock_connection()
        proxy = iterm2.session.Session.active_proxy(conn)
        assert isinstance(proxy, iterm2.session.ProxySession)
        assert proxy.session_id == "active"

    def test_all_proxy(self):
        conn = _mock_connection()
        proxy = iterm2.session.Session.all_proxy(conn)
        assert isinstance(proxy, iterm2.session.ProxySession)
        assert proxy.session_id == "all"


# ---------------------------------------------------------------------------
# Session.__init__ with link parameter
# ---------------------------------------------------------------------------

class TestSessionInitLink:
    """Tests for Session.__init__ with link parameter."""

    def test_init_link_all_fields(self):
        conn = _mock_connection()
        link = _make_split_tree_link(
            session_id="sess-abc",
            title="My Terminal",
            grid_width=120,
            grid_height=40,
        )
        sess = iterm2.session.Session(conn, link)
        assert sess.session_id == "sess-abc"
        assert sess.name == "My Terminal"
        assert sess.buried is False
        assert sess.grid_size.width == 120
        assert sess.grid_size.height == 40
        assert sess.preferred_size.width == 120
        assert sess.preferred_size.height == 40

    def test_init_link_stores_connection(self):
        conn = _mock_connection()
        link = _make_split_tree_link()
        sess = iterm2.session.Session(conn, link)
        assert sess.connection is conn


# ---------------------------------------------------------------------------
# Session.__init__ with summary parameter
# ---------------------------------------------------------------------------

class TestSessionInitSummary:
    """Tests for Session.__init__ with summary parameter."""

    def test_init_summary_buried(self):
        conn = _mock_connection()
        summary = _make_session_summary(session_id="buried-1", title="Buried Session")
        sess = iterm2.session.Session(conn, None, summary=summary)
        assert sess.session_id == "buried-1"
        assert sess.name == "Buried Session"
        assert sess.buried is True
        assert sess.frame is None

    def test_init_summary_grid_size_none(self):
        conn = _mock_connection()
        summary = _make_session_summary()
        sess = iterm2.session.Session(conn, None, summary=summary)
        assert sess.grid_size is None


# ---------------------------------------------------------------------------
# Session.__repr__
# ---------------------------------------------------------------------------

class TestSessionRepr:
    """Tests for Session.__repr__."""

    def test_repr_link_session(self):
        sess = _make_session_from_link(session_id="s-42")
        sess.name = "myterm"
        r = repr(sess)
        assert "Session" in r
        assert "myterm" in r
        assert "s-42" in r

    def test_repr_summary_session(self):
        sess = _make_session_from_summary(session_id="b-7")
        sess.name = "buried"
        r = repr(sess)
        assert "Session" in r
        assert "buried" in r
        assert "b-7" in r


# ---------------------------------------------------------------------------
# Session.to_session_summary_protobuf
# ---------------------------------------------------------------------------

class TestSessionToSessionSummaryProtobuf:
    """Tests for Session.to_session_summary_protobuf."""

    def test_to_session_summary_protobuf(self):
        sess = _make_session_from_link(session_id="proto-sess")
        proto = sess.to_session_summary_protobuf()
        assert proto.unique_identifier == "proto-sess"
        assert proto.grid_size.width == 80
        assert proto.grid_size.height == 24


# ---------------------------------------------------------------------------
# Session.update_from
# ---------------------------------------------------------------------------

class TestSessionUpdateFrom:
    """Tests for Session.update_from."""

    def test_update_from_copies_fields(self):
        s1 = _make_session_from_link(session_id="s1")
        s2 = _make_session_from_link(session_id="s2")
        s2.name = "Updated Name"
        s1.update_from(s2)
        assert s1.name == "Updated Name"
        assert s1.grid_size.width == s2.grid_size.width
        assert s1.grid_size.height == s2.grid_size.height


# ---------------------------------------------------------------------------
# Session.pretty_str
# ---------------------------------------------------------------------------

class TestSessionPrettyStr:
    """Tests for Session.pretty_str."""

    def test_pretty_str_link_session(self):
        sess = _make_session_from_link(session_id="ps-1")
        sess.name = "Pretty"
        result = sess.pretty_str("")
        assert "Pretty" in result
        assert "ps-1" in result
        assert result.endswith("\n")

    def test_pretty_str_with_indent(self):
        sess = _make_session_from_link(session_id="ps-2")
        sess.name = "Indented"
        result = sess.pretty_str("  ")
        assert result.startswith("  Session")

    def test_pretty_str_summary_session(self):
        sess = _make_session_from_summary(session_id="ps-b")
        sess.name = "Buried"
        result = sess.pretty_str("")
        assert "Buried" in result
        assert "[Undefined]" in result  # frame is None


# ---------------------------------------------------------------------------
# Session.tab / Session.get_tab
# ---------------------------------------------------------------------------

class TestSessionTab:
    """Tests for Session.tab and Session.get_tab."""

    def test_tab_no_delegate(self):
        sess = _make_session_from_link()
        assert iterm2.session.Session.delegate is None
        result = sess.tab
        assert result is None

    def test_tab_with_delegate(self):
        sess = _make_session_from_link()
        mock_tab = Mock()
        delegate = Mock()
        delegate.session_delegate_get_tab = Mock(return_value=mock_tab)
        iterm2.session.Session.delegate = delegate
        try:
            result = sess.tab
            assert result is mock_tab
            delegate.session_delegate_get_tab.assert_called_once_with(sess)
        finally:
            iterm2.session.Session.delegate = None

    def test_get_tab_no_delegate(self):
        sess = _make_session_from_link()
        assert iterm2.session.Session.get_tab(sess) is None

    def test_get_tab_with_delegate(self):
        sess = _make_session_from_link()
        mock_tab = Mock()
        delegate = Mock()
        delegate.session_delegate_get_tab = Mock(return_value=mock_tab)
        iterm2.session.Session.delegate = delegate
        try:
            result = iterm2.session.Session.get_tab(sess)
            assert result is mock_tab
        finally:
            iterm2.session.Session.delegate = None


# ---------------------------------------------------------------------------
# Session.get_window / Session.window
# ---------------------------------------------------------------------------

class TestSessionWindow:
    """Tests for Session.get_window and Session.window property."""

    def test_window_no_delegate(self):
        sess = _make_session_from_link()
        assert iterm2.session.Session.delegate is None
        result = sess.window
        assert result is None

    def test_window_with_delegate(self):
        sess = _make_session_from_link()
        mock_window = Mock()
        delegate = Mock()
        delegate.session_delegate_get_window = Mock(return_value=mock_window)
        iterm2.session.Session.delegate = delegate
        try:
            result = sess.window
            assert result is mock_window
        finally:
            iterm2.session.Session.delegate = None

    def test_get_window_no_delegate(self):
        sess = _make_session_from_link()
        assert iterm2.session.Session.get_window(sess) is None

    def test_get_window_with_delegate(self):
        sess = _make_session_from_link()
        mock_window = Mock()
        delegate = Mock()
        delegate.session_delegate_get_window = Mock(return_value=mock_window)
        iterm2.session.Session.delegate = delegate
        try:
            result = iterm2.session.Session.get_window(sess)
            assert result is mock_window
        finally:
            iterm2.session.Session.delegate = None


# ---------------------------------------------------------------------------
# Session.preferred_size
# ---------------------------------------------------------------------------

class TestSessionPreferredSize:
    """Tests for Session.preferred_size getter/setter."""

    def test_preferred_size_default_equals_grid_size(self):
        sess = _make_session_from_link()
        assert sess.preferred_size.width == sess.grid_size.width
        assert sess.preferred_size.height == sess.grid_size.height

    def test_preferred_size_setter(self):
        sess = _make_session_from_link()
        new_size = iterm2.util.Size(100, 50)
        sess.preferred_size = new_size
        assert sess.preferred_size.width == 100
        assert sess.preferred_size.height == 50

    def test_preferred_size_independent_of_grid_size(self):
        sess = _make_session_from_link()
        original_grid = sess.grid_size
        sess.preferred_size = iterm2.util.Size(200, 100)
        assert sess.grid_size.width == original_grid.width
        assert sess.preferred_size.width == 200


# ---------------------------------------------------------------------------
# Session.session_id
# ---------------------------------------------------------------------------

class TestSessionId:
    """Tests for Session.session_id property."""

    def test_session_id_from_link(self):
        sess = _make_session_from_link(session_id="unique-123")
        assert sess.session_id == "unique-123"

    def test_session_id_from_summary(self):
        sess = _make_session_from_summary(session_id="buried-456")
        assert sess.session_id == "buried-456"


# ---------------------------------------------------------------------------
# Session.async_get_screen_contents
# ---------------------------------------------------------------------------

class TestAsyncGetScreenContents:
    """Tests for Session.async_get_screen_contents."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="sc-1")
        resp = Mock()
        resp.get_buffer_response = Mock(
            status=iterm2.api_pb2.GetBufferResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_get_screen_contents',
                          new=AsyncMock(return_value=resp)):
            with patch.object(iterm2.screen, 'ScreenContents', return_value=Mock()) as mock_sc:
                result = await sess.async_get_screen_contents()
                assert result is mock_sc.return_value
                iterm2.rpc.async_get_screen_contents.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="sc-1")
        resp = Mock()
        resp.get_buffer_response = Mock(
            status=iterm2.api_pb2.GetBufferResponse.Status.Value("SESSION_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_get_screen_contents',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_get_screen_contents()


# ---------------------------------------------------------------------------
# Session.async_get_contents
# ---------------------------------------------------------------------------

class TestAsyncGetContents:
    """Tests for Session.async_get_contents."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="gc-1")
        resp = Mock()
        resp.get_buffer_response = Mock(
            status=iterm2.api_pb2.GetBufferResponse.Status.Value("OK")
        )
        mock_contents = Mock()
        mock_contents.number_of_lines = 3
        mock_line = Mock()
        mock_contents.line = Mock(return_value=mock_line)

        with patch.object(iterm2.rpc, 'async_get_screen_contents',
                          new=AsyncMock(return_value=resp)):
            with patch.object(iterm2.screen, 'ScreenContents',
                              return_value=mock_contents):
                result = await sess.async_get_contents(0, 10)
                assert len(result) == 3
                assert result[0] is mock_line

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="gc-1")
        resp = Mock()
        resp.get_buffer_response = Mock(
            status=iterm2.api_pb2.GetBufferResponse.Status.Value("SESSION_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_get_screen_contents',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_get_contents(0, 10)


# ---------------------------------------------------------------------------
# Session.get_screen_streamer
# ---------------------------------------------------------------------------

class TestGetScreenStreamer:
    """Tests for Session.get_screen_streamer."""

    def test_want_contents_true(self):
        sess = _make_session_from_link(session_id="ss-1")
        with patch.object(iterm2.screen, 'ScreenStreamer') as mock_ss:
            streamer = sess.get_screen_streamer(want_contents=True)
            mock_ss.assert_called_once()
            call_kwargs = mock_ss.call_args[1]
            assert call_kwargs['want_contents'] is True

    def test_want_contents_false(self):
        sess = _make_session_from_link(session_id="ss-1")
        with patch.object(iterm2.screen, 'ScreenStreamer') as mock_ss:
            streamer = sess.get_screen_streamer(want_contents=False)
            call_kwargs = mock_ss.call_args[1]
            assert call_kwargs['want_contents'] is False


# ---------------------------------------------------------------------------
# Session.async_send_text
# ---------------------------------------------------------------------------

class TestAsyncSendText:
    """Tests for Session.async_send_text."""

    @pytest.mark.asyncio
    async def test_default_suppress_broadcast(self):
        sess = _make_session_from_link(session_id="st-1")
        with patch.object(iterm2.rpc, 'async_send_text', new=AsyncMock()) as mock_rpc:
            await sess.async_send_text("hello")
            call_args = mock_rpc.await_args[0]
            assert call_args[3] is False  # suppress_broadcast (positional)

    @pytest.mark.asyncio
    async def test_suppress_broadcast_true(self):
        sess = _make_session_from_link(session_id="st-1")
        with patch.object(iterm2.rpc, 'async_send_text', new=AsyncMock()) as mock_rpc:
            await sess.async_send_text("hello", suppress_broadcast=True)
            call_args = mock_rpc.await_args[0]
            assert call_args[3] is True  # suppress_broadcast (positional)


# ---------------------------------------------------------------------------
# Session.async_split_pane
# ---------------------------------------------------------------------------

class TestAsyncSplitPane:
    """Tests for Session.async_split_pane."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="sp-1")
        resp = Mock()
        resp.split_pane_response = Mock(
            status=iterm2.api_pb2.SplitPaneResponse.Status.Value("OK"),
            session_id=["new-sess-id"]
        )
        new_sess = Mock()
        delegate = Mock()
        delegate.session_delegate_create_session = AsyncMock(return_value=new_sess)
        iterm2.session.Session.delegate = delegate
        try:
            with patch.object(iterm2.rpc, 'async_split_pane',
                              new=AsyncMock(return_value=resp)):
                result = await sess.async_split_pane(vertical=True, before=False)
                assert result is new_sess
                delegate.session_delegate_create_session.assert_awaited_once_with(
                    "new-sess-id"
                )
        finally:
            iterm2.session.Session.delegate = None

    @pytest.mark.asyncio
    async def test_error_status(self):
        sess = _make_session_from_link(session_id="sp-1")
        resp = Mock()
        resp.split_pane_response = Mock(
            status=iterm2.api_pb2.SplitPaneResponse.Status.Value("CANNOT_SPLIT")
        )
        with patch.object(iterm2.rpc, 'async_split_pane',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.session.SplitPaneException):
                await sess.async_split_pane()

    @pytest.mark.asyncio
    async def test_delegate_returns_none(self):
        sess = _make_session_from_link(session_id="sp-1")
        resp = Mock()
        resp.split_pane_response = Mock(
            status=iterm2.api_pb2.SplitPaneResponse.Status.Value("OK"),
            session_id=["new-sess-id"]
        )
        delegate = Mock()
        delegate.session_delegate_create_session = AsyncMock(return_value=None)
        iterm2.session.Session.delegate = delegate
        try:
            with patch.object(iterm2.rpc, 'async_split_pane',
                              new=AsyncMock(return_value=resp)):
                with pytest.raises(iterm2.session.SplitPaneException,
                                   match="No such session"):
                    await sess.async_split_pane()
        finally:
            iterm2.session.Session.delegate = None

    @pytest.mark.asyncio
    async def test_with_profile_customizations(self):
        sess = _make_session_from_link(session_id="sp-1")
        resp = Mock()
        resp.split_pane_response = Mock(
            status=iterm2.api_pb2.SplitPaneResponse.Status.Value("OK"),
            session_id=["new-sess-id"]
        )
        new_sess = Mock()
        custom = Mock()
        custom.values = {"fontSize": "14"}
        delegate = Mock()
        delegate.session_delegate_create_session = AsyncMock(return_value=new_sess)
        iterm2.session.Session.delegate = delegate
        try:
            with patch.object(iterm2.rpc, 'async_split_pane',
                              new=AsyncMock(return_value=resp)) as mock_rpc:
                await sess.async_split_pane(profile_customizations=custom)
                call_kwargs = mock_rpc.await_args[1]
                assert call_kwargs['profile_customizations'] == {"fontSize": "14"}
        finally:
            iterm2.session.Session.delegate = None


# ---------------------------------------------------------------------------
# Session.async_set_profile_properties
# ---------------------------------------------------------------------------

class TestAsyncSetProfileProperties:
    """Tests for Session.async_set_profile_properties."""

    @pytest.mark.asyncio
    async def test_multiple_capabilities(self):
        sess = _make_session_from_link(session_id="pp-1")
        profile = Mock()
        profile.values = {"fontSize": json.dumps(14), "tabColor": json.dumps("#ff0000")}
        resp = Mock()
        resp.set_profile_property_response = Mock(
            status=iterm2.api_pb2.SetProfilePropertyResponse.Status.Value("OK")
        )
        with patch.object(iterm2.capabilities,
                          'supports_multiple_set_profile_properties',
                          return_value=True):
            with patch.object(iterm2.rpc, 'async_set_profile_properties_json',
                              new=AsyncMock(return_value=resp)) as mock_rpc:
                await sess.async_set_profile_properties(profile)
                mock_rpc.assert_awaited_once()
                call_args = mock_rpc.await_args[0]
                assignments = call_args[2]
                keys = [a[0] for a in assignments]
                assert "fontSize" in keys
                assert "tabColor" in keys

    @pytest.mark.asyncio
    async def test_single_capability_legacy(self):
        sess = _make_session_from_link(session_id="pp-1")
        profile = Mock()
        profile.values = {"fontSize": json.dumps(14)}
        resp = Mock()
        resp.set_profile_property_response = Mock(
            status=iterm2.api_pb2.SetProfilePropertyResponse.Status.Value("OK")
        )
        with patch.object(iterm2.capabilities,
                          'supports_multiple_set_profile_properties',
                          return_value=False):
            with patch.object(iterm2.rpc, 'async_set_profile_property_json',
                              new=AsyncMock(return_value=resp)) as mock_rpc:
                await sess.async_set_profile_properties(profile)
                assert mock_rpc.await_count == 1

    @pytest.mark.asyncio
    async def test_error_multiple(self):
        sess = _make_session_from_link(session_id="pp-1")
        profile = Mock()
        profile.values = {"fontSize": json.dumps(14)}
        resp = Mock()
        resp.set_profile_property_response = Mock(
            status=iterm2.api_pb2.SetProfilePropertyResponse.Status.Value("REQUEST_MALFORMED")
        )
        with patch.object(iterm2.capabilities,
                          'supports_multiple_set_profile_properties',
                          return_value=True):
            with patch.object(iterm2.rpc, 'async_set_profile_properties_json',
                              new=AsyncMock(return_value=resp)):
                with pytest.raises(iterm2.rpc.RPCException):
                    await sess.async_set_profile_properties(profile)


# ---------------------------------------------------------------------------
# Session.async_get_profile
# ---------------------------------------------------------------------------

class TestAsyncGetProfile:
    """Tests for Session.async_get_profile."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="gp-1")
        resp = Mock()
        resp.get_profile_property_response = Mock(
            status=iterm2.api_pb2.GetProfilePropertyResponse.Status.Value("OK"),
            properties={}
        )
        with patch.object(iterm2.rpc, 'async_get_profile',
                          new=AsyncMock(return_value=resp)):
            with patch.object(iterm2.profile, 'Profile') as mock_profile:
                result = await sess.async_get_profile()
                assert result is mock_profile.return_value

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="gp-1")
        resp = Mock()
        resp.get_profile_property_response = Mock(
            status=iterm2.api_pb2.GetProfilePropertyResponse.Status.Value(
                "SESSION_NOT_FOUND"
            )
        )
        with patch.object(iterm2.rpc, 'async_get_profile',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_get_profile()


# ---------------------------------------------------------------------------
# Session.async_set_profile
# ---------------------------------------------------------------------------

class TestAsyncSetProfile:
    """Tests for Session.async_set_profile."""

    @pytest.mark.asyncio
    async def test_delegates_to_set_profile_properties(self):
        sess = _make_session_from_link(session_id="sp-1")
        profile = Mock()
        profile.local_write_only_copy = Mock()
        with patch.object(sess, 'async_set_profile_properties',
                          new=AsyncMock()) as mock_set:
            await sess.async_set_profile(profile)
            mock_set.assert_awaited_once_with(profile.local_write_only_copy)


# ---------------------------------------------------------------------------
# Session.async_inject
# ---------------------------------------------------------------------------

class TestAsyncInject:
    """Tests for Session.async_inject."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="inj-1")
        resp = Mock()
        resp.inject_response = Mock(
            status=[iterm2.api_pb2.InjectResponse.Status.Value("OK")]
        )
        with patch.object(iterm2.rpc, 'async_inject',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_inject(b"\x1b[2J")
            call_args = mock_rpc.await_args[0]
            assert call_args[1] == b"\x1b[2J"  # data (positional)
            assert call_args[2] == ["inj-1"]  # sessions (positional)

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="inj-1")
        resp = Mock()
        resp.inject_response = Mock(
            status=[iterm2.api_pb2.InjectResponse.Status.Value("SESSION_NOT_FOUND")]
        )
        with patch.object(iterm2.rpc, 'async_inject',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_inject(b"hello")


# ---------------------------------------------------------------------------
# Session.async_activate
# ---------------------------------------------------------------------------

class TestAsyncActivate:
    """Tests for Session.async_activate."""

    @pytest.mark.asyncio
    async def test_defaults(self):
        sess = _make_session_from_link(session_id="act-1")
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()) as mock_rpc:
            await sess.async_activate()
            call_args = mock_rpc.await_args[0]
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['session_id'] == "act-1"
            assert call_args[2] is True  # select_tab
            assert call_args[3] is True  # order_window_front

    @pytest.mark.asyncio
    async def test_custom_params(self):
        sess = _make_session_from_link(session_id="act-1")
        with patch.object(iterm2.rpc, 'async_activate', new=AsyncMock()) as mock_rpc:
            await sess.async_activate(select_tab=False, order_window_front=False)
            call_args = mock_rpc.await_args[0]
            assert call_args[2] is False
            assert call_args[3] is False


# ---------------------------------------------------------------------------
# Session.async_set_variable / async_get_variable
# ---------------------------------------------------------------------------

class TestSessionVariables:
    """Tests for Session async variable methods."""

    @pytest.mark.asyncio
    async def test_async_set_variable_ok(self):
        sess = _make_session_from_link(session_id="var-1")
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_variable',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_set_variable("user.myvar", {"key": "val"})
            call_args = mock_rpc.await_args[0]
            assert call_args[1] == "var-1"  # session_id (positional)
            sets = call_args[2]
            assert sets[0][0] == "user.myvar"
            assert json.loads(sets[0][1]) == {"key": "val"}

    @pytest.mark.asyncio
    async def test_async_set_variable_error(self):
        sess = _make_session_from_link(session_id="var-1")
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("SESSION_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_variable',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_set_variable("user.var", "val")

    @pytest.mark.asyncio
    async def test_async_get_variable_ok(self):
        sess = _make_session_from_link(session_id="var-1")
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("OK"),
            values=[json.dumps("hello")]
        )
        with patch.object(iterm2.rpc, 'async_variable',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            result = await sess.async_get_variable("user.myvar")
            assert result == "hello"
            call_args = mock_rpc.await_args[0]
            gets = call_args[3]
            assert gets[0] == "user.myvar"

    @pytest.mark.asyncio
    async def test_async_get_variable_error(self):
        sess = _make_session_from_link(session_id="var-1")
        resp = Mock()
        resp.variable_response = Mock(
            status=iterm2.api_pb2.VariableResponse.Status.Value("SESSION_NOT_FOUND")
        )
        with patch.object(iterm2.rpc, 'async_variable',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_get_variable("user.var")


# ---------------------------------------------------------------------------
# Session.async_restart
# ---------------------------------------------------------------------------

class TestAsyncRestart:
    """Tests for Session.async_restart."""

    @pytest.mark.asyncio
    async def test_success_default(self):
        sess = _make_session_from_link(session_id="rst-1")
        resp = Mock()
        resp.restart_session_response = Mock(
            status=iterm2.api_pb2.RestartSessionResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_restart_session',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_restart()
            call_args = mock_rpc.await_args[0]
            assert call_args[2] is False  # only_if_exited (positional)

    @pytest.mark.asyncio
    async def test_success_only_if_exited(self):
        sess = _make_session_from_link(session_id="rst-1")
        resp = Mock()
        resp.restart_session_response = Mock(
            status=iterm2.api_pb2.RestartSessionResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_restart_session',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_restart(only_if_exited=True)
            call_args = mock_rpc.await_args[0]
            assert call_args[2] is True  # only_if_exited (positional)

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="rst-1")
        resp = Mock()
        resp.restart_session_response = Mock(
            status=iterm2.api_pb2.RestartSessionResponse.Status.Value(
                "SESSION_NOT_FOUND"
            )
        )
        with patch.object(iterm2.rpc, 'async_restart_session',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_restart()


# ---------------------------------------------------------------------------
# Session.async_close
# ---------------------------------------------------------------------------

class TestAsyncClose:
    """Tests for Session.async_close."""

    @pytest.mark.asyncio
    async def test_success_default(self):
        sess = _make_session_from_link(session_id="cls-1")
        resp = Mock()
        resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("OK")]
        )
        with patch.object(iterm2.rpc, 'async_close',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_close()
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['force'] is False
            assert call_kwargs['sessions'] == ["cls-1"]

    @pytest.mark.asyncio
    async def test_success_force(self):
        sess = _make_session_from_link(session_id="cls-1")
        resp = Mock()
        resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("OK")]
        )
        with patch.object(iterm2.rpc, 'async_close',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_close(force=True)
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['force'] is True

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="cls-1")
        resp = Mock()
        resp.close_response = Mock(
            statuses=[iterm2.api_pb2.CloseResponse.Status.Value("USER_DECLINED")]
        )
        with patch.object(iterm2.rpc, 'async_close',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_close()


# ---------------------------------------------------------------------------
# Session.async_set_grid_size / Session.grid_size
# ---------------------------------------------------------------------------

class TestSessionGridSize:
    """Tests for Session grid_size property and async_set_grid_size."""

    def test_grid_size_property(self):
        sess = _make_session_from_link()
        # grid_size is a protobuf message from the link, has .width/.height
        assert sess.grid_size.width == 80
        assert sess.grid_size.height == 24

    @pytest.mark.asyncio
    async def test_async_set_grid_size(self):
        sess = _make_session_from_link(session_id="gs-1")
        resp = Mock()
        resp.set_property_response = Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_set_property',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            size = iterm2.util.Size(100, 50)
            await sess.async_set_grid_size(size)
            call_args = mock_rpc.await_args[0]
            assert call_args[1] == "grid_size"  # name (positional)
            parsed = json.loads(call_args[2])  # json_value (positional)
            assert parsed["width"] == 100
            assert parsed["height"] == 50


# ---------------------------------------------------------------------------
# Session.async_set_buried
# ---------------------------------------------------------------------------

class TestAsyncSetBuried:
    """Tests for Session.async_set_buried."""

    @pytest.mark.asyncio
    async def test_set_buried_true(self):
        sess = _make_session_from_link(session_id="bur-1")
        resp = Mock()
        resp.set_property_response = Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_set_property',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_set_buried(True)
            call_args = mock_rpc.await_args[0]
            assert call_args[1] == "buried"  # name (positional)
            assert json.loads(call_args[2]) is True  # json_value (positional)

    @pytest.mark.asyncio
    async def test_set_buried_false(self):
        sess = _make_session_from_link(session_id="bur-1")
        resp = Mock()
        resp.set_property_response = Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_set_property',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_set_buried(False)
            call_args = mock_rpc.await_args[0]
            assert json.loads(call_args[2]) is False  # json_value (positional)


# ---------------------------------------------------------------------------
# Session._async_set_property
# ---------------------------------------------------------------------------

class TestAsyncSetProperty:
    """Tests for Session._async_set_property."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="ps-1")
        resp = Mock()
        resp.set_property_response = Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_set_property',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            result = await sess._async_set_property("some_key", json.dumps(42))
            assert result is resp
            call_args = mock_rpc.await_args[0]
            assert call_args[1] == "some_key"  # name (positional)
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['session_id'] == "ps-1"

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="ps-1")
        resp = Mock()
        resp.set_property_response = Mock(
            status=iterm2.api_pb2.SetPropertyResponse.Status.Value("UNRECOGNIZED_NAME")
        )
        with patch.object(iterm2.rpc, 'async_set_property',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess._async_set_property("bad_key", "val")


# ---------------------------------------------------------------------------
# Session.async_get_selection
# ---------------------------------------------------------------------------

class TestAsyncGetSelection:
    """Tests for Session.async_get_selection."""

    @pytest.mark.asyncio
    async def test_success_with_selection(self):
        sess = _make_session_from_link(session_id="sel-1")
        # Build response with a sub_selection
        resp = Mock()
        sub_proto = Mock()
        sub_proto.windowed_coord_range.coord_range.start.x = 0
        sub_proto.windowed_coord_range.coord_range.start.y = 5
        sub_proto.windowed_coord_range.coord_range.end.x = 10
        sub_proto.windowed_coord_range.coord_range.end.y = 5
        sub_proto.windowed_coord_range.columns.location = 0
        sub_proto.windowed_coord_range.columns.length = 80
        sub_proto.selection_mode = 0  # CHARACTER
        sub_proto.connected = True

        get_sel = Mock()
        get_sel.selection.sub_selections = [sub_proto]

        sel_resp = Mock()
        sel_resp.status = iterm2.api_pb2.SelectionResponse.Status.Value("OK")
        sel_resp.get_selection_response = get_sel

        resp.selection_response = sel_resp

        with patch.object(iterm2.rpc, 'async_get_selection',
                          new=AsyncMock(return_value=resp)):
            with patch.object(iterm2, 'Selection') as mock_sel:
                with patch.object(iterm2, 'SubSelection') as mock_sub:
                    result = await sess.async_get_selection()
                    mock_sub.assert_called_once()
                    mock_sel.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_empty_selection(self):
        sess = _make_session_from_link(session_id="sel-1")
        get_sel = Mock()
        get_sel.selection.sub_selections = []
        sel_resp = Mock()
        sel_resp.status = iterm2.api_pb2.SelectionResponse.Status.Value("OK")
        sel_resp.get_selection_response = get_sel
        resp = Mock()
        resp.selection_response = sel_resp

        with patch.object(iterm2.rpc, 'async_get_selection',
                          new=AsyncMock(return_value=resp)):
            with patch.object(iterm2, 'Selection') as mock_sel:
                with patch.object(iterm2, 'SubSelection') as mock_sub:
                    await sess.async_get_selection()
                    mock_sub.assert_not_called()
                    mock_sel.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="sel-1")
        resp = Mock()
        resp.selection_response = Mock(
            status=iterm2.api_pb2.SelectionResponse.Status.Value("INVALID_SESSION")
        )
        with patch.object(iterm2.rpc, 'async_get_selection',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_get_selection()


# ---------------------------------------------------------------------------
# Session.async_get_selection_text
# ---------------------------------------------------------------------------

class TestAsyncGetSelectionText:
    """Tests for Session.async_get_selection_text."""

    @pytest.mark.asyncio
    async def test_delegates_to_selection(self):
        sess = _make_session_from_link(session_id="st-1")
        selection = Mock()
        selection.async_get_string = AsyncMock(return_value="selected text")
        with patch.object(selection, 'async_get_string',
                          new=AsyncMock(return_value="selected text")) as mock_get:
            result = await sess.async_get_selection_text(selection)
            assert result == "selected text"
            mock_get.assert_awaited_once_with(
                sess.connection, sess.session_id, sess.grid_size.width
            )


# ---------------------------------------------------------------------------
# Session.async_set_selection
# ---------------------------------------------------------------------------

class TestAsyncSetSelection:
    """Tests for Session.async_set_selection."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="ss-1")
        sel = Mock()
        resp = Mock()
        resp.selection_response = Mock(
            status=iterm2.api_pb2.SelectionResponse.Status.Value("OK")
        )
        with patch.object(iterm2.rpc, 'async_set_selection',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            await sess.async_set_selection(sel)
            call_args = mock_rpc.await_args[0]
            assert call_args[2] is sel  # selection (positional)

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="ss-1")
        sel = Mock()
        resp = Mock()
        resp.selection_response = Mock(
            status=iterm2.api_pb2.SelectionResponse.Status.Value("INVALID_SESSION")
        )
        with patch.object(iterm2.rpc, 'async_set_selection',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_set_selection(sel)


# ---------------------------------------------------------------------------
# Session.async_get_line_info
# ---------------------------------------------------------------------------

class TestAsyncGetLineInfo:
    """Tests for Session.async_get_line_info."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="li-1")
        line_data = json.dumps({
            "grid": 24,
            "history": 1000,
            "overflow": 50,
            "first_visible": 10,
        })
        resp = Mock()
        resp.get_property_response = Mock(
            status=iterm2.api_pb2.GetPropertyResponse.Status.Value("OK"),
            json_value=line_data,
        )
        with patch.object(iterm2.rpc, 'async_get_property',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            result = await sess.async_get_line_info()
            assert isinstance(result, iterm2.session.SessionLineInfo)
            assert result.mutable_area_height == 24
            assert result.scrollback_buffer_height == 1000
            assert result.overflow == 50
            assert result.first_visible_line_number == 10
            call_args = mock_rpc.await_args[0]
            assert call_args[1] == "number_of_lines"  # name (positional)

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="li-1")
        resp = Mock()
        resp.get_property_response = Mock(
            status=iterm2.api_pb2.GetPropertyResponse.Status.Value("UNRECOGNIZED_NAME")
        )
        with patch.object(iterm2.rpc, 'async_get_property',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException):
                await sess.async_get_line_info()


# ---------------------------------------------------------------------------
# Session.async_set_name
# ---------------------------------------------------------------------------

class TestAsyncSetName:
    """Tests for Session.async_set_name."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="sn-1")
        with patch.object(iterm2.rpc, 'async_invoke_method',
                          new=AsyncMock()) as mock_rpc:
            await sess.async_set_name("My New Name")
            call_args = mock_rpc.await_args[0]
            invocation = call_args[2]
            assert "iterm2.set_name" in invocation
            assert "My New Name" in invocation


# ---------------------------------------------------------------------------
# Session.async_run_tmux_command
# ---------------------------------------------------------------------------

class TestAsyncRunTmuxCommand:
    """Tests for Session.async_run_tmux_command."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="tmux-1")
        with patch.object(iterm2.rpc, 'async_invoke_method',
                          new=AsyncMock(return_value="tmux output")) as mock_rpc:
            result = await sess.async_run_tmux_command("list-sessions")
            assert result == "tmux output"
            invocation = mock_rpc.await_args[0][2]
            assert "iterm2.run_tmux_command" in invocation
            assert "list-sessions" in invocation


# ---------------------------------------------------------------------------
# Session.async_invoke_function
# ---------------------------------------------------------------------------

class TestAsyncInvokeFunction:
    """Tests for Session.async_invoke_function."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="inv-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='success')
        )
        resp.invoke_function_response.success = Mock(
            json_result=json.dumps({"result": 42})
        )
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)) as mock_rpc:
            result = await sess.async_invoke_function("myFunc()", timeout=10.0)
            assert result == {"result": 42}
            call_kwargs = mock_rpc.await_args[1]
            assert call_kwargs['session_id'] == "inv-1"
            assert call_kwargs['timeout'] == 10.0

    @pytest.mark.asyncio
    async def test_error_timeout(self):
        sess = _make_session_from_link(session_id="inv-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("TIMEOUT"),
            error_reason=""
        )
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException, match="Timeout"):
                await sess.async_invoke_function("slowFunc()")

    @pytest.mark.asyncio
    async def test_error_general(self):
        sess = _make_session_from_link(session_id="inv-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("FAILED"),
            error_reason="Function not found"
        )
        with patch.object(iterm2.rpc, 'async_invoke_function',
                          new=AsyncMock(return_value=resp)):
            with pytest.raises(iterm2.rpc.RPCException,
                               match="Function not found"):
                await sess.async_invoke_function("missingFunc()")


# ---------------------------------------------------------------------------
# Session.async_get_coprocess
# ---------------------------------------------------------------------------

class TestAsyncGetCoprocess:
    """Tests for Session.async_get_coprocess."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="cp-1")
        with patch.object(iterm2.capabilities, 'check_supports_coprocesses'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock(return_value="my-coproc")):
                result = await sess.async_get_coprocess()
                assert result == "my-coproc"


# ---------------------------------------------------------------------------
# Session.async_stop_coprocess
# ---------------------------------------------------------------------------

class TestAsyncStopCoprocess:
    """Tests for Session.async_stop_coprocess."""

    @pytest.mark.asyncio
    async def test_stopped_returns_true(self):
        sess = _make_session_from_link(session_id="sc-1")
        with patch.object(iterm2.capabilities, 'check_supports_coprocesses'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock(return_value="stopped")):
                result = await sess.async_stop_coprocess()
                assert result is True

    @pytest.mark.asyncio
    async def test_none_returns_false(self):
        sess = _make_session_from_link(session_id="sc-1")
        with patch.object(iterm2.capabilities, 'check_supports_coprocesses'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock(return_value=None)):
                result = await sess.async_stop_coprocess()
                assert result is False


# ---------------------------------------------------------------------------
# Session.async_add_annotation
# ---------------------------------------------------------------------------

class TestAsyncAddAnnotation:
    """Tests for Session.async_add_annotation."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="ann-1")
        rng = iterm2.util.CoordRange(
            iterm2.util.Point(0, 5),
            iterm2.util.Point(10, 5)
        )
        with patch.object(iterm2.capabilities, 'check_supports_add_annotation'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock()) as mock_rpc:
                await sess.async_add_annotation(rng, "my annotation")
                invocation = mock_rpc.await_args[0][2]
                assert "iterm2.add_annotation" in invocation
                assert "my annotation" in invocation
                assert "startX" in invocation
                assert "endX" in invocation


# ---------------------------------------------------------------------------
# Session.async_run_coprocess
# ---------------------------------------------------------------------------

class TestAsyncRunCoprocess:
    """Tests for Session.async_run_coprocess."""

    @pytest.mark.asyncio
    async def test_success_launched(self):
        sess = _make_session_from_link(session_id="rc-1")
        with patch.object(iterm2.capabilities, 'check_supports_coprocesses'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock(return_value="launched")):
                result = await sess.async_run_coprocess("python3 myscript.py")
                assert result is True

    @pytest.mark.asyncio
    async def test_already_running(self):
        sess = _make_session_from_link(session_id="rc-1")
        with patch.object(iterm2.capabilities, 'check_supports_coprocesses'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock(return_value=None)):
                result = await sess.async_run_coprocess("python3 myscript.py")
                assert result is False


# ---------------------------------------------------------------------------
# Session.async_load_url
# ---------------------------------------------------------------------------

class TestAsyncLoadUrl:
    """Tests for Session.async_load_url."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="lu-1")
        with patch.object(iterm2.capabilities, 'check_supports_load_url'):
            with patch.object(iterm2.rpc, 'async_invoke_method',
                              new=AsyncMock()) as mock_rpc:
                await sess.async_load_url("https://example.com")
                invocation = mock_rpc.await_args[0][2]
                assert "iterm2.load_url" in invocation
                assert "https://example.com" in invocation


# ---------------------------------------------------------------------------
# Session.async_move_to_new_tab
# ---------------------------------------------------------------------------

class TestAsyncMoveToNewTab:
    """Tests for Session.async_move_to_new_tab."""

    @pytest.mark.asyncio
    async def test_success_minimal(self):
        sess = _make_session_from_link(session_id="mtt-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='success')
        )
        resp.invoke_function_response.success = Mock(
            json_result=json.dumps("new-tab-id")
        )
        with patch.object(iterm2.capabilities,
                          'check_supports_move_session_to_tab_or_window'):
            with patch.object(iterm2.rpc, 'async_invoke_function',
                              new=AsyncMock(return_value=resp)):
                result = await sess.async_move_to_new_tab()
                assert result == "new-tab-id"

    @pytest.mark.asyncio
    async def test_success_with_window_and_tab_index(self):
        sess = _make_session_from_link(session_id="mtt-1")
        mock_window = Mock()
        mock_window.window_id = "win-5"
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='success')
        )
        resp.invoke_function_response.success = Mock(
            json_result=json.dumps("new-tab-id")
        )
        with patch.object(iterm2.capabilities,
                          'check_supports_move_session_to_tab_or_window'):
            with patch.object(iterm2.rpc, 'async_invoke_function',
                              new=AsyncMock(return_value=resp)) as mock_rpc:
                result = await sess.async_move_to_new_tab(
                    window=mock_window, tab_index=0
                )
                assert result == "new-tab-id"
                invocation = mock_rpc.await_args[0][1]
                assert "iterm2.move_session_to_new_tab" in invocation
                assert "win-5" in invocation
                assert "tab_index" in invocation

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="mtt-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("FAILED"),
            error_reason="Cannot move"
        )
        with patch.object(iterm2.capabilities,
                          'check_supports_move_session_to_tab_or_window'):
            with patch.object(iterm2.rpc, 'async_invoke_function',
                              new=AsyncMock(return_value=resp)):
                with pytest.raises(iterm2.rpc.RPCException,
                                   match="Cannot move"):
                    await sess.async_move_to_new_tab()


# ---------------------------------------------------------------------------
# Session.async_move_to_new_window
# ---------------------------------------------------------------------------

class TestAsyncMoveToNewWindow:
    """Tests for Session.async_move_to_new_window."""

    @pytest.mark.asyncio
    async def test_success(self):
        sess = _make_session_from_link(session_id="mtw-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='success')
        )
        resp.invoke_function_response.success = Mock(
            json_result=json.dumps("new-window-id")
        )
        with patch.object(iterm2.capabilities,
                          'check_supports_move_session_to_tab_or_window'):
            with patch.object(iterm2.rpc, 'async_invoke_function',
                              new=AsyncMock(return_value=resp)):
                result = await sess.async_move_to_new_window()
                assert result == "new-window-id"

    @pytest.mark.asyncio
    async def test_error(self):
        sess = _make_session_from_link(session_id="mtw-1")
        resp = Mock()
        resp.invoke_function_response = Mock(
            WhichOneof=Mock(return_value='error')
        )
        resp.invoke_function_response.error = Mock(
            status=iterm2.api_pb2.InvokeFunctionResponse.Status.Value("FAILED"),
            error_reason="Cannot move"
        )
        with patch.object(iterm2.capabilities,
                          'check_supports_move_session_to_tab_or_window'):
            with patch.object(iterm2.rpc, 'async_invoke_function',
                              new=AsyncMock(return_value=resp)):
                with pytest.raises(iterm2.rpc.RPCException,
                                   match="Cannot move"):
                    await sess.async_move_to_new_window()


# ---------------------------------------------------------------------------
# ProxySession
# ---------------------------------------------------------------------------

class TestProxySession:
    """Tests for ProxySession."""

    def test_init(self):
        conn = _mock_connection()
        proxy = iterm2.session.ProxySession(conn, "active")
        assert proxy.session_id == "active"
        assert proxy.connection is conn

    def test_repr(self):
        conn = _mock_connection()
        proxy = iterm2.session.ProxySession(conn, "all")
        r = repr(proxy)
        assert "ProxySession" in r
        assert "all" in r

    def test_pretty_str(self):
        conn = _mock_connection()
        proxy = iterm2.session.ProxySession(conn, "active")
        result = proxy.pretty_str("")
        assert "ProxySession" in result
        assert "active" in result

    def test_pretty_str_with_indent(self):
        conn = _mock_connection()
        proxy = iterm2.session.ProxySession(conn, "all")
        result = proxy.pretty_str("  ")
        assert result.startswith("  ProxySession")


# ---------------------------------------------------------------------------
# Session.Delegate
# ---------------------------------------------------------------------------

class TestSessionDelegate:
    """Tests for Session.Delegate abstract class."""

    def test_delegate_is_abstract(self):
        with pytest.raises(TypeError):
            iterm2.session.Session.Delegate()

    def test_delegate_has_required_methods(self):
        assert hasattr(iterm2.session.Session.Delegate,
                       'session_delegate_get_tab')
        assert hasattr(iterm2.session.Session.Delegate,
                       'session_delegate_get_window')
        assert hasattr(iterm2.session.Session.Delegate,
                       'session_delegate_create_session')

    def test_delegate_methods_are_abstract(self):
        import inspect
        cls = iterm2.session.Session.Delegate
        assert inspect.isabstract(cls)
