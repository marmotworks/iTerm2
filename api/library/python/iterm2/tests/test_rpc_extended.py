import json
import pytest
import unittest.mock as mock
import iterm2
import iterm2.rpc
import iterm2.api_pb2
import iterm2.util
import iterm2.selection


def make_response(request_id=1):
    """Creates a basic successful response."""
    resp = iterm2.api_pb2.ServerOriginatedMessage()
    resp.id = request_id
    return resp


def make_mock_connection(response=None):
    """Creates a mock connection that captures the last sent request."""
    conn = mock.MagicMock()
    conn.async_send_message = mock.AsyncMock()
    default_resp = response if response is not None else make_response()
    conn.async_dispatch_until_id = mock.AsyncMock(return_value=default_resp)
    return conn


class TestAsyncCall:
    """Tests for the _async_call private function."""

    @pytest.mark.asyncio
    async def test_async_call_success(self):
        conn = make_mock_connection()
        response = make_response(42)
        conn.async_dispatch_until_id.return_value = response

        req = iterm2.rpc._alloc_request()
        result = await iterm2.rpc._async_call(conn, req)

        conn.async_send_message.assert_called_once_with(req)
        conn.async_dispatch_until_id.assert_called_once_with(req.id)
        assert result == response

    @pytest.mark.asyncio
    async def test_async_call_raises_on_error(self):
        conn = make_mock_connection()
        response = iterm2.api_pb2.ServerOriginatedMessage()
        response.error = "something went wrong"
        conn.async_dispatch_until_id.return_value = response

        req = iterm2.rpc._alloc_request()
        with pytest.raises(iterm2.rpc.RPCException) as exc_info:
            await iterm2.rpc._async_call(conn, req)
        assert str(exc_info.value) == "something went wrong"


class TestAsyncListSessions:

    @pytest.mark.asyncio
    async def test_builds_list_sessions_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_sessions(conn)

        req = conn._captured_request
        assert req.HasField("list_sessions_request")


class TestAsyncSendText:

    @pytest.mark.asyncio
    async def test_sets_all_fields(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_send_text(conn, "sess1", "hello world", True)

        req = conn._captured_request
        assert req.send_text_request.session == "sess1"
        assert req.send_text_request.text == "hello world"
        assert req.send_text_request.suppress_broadcast is True

    @pytest.mark.asyncio
    async def test_suppress_broadcast_false(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_send_text(conn, "sess2", "ls\n", False)

        req = conn._captured_request
        assert req.send_text_request.suppress_broadcast is False


class TestAsyncSplitPane:

    @pytest.mark.asyncio
    async def test_vertical_before(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_split_pane(conn, "sess1", True, True)

        req = conn._captured_request
        assert req.HasField("split_pane_request")
        assert req.split_pane_request.session == "sess1"
        assert req.split_pane_request.split_direction == iterm2.api_pb2.SplitPaneRequest.VERTICAL
        assert req.split_pane_request.before is True

    @pytest.mark.asyncio
    async def test_horizontal_after(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_split_pane(conn, "sess1", False, False)

        req = conn._captured_request
        assert req.split_pane_request.split_direction == iterm2.api_pb2.SplitPaneRequest.HORIZONTAL
        assert req.split_pane_request.before is False

    @pytest.mark.asyncio
    async def test_with_profile(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_split_pane(conn, "sess1", True, True, profile="MyProfile")

        req = conn._captured_request
        assert req.split_pane_request.profile_name == "MyProfile"

    @pytest.mark.asyncio
    async def test_with_profile_customizations(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        customs = {"key1": "val1", "key2": "val2"}
        await iterm2.rpc.async_split_pane(conn, "sess1", True, True, profile_customizations=customs)

        req = conn._captured_request
        assert len(req.split_pane_request.custom_profile_properties) == 2
        props = {(p.key, p.json_value) for p in req.split_pane_request.custom_profile_properties}
        assert ("key1", "val1") in props
        assert ("key2", "val2") in props

    @pytest.mark.asyncio
    async def test_no_session(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_split_pane(conn, None, True, True)

        req = conn._captured_request
        assert req.split_pane_request.session == ""


class TestAsyncCreateTab:

    @pytest.mark.asyncio
    async def test_basic(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_create_tab(conn)

        req = conn._captured_request
        assert req.HasField("create_tab_request")

    @pytest.mark.asyncio
    async def test_with_profile(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_create_tab(conn, profile="TestProfile")

        req = conn._captured_request
        assert req.create_tab_request.profile_name == "TestProfile"

    @pytest.mark.asyncio
    async def test_with_window(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_create_tab(conn, window="win1")

        req = conn._captured_request
        assert req.create_tab_request.window_id == "win1"

    @pytest.mark.asyncio
    async def test_with_index(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_create_tab(conn, index=3)

        req = conn._captured_request
        assert req.create_tab_request.tab_index == 3

    @pytest.mark.asyncio
    async def test_with_command(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_create_tab(conn, command="ls -la")

        req = conn._captured_request
        props = {p.key: p.json_value for p in req.create_tab_request.custom_profile_properties}
        assert "Custom Command" in props
        assert "Command" in props

    @pytest.mark.asyncio
    async def test_with_profile_customizations(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        customs = {"CustomProperty": "customVal"}
        await iterm2.rpc.async_create_tab(conn, profile_customizations=customs)

        req = conn._captured_request
        props = {p.key: p.json_value for p in req.create_tab_request.custom_profile_properties}
        assert props["CustomProperty"] == "customVal"


class TestAsyncGetScreenContents:

    @pytest.mark.asyncio
    async def test_basic(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_screen_contents(conn, "sess1")

        req = conn._captured_request
        assert req.get_buffer_request.session == "sess1"
        assert req.get_buffer_request.include_styles is False
        assert req.get_buffer_request.line_range.screen_contents_only is True

    @pytest.mark.asyncio
    async def test_with_styles(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_screen_contents(conn, "sess1", style=True)

        req = conn._captured_request
        assert req.get_buffer_request.include_styles is True

    @pytest.mark.asyncio
    async def test_with_windowed_coord_range(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0),
            iterm2.util.Point(10, 5))
        windowed_range = iterm2.util.WindowedCoordRange(
            coord_range, iterm2.util.Range(0, 80))

        await iterm2.rpc.async_get_screen_contents(conn, "sess1", windowed_coord_range=windowed_range)

        req = conn._captured_request
        assert req.get_buffer_request.line_range.HasField("windowed_coord_range")
        assert req.get_buffer_request.line_range.screen_contents_only is False

    @pytest.mark.asyncio
    async def test_no_session(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_screen_contents(conn, None)

        req = conn._captured_request
        assert req.get_buffer_request.session == ""


class TestAsyncGetPrompt:

    @pytest.mark.asyncio
    async def test_basic(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_prompt(conn)

        req = conn._captured_request
        assert req.HasField("get_prompt_request")

    @pytest.mark.asyncio
    async def test_with_session(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_prompt(conn, session="sess1")

        req = conn._captured_request
        assert req.get_prompt_request.session == "sess1"

    @pytest.mark.asyncio
    async def test_with_prompt_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_prompt(conn, prompt_id="42")

        req = conn._captured_request
        assert req.get_prompt_request.unique_prompt_id == "42"


class TestAsyncListPrompts:

    @pytest.mark.asyncio
    async def test_basic(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_prompts(conn, "sess1", None, None)

        req = conn._captured_request
        assert req.HasField("list_prompts_request")
        assert req.list_prompts_request.session == "sess1"

    @pytest.mark.asyncio
    async def test_with_first_and_last(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_prompts(conn, "sess1", "10", "20")

        req = conn._captured_request
        assert req.list_prompts_request.first_unique_id == "10"
        assert req.list_prompts_request.last_unique_id == "20"

    @pytest.mark.asyncio
    async def test_with_first_only(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_prompts(conn, "sess1", "10", None)

        req = conn._captured_request
        assert req.list_prompts_request.first_unique_id == "10"
        assert req.list_prompts_request.last_unique_id == ""

    @pytest.mark.asyncio
    async def test_with_last_only(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_prompts(conn, "sess1", None, "20")

        req = conn._captured_request
        assert req.list_prompts_request.first_unique_id == ""
        assert req.list_prompts_request.last_unique_id == "20"


class TestAsyncStartTransaction:

    @pytest.mark.asyncio
    async def test_sets_begin_true(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_start_transaction(conn)

        req = conn._captured_request
        assert req.transaction_request.begin is True


class TestAsyncEndTransaction:

    @pytest.mark.asyncio
    async def test_sets_begin_false(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_end_transaction(conn)

        req = conn._captured_request
        assert req.transaction_request.begin is False


class TestAsyncRegisterWebViewTool:

    @pytest.mark.asyncio
    async def test_sets_all_fields(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_register_web_view_tool(
            conn, "My Tool", "com.example.tool", True, "http://example.com")

        req = conn._captured_request
        assert req.register_tool_request.name == "My Tool"
        assert req.register_tool_request.identifier == "com.example.tool"
        assert req.register_tool_request.reveal_if_already_registered is True
        assert req.register_tool_request.URL == "http://example.com"
        assert req.register_tool_request.tool_type == iterm2.api_pb2.RegisterToolRequest.ToolType.Value("WEB_VIEW_TOOL")

    @pytest.mark.asyncio
    async def test_reveal_false(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_register_web_view_tool(
            conn, "My Tool", "com.example.tool", False, "http://example.com")

        req = conn._captured_request
        assert req.register_tool_request.reveal_if_already_registered is False


class TestAsyncSetProfileProperty:

    @pytest.mark.asyncio
    async def test_with_session_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_profile_property(conn, "sess1", "key1", {"a": 1})

        req = conn._captured_request
        assert req.set_profile_property_request.session == "sess1"
        assert req.set_profile_property_request.key == "key1"
        assert json.loads(req.set_profile_property_request.json_value) == {"a": 1}

    @pytest.mark.asyncio
    async def test_with_guids(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_profile_property(
            conn, None, "key1", "value1", guids=["guid1", "guid2"])

        req = conn._captured_request
        assert set(req.set_profile_property_request.guid_list.guids) == {"guid1", "guid2"}


class TestAsyncSetProfilePropertyJson:

    @pytest.mark.asyncio
    async def test_with_session(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_profile_property_json(conn, "sess1", "key1", '{"v":2}')

        req = conn._captured_request
        assert req.set_profile_property_request.session == "sess1"
        assert req.set_profile_property_request.key == "key1"
        assert req.set_profile_property_request.json_value == '{"v":2}'

    @pytest.mark.asyncio
    async def test_with_guids(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_profile_property_json(
            conn, None, "key1", '{"v":2}', guids=["g1"])

        req = conn._captured_request
        assert "g1" in req.set_profile_property_request.guid_list.guids


class TestAsyncSetProfilePropertiesJson:

    @pytest.mark.asyncio
    async def test_multiple_assignments(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        assignments = [("k1", '{"a":1}'), ("k2", '{"b":2}')]
        await iterm2.rpc.async_set_profile_properties_json(conn, "sess1", assignments)

        req = conn._captured_request
        assert req.set_profile_property_request.session == "sess1"
        assert len(req.set_profile_property_request.assignments) == 2
        proto_dict = {a.key: a.json_value for a in req.set_profile_property_request.assignments}
        assert proto_dict["k1"] == '{"a":1}'
        assert proto_dict["k2"] == '{"b":2}'

    @pytest.mark.asyncio
    async def test_with_guids(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        assignments = [("k1", "v1")]
        await iterm2.rpc.async_set_profile_properties_json(
            conn, None, assignments, guids=["g1", "g2"])

        req = conn._captured_request
        assert set(req.set_profile_property_request.guid_list.guids) == {"g1", "g2"}


class TestAsyncGetProfile:

    @pytest.mark.asyncio
    async def test_basic(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_profile(conn)

        req = conn._captured_request
        assert req.HasField("get_profile_property_request")

    @pytest.mark.asyncio
    async def test_with_session(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_profile(conn, session="sess1")

        req = conn._captured_request
        assert req.get_profile_property_request.session == "sess1"

    @pytest.mark.asyncio
    async def test_with_keys(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_profile(conn, keys=["key1", "key2"])

        req = conn._captured_request
        assert set(req.get_profile_property_request.keys) == {"key1", "key2"}


class TestAsyncSetProperty:

    @pytest.mark.asyncio
    async def test_with_window_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_property(conn, "propName", '{"v":1}', window_id="win1")

        req = conn._captured_request
        assert req.HasField("set_property_request")
        assert req.set_property_request.window_id == "win1"
        assert req.set_property_request.name == "propName"
        assert req.set_property_request.json_value == '{"v":1}'

    @pytest.mark.asyncio
    async def test_with_session_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_property(conn, "propName", '{"v":1}', session_id="sess1")

        req = conn._captured_request
        assert req.set_property_request.session_id == "sess1"

    @pytest.mark.asyncio
    async def test_raises_when_no_id(self):
        conn = make_mock_connection()
        with pytest.raises(AssertionError):
            await iterm2.rpc.async_set_property(conn, "propName", '{"v":1}')


class TestAsyncGetProperty:

    @pytest.mark.asyncio
    async def test_with_window_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_property(conn, "propName", window_id="win1")

        req = conn._captured_request
        assert req.HasField("get_property_request")
        assert req.get_property_request.window_id == "win1"
        assert req.get_property_request.name == "propName"

    @pytest.mark.asyncio
    async def test_with_session_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_property(conn, "propName", session_id="sess1")

        req = conn._captured_request
        assert req.get_property_request.session_id == "sess1"


class TestAsyncInject:

    @pytest.mark.asyncio
    async def test_inject_bytes(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_inject(conn, b"hello", ["sess1", "sess2"])

        req = conn._captured_request
        assert req.HasField("inject_request")
        assert req.inject_request.data == b"hello"
        assert set(req.inject_request.session_id) == {"sess1", "sess2"}

    @pytest.mark.asyncio
    async def test_inject_bytes_only(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_inject(conn, b"hello", ["sess1"])

        req = conn._captured_request
        assert req.inject_request.data == b"hello"


class TestAsyncActivate:

    @pytest.mark.asyncio
    async def test_with_session_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_activate(conn, True, True, True, session_id="sess1")

        req = conn._captured_request
        assert req.activate_request.session_id == "sess1"
        assert req.activate_request.select_session is True
        assert req.activate_request.select_tab is True
        assert req.activate_request.order_window_front is True

    @pytest.mark.asyncio
    async def test_with_tab_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_activate(conn, False, True, True, tab_id="tab1")

        req = conn._captured_request
        assert req.activate_request.tab_id == "tab1"

    @pytest.mark.asyncio
    async def test_with_window_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_activate(conn, False, False, True, window_id="win1")

        req = conn._captured_request
        assert req.activate_request.window_id == "win1"

    @pytest.mark.asyncio
    async def test_with_activate_app_opts_raise_all(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_activate(
            conn, False, False, False,
            activate_app_opts=[iterm2.rpc.ACTIVATE_RAISE_ALL_WINDOWS])

        req = conn._captured_request
        assert req.activate_request.HasField("activate_app")
        assert req.activate_request.activate_app.raise_all_windows is True

    @pytest.mark.asyncio
    async def test_with_activate_app_opts_ignoring_other_apps(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_activate(
            conn, False, False, False,
            activate_app_opts=[iterm2.rpc.ACTIVATE_IGNORING_OTHER_APPS])

        req = conn._captured_request
        assert req.activate_request.activate_app.ignoring_other_apps is True

    @pytest.mark.asyncio
    async def test_no_ids(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_activate(conn, False, False, False)

        req = conn._captured_request
        assert req.activate_request.session_id == ""
        assert req.activate_request.tab_id == ""
        assert req.activate_request.window_id == ""
        assert not req.activate_request.HasField("activate_app")


class TestAsyncVariable:

    @pytest.mark.asyncio
    async def test_session_level(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_variable(conn, session_id="sess1", gets=["var1"])

        req = conn._captured_request
        assert req.variable_request.session_id == "sess1"
        assert "var1" in req.variable_request.get

    @pytest.mark.asyncio
    async def test_tab_level(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_variable(conn, tab_id="tab1", gets=["var1"])

        req = conn._captured_request
        assert req.variable_request.tab_id == "tab1"

    @pytest.mark.asyncio
    async def test_window_level(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_variable(conn, window_id="win1", gets=["var1"])

        req = conn._captured_request
        assert req.variable_request.window_id == "win1"

    @pytest.mark.asyncio
    async def test_app_level(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_variable(conn, gets=["var1"])

        req = conn._captured_request
        assert req.variable_request.app is True

    @pytest.mark.asyncio
    async def test_set_variables(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_variable(
            conn, session_id="sess1",
            sets=[("var1", '{"a":1}'), ("var2", '{"b":2}')])

        req = conn._captured_request
        assert len(req.variable_request.set) == 2
        kvps = {s.name: s.value for s in req.variable_request.set}
        assert kvps["var1"] == '{"a":1}'
        assert kvps["var2"] == '{"b":2}'

    @pytest.mark.asyncio
    async def test_empty_sets_and_gets(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_variable(conn, session_id="sess1")

        req = conn._captured_request
        assert len(req.variable_request.get) == 0
        assert len(req.variable_request.set) == 0


class TestAsyncSaveArrangement:

    @pytest.mark.asyncio
    async def test_without_window(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_save_arrangement(conn, "MyLayout")

        req = conn._captured_request
        assert req.saved_arrangement_request.name == "MyLayout"
        assert req.saved_arrangement_request.action == iterm2.api_pb2.SavedArrangementRequest.Action.Value("SAVE")

    @pytest.mark.asyncio
    async def test_with_window(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_save_arrangement(conn, "MyLayout", window_id="win1")

        req = conn._captured_request
        assert req.saved_arrangement_request.window_id == "win1"


class TestAsyncRestoreArrangement:

    @pytest.mark.asyncio
    async def test_without_window(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_restore_arrangement(conn, "MyLayout")

        req = conn._captured_request
        assert req.saved_arrangement_request.name == "MyLayout"
        assert req.saved_arrangement_request.action == iterm2.api_pb2.SavedArrangementRequest.Action.Value("RESTORE")

    @pytest.mark.asyncio
    async def test_with_window(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_restore_arrangement(conn, "MyLayout", window_id="win1")

        req = conn._captured_request
        assert req.saved_arrangement_request.window_id == "win1"


class TestAsyncListArrangements:

    @pytest.mark.asyncio
    async def test_list_action(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_arrangements(conn)

        req = conn._captured_request
        assert req.saved_arrangement_request.action == iterm2.api_pb2.SavedArrangementRequest.Action.Value("LIST")


class TestAsyncGetFocusInfo:

    @pytest.mark.asyncio
    async def test_sets_focus_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_focus_info(conn)

        req = conn._captured_request
        assert req.HasField("focus_request")


class TestAsyncListProfiles:

    @pytest.mark.asyncio
    async def test_all_profiles(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_profiles(conn, None, None)

        req = conn._captured_request
        assert req.HasField("list_profiles_request")
        assert len(req.list_profiles_request.guids) == 0
        assert len(req.list_profiles_request.properties) == 0

    @pytest.mark.asyncio
    async def test_with_guids(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_profiles(conn, ["g1", "g2"], None)

        req = conn._captured_request
        assert set(req.list_profiles_request.guids) == {"g1", "g2"}

    @pytest.mark.asyncio
    async def test_with_properties(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_profiles(conn, None, ["prop1", "prop2"])

        req = conn._captured_request
        assert set(req.list_profiles_request.properties) == {"prop1", "prop2"}

    @pytest.mark.asyncio
    async def test_with_both(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_profiles(conn, ["g1"], ["prop1"])

        req = conn._captured_request
        assert "g1" in req.list_profiles_request.guids
        assert "prop1" in req.list_profiles_request.properties


class TestAsyncSendRpcResult:

    @pytest.mark.asyncio
    async def test_success_value(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_send_rpc_result(conn, "42", False, {"result": "ok"})

        req = conn._captured_request
        assert req.server_originated_rpc_result_request.request_id == "42"
        assert json.loads(req.server_originated_rpc_result_request.json_value) == {"result": "ok"}
        assert not req.server_originated_rpc_result_request.json_exception

    @pytest.mark.asyncio
    async def test_exception_value(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_send_rpc_result(conn, "42", True, "error message")

        req = conn._captured_request
        assert req.server_originated_rpc_result_request.request_id == "42"
        assert json.loads(req.server_originated_rpc_result_request.json_exception) == "error message"
        assert not req.server_originated_rpc_result_request.json_value


class TestAsyncRestartSession:

    @pytest.mark.asyncio
    async def test_not_exited(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_restart_session(conn, "sess1", False)

        req = conn._captured_request
        assert req.HasField("restart_session_request")
        assert req.restart_session_request.session_id == "sess1"
        assert req.restart_session_request.only_if_exited is False

    @pytest.mark.asyncio
    async def test_only_if_exited(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_restart_session(conn, "sess1", True)

        req = conn._captured_request
        assert req.restart_session_request.only_if_exited is True


class TestAsyncMenuItem:

    @pytest.mark.asyncio
    async def test_query_only(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_menu_item(conn, "com.example.menu", True)

        req = conn._captured_request
        assert req.HasField("menu_item_request")
        assert req.menu_item_request.identifier == "com.example.menu"
        assert req.menu_item_request.query_only is True

    @pytest.mark.asyncio
    async def test_select(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_menu_item(conn, "com.example.menu", False)

        req = conn._captured_request
        assert req.menu_item_request.query_only is False


class TestAsyncSetTabLayout:

    @pytest.mark.asyncio
    async def test_sets_tab_id_and_root(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        tree = iterm2.api_pb2.SplitTreeNode()
        tree.vertical = True
        link = tree.links.add()
        link.session.unique_identifier = "sess1"

        await iterm2.rpc.async_set_tab_layout(conn, "tab1", tree)

        req = conn._captured_request
        assert req.HasField("set_tab_layout_request")
        assert req.set_tab_layout_request.tab_id == "tab1"
        assert req.set_tab_layout_request.root.vertical is True
        assert req.set_tab_layout_request.root.links[0].session.unique_identifier == "sess1"


class TestAsyncGetBroadcastDomains:

    @pytest.mark.asyncio
    async def test_sets_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_broadcast_domains(conn)

        req = conn._captured_request
        assert req.HasField("get_broadcast_domains_request")


class TestTmuxRpcFunctions:

    @pytest.mark.asyncio
    async def test_list_tmux_connections(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        with mock.patch.object(iterm2.Transaction, 'current', return_value=None):
            await iterm2.rpc.async_rpc_list_tmux_connections(conn)

        req = conn._captured_request
        assert req.HasField("tmux_request")
        assert req.tmux_request.HasField("list_connections")

    @pytest.mark.asyncio
    async def test_send_tmux_command(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        with mock.patch.object(iterm2.Transaction, 'current', return_value=None):
            await iterm2.rpc.async_rpc_send_tmux_command(conn, "tmux1", "list-windows")

        req = conn._captured_request
        assert req.tmux_request.HasField("send_command")
        assert req.tmux_request.send_command.connection_id == "tmux1"
        assert req.tmux_request.send_command.command == "list-windows"

    @pytest.mark.asyncio
    async def test_set_tmux_window_visible(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        with mock.patch.object(iterm2.Transaction, 'current', return_value=None):
            await iterm2.rpc.async_rpc_set_tmux_window_visible(conn, "tmux1", "3", True)

        req = conn._captured_request
        assert req.tmux_request.HasField("set_window_visible")
        assert req.tmux_request.set_window_visible.connection_id == "tmux1"
        assert req.tmux_request.set_window_visible.window_id == "3"
        assert req.tmux_request.set_window_visible.visible is True

    @pytest.mark.asyncio
    async def test_set_tmux_window_hidden(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        with mock.patch.object(iterm2.Transaction, 'current', return_value=None):
            await iterm2.rpc.async_rpc_set_tmux_window_visible(conn, "tmux1", "3", False)

        req = conn._captured_request
        assert req.tmux_request.set_window_visible.visible is False

    @pytest.mark.asyncio
    async def test_create_tmux_window_without_affinity(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        with mock.patch.object(iterm2.Transaction, 'current', return_value=None):
            await iterm2.rpc.async_rpc_create_tmux_window(conn, "tmux1")

        req = conn._captured_request
        assert req.tmux_request.HasField("create_window")
        assert req.tmux_request.create_window.connection_id == "tmux1"
        assert req.tmux_request.create_window.affinity == ""

    @pytest.mark.asyncio
    async def test_create_tmux_window_with_affinity(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        with mock.patch.object(iterm2.Transaction, 'current', return_value=None):
            await iterm2.rpc.async_rpc_create_tmux_window(conn, "tmux1", affinity="sess1")

        req = conn._captured_request
        assert req.tmux_request.create_window.affinity == "sess1"

    @pytest.mark.asyncio
    async def test_tmux_raises_in_transaction(self):
        conn = make_mock_connection()

        fake_txn = mock.MagicMock()
        with mock.patch.object(iterm2.Transaction, 'current', return_value=fake_txn):
            with pytest.raises(AssertionError):
                await iterm2.rpc.async_rpc_list_tmux_connections(conn)


class TestAsyncReorderTabs:

    @pytest.mark.asyncio
    async def test_single_window(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        assignments = [("win1", ["tab1", "tab2"])]
        await iterm2.rpc.async_reorder_tabs(conn, assignments)

        req = conn._captured_request
        assert req.HasField("reorder_tabs_request")
        assert len(req.reorder_tabs_request.assignments) == 1
        assert req.reorder_tabs_request.assignments[0].window_id == "win1"
        assert list(req.reorder_tabs_request.assignments[0].tab_ids) == ["tab1", "tab2"]

    @pytest.mark.asyncio
    async def test_multiple_windows(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        assignments = [
            ("win1", ["tab1", "tab2"]),
            ("win2", ["tab3"]),
        ]
        await iterm2.rpc.async_reorder_tabs(conn, assignments)

        req = conn._captured_request
        assert len(req.reorder_tabs_request.assignments) == 2


class TestAsyncGetDefaultProfile:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_default_profile(conn)

        req = conn._captured_request
        assert req.HasField("preferences_request")
        assert len(req.preferences_request.requests) == 1
        sub_req = req.preferences_request.requests[0]
        assert sub_req.HasField("get_default_profile_request")


class TestAsyncSetDefaultProfile:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_default_profile(conn, "profile-guid-123")

        req = conn._captured_request
        assert req.HasField("preferences_request")
        sub_req = req.preferences_request.requests[0]
        assert sub_req.HasField("set_default_profile_request")
        assert sub_req.set_default_profile_request.guid == "profile-guid-123"


class TestAsyncGetPreference:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_preference(conn, "NSStatusbarShowStack")

        req = conn._captured_request
        assert req.HasField("preferences_request")
        sub_req = req.preferences_request.requests[0]
        assert sub_req.HasField("get_preference_request")
        assert sub_req.get_preference_request.key == "NSStatusbarShowStack"


class TestAsyncSetPreference:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_preference(conn, "NSStatusbarShowStack", "true")

        req = conn._captured_request
        assert req.HasField("preferences_request")
        sub_req = req.preferences_request.requests[0]
        assert sub_req.HasField("set_preference_request")
        assert sub_req.set_preference_request.key == "NSStatusbarShowStack"
        assert sub_req.set_preference_request.json_value == "true"


class TestAsyncListColorPresets:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_list_color_presets(conn)

        req = conn._captured_request
        assert req.HasField("color_preset_request")
        assert req.color_preset_request.HasField("list_presets")


class TestAsyncGetColorPreset:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_color_preset(conn, "Solarized Dark")

        req = conn._captured_request
        assert req.HasField("color_preset_request")
        assert req.color_preset_request.HasField("get_preset")
        assert req.color_preset_request.get_preset.name == "Solarized Dark"


class TestAsyncGetSelection:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_get_selection(conn, "sess1")

        req = conn._captured_request
        assert req.selection_request.HasField("get_selection_request")
        assert req.selection_request.get_selection_request.session_id == "sess1"


class TestAsyncSetSelection:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0),
            iterm2.util.Point(5, 0))
        windowed_range = iterm2.util.WindowedCoordRange(
            coord_range, iterm2.util.Range(0, 80))
        sub_sel = iterm2.selection.SubSelection(
            windowed_range,
            iterm2.selection.SelectionMode.CHARACTER,
            False)
        selection = iterm2.selection.Selection([sub_sel])

        await iterm2.rpc.async_set_selection(conn, "sess1", selection)

        req = conn._captured_request
        assert req.selection_request.HasField("set_selection_request")
        assert req.selection_request.set_selection_request.session_id == "sess1"
        assert req.selection_request.set_selection_request.HasField("selection")
        assert len(req.selection_request.set_selection_request.selection.sub_selections) == 1


class TestAsyncOpenStatusBarComponentPopover:

    @pytest.mark.asyncio
    async def test_builds_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        size = iterm2.util.Size(200, 100)

        await iterm2.rpc.async_open_status_bar_component_popover(
            conn, "com.example.component", "sess1", "<html>Hi</html>", size)

        req = conn._captured_request
        assert req.HasField("status_bar_component_request")
        assert req.status_bar_component_request.identifier == "com.example.component"
        assert req.status_bar_component_request.open_popover.session_id == "sess1"
        assert req.status_bar_component_request.open_popover.html == "<html>Hi</html>"
        assert req.status_bar_component_request.open_popover.size.width == 200
        assert req.status_bar_component_request.open_popover.size.height == 100


class TestAsyncSetBroadcastDomains:

    @pytest.mark.asyncio
    async def test_single_domain(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_broadcast_domains(conn, [["sess1", "sess2"]])

        req = conn._captured_request
        assert req.HasField("set_broadcast_domains_request")
        assert len(req.set_broadcast_domains_request.broadcast_domains) == 1
        assert set(req.set_broadcast_domains_request.broadcast_domains[0].session_ids) == {"sess1", "sess2"}

    @pytest.mark.asyncio
    async def test_multiple_domains(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_broadcast_domains(
            conn, [["sess1"], ["sess2", "sess3"]])

        req = conn._captured_request
        assert len(req.set_broadcast_domains_request.broadcast_domains) == 2
        assert set(req.set_broadcast_domains_request.broadcast_domains[0].session_ids) == {"sess1"}
        assert set(req.set_broadcast_domains_request.broadcast_domains[1].session_ids) == {"sess2", "sess3"}

    @pytest.mark.asyncio
    async def test_empty_domains(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_set_broadcast_domains(conn, [])

        req = conn._captured_request
        assert len(req.set_broadcast_domains_request.broadcast_domains) == 0


class TestAsyncClose:

    @pytest.mark.asyncio
    async def test_close_sessions(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_close(conn, sessions=["sess1", "sess2"])

        req = conn._captured_request
        assert req.HasField("close_request")
        assert set(req.close_request.sessions.session_ids) == {"sess1", "sess2"}
        assert req.close_request.force is False

    @pytest.mark.asyncio
    async def test_close_tabs(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_close(conn, tabs=["tab1"])

        req = conn._captured_request
        assert "tab1" in req.close_request.tabs.tab_ids

    @pytest.mark.asyncio
    async def test_close_windows(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_close(conn, windows=["win1", "win2"])

        req = conn._captured_request
        assert set(req.close_request.windows.window_ids) == {"win1", "win2"}

    @pytest.mark.asyncio
    async def test_close_with_force(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_close(conn, sessions=["sess1"], force=True)

        req = conn._captured_request
        assert req.close_request.force is True

    @pytest.mark.asyncio
    async def test_raises_when_nothing_to_close(self):
        conn = make_mock_connection()
        with pytest.raises(AssertionError):
            await iterm2.rpc.async_close(conn)

    @pytest.mark.asyncio
    async def test_raises_when_multiple_types(self):
        conn = make_mock_connection()
        with pytest.raises(AssertionError):
            await iterm2.rpc.async_close(conn, sessions=["s1"], tabs=["t1"])


class TestAsyncInvokeFunction:

    @pytest.mark.asyncio
    async def test_with_receiver(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(
            conn, "myFunc", receiver="receiver1")

        req = conn._captured_request
        assert req.HasField("invoke_function_request")
        assert req.invoke_function_request.invocation == "myFunc"
        assert req.invoke_function_request.method.receiver == "receiver1"

    @pytest.mark.asyncio
    async def test_with_session_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(
            conn, "myFunc", session_id="sess1")

        req = conn._captured_request
        assert req.invoke_function_request.session.session_id == "sess1"

    @pytest.mark.asyncio
    async def test_with_tab_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(
            conn, "myFunc", tab_id="tab1")

        req = conn._captured_request
        assert req.invoke_function_request.tab.tab_id == "tab1"

    @pytest.mark.asyncio
    async def test_with_window_id(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(
            conn, "myFunc", window_id="win1")

        req = conn._captured_request
        assert req.invoke_function_request.window.window_id == "win1"

    @pytest.mark.asyncio
    async def test_app_level(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(conn, "myFunc")

        req = conn._captured_request
        assert req.invoke_function_request.HasField("app")

    @pytest.mark.asyncio
    async def test_with_timeout(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(
            conn, "myFunc", timeout=30.0)

        req = conn._captured_request
        assert req.invoke_function_request.timeout == 30.0

    @pytest.mark.asyncio
    async def test_default_timeout(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_invoke_function(conn, "myFunc")

        req = conn._captured_request
        assert req.invoke_function_request.timeout == -1


class TestAsyncInvokeMethod:

    @pytest.mark.asyncio
    async def test_success_response(self):
        conn = make_mock_connection()

        response = iterm2.api_pb2.ServerOriginatedMessage()
        response.invoke_function_response.success.json_result = json.dumps({"result": 42})
        conn.async_dispatch_until_id.return_value = response

        result = await iterm2.rpc.async_invoke_method(conn, "receiver1", "myMethod", 10)

        assert result == {"result": 42}

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        conn = make_mock_connection()

        response = iterm2.api_pb2.ServerOriginatedMessage()
        response.invoke_function_response.error.status = iterm2.api_pb2.InvokeFunctionResponse.Status.Value("TIMEOUT")
        response.invoke_function_response.error.error_reason = "timed out"
        conn.async_dispatch_until_id.return_value = response

        with pytest.raises(iterm2.rpc.RPCException) as exc_info:
            await iterm2.rpc.async_invoke_method(conn, "receiver1", "myMethod", 10)
        assert "Timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_failed_error(self):
        conn = make_mock_connection()

        response = iterm2.api_pb2.ServerOriginatedMessage()
        response.invoke_function_response.error.status = iterm2.api_pb2.InvokeFunctionResponse.Status.Value("FAILED")
        response.invoke_function_response.error.error_reason = "something bad"
        conn.async_dispatch_until_id.return_value = response

        with pytest.raises(iterm2.rpc.RPCException) as exc_info:
            await iterm2.rpc.async_invoke_method(conn, "receiver1", "myMethod", 10)
        assert "FAILED" in str(exc_info.value)
        assert "something bad" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_without_receiver(self):
        conn = make_mock_connection()
        with pytest.raises(AssertionError):
            await iterm2.rpc.async_invoke_method(conn, None, "myMethod", 10)


class TestAsyncNotificationRequest:

    @pytest.mark.asyncio
    async def test_subscribe_basic(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE)

        req = conn._captured_request
        assert req.HasField("notification_request")
        assert req.notification_request.subscribe is True
        assert req.notification_request.notification_type == iterm2.api_pb2.NOTIFY_ON_KEYSTROKE

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_notification_request(
            conn, False, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE)

        req = conn._captured_request
        assert req.notification_request.subscribe is False

    @pytest.mark.asyncio
    async def test_with_session(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE, session="sess1")

        req = conn._captured_request
        assert req.notification_request.session == "sess1"

    @pytest.mark.asyncio
    async def test_with_rpc_registration_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        rpc_reg = iterm2.api_pb2.RPCRegistrationRequest()
        rpc_reg.name = "myFunc"

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_SERVER_ORIGINATED_RPC,
            rpc_registration_request=rpc_reg)

        req = conn._captured_request
        assert req.notification_request.rpc_registration_request.name == "myFunc"

    @pytest.mark.asyncio
    async def test_with_keystroke_monitor_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        ks_mon = iterm2.api_pb2.KeystrokeMonitorRequest()
        ks_mon.advanced = True

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE,
            keystroke_monitor_request=ks_mon)

        req = conn._captured_request
        assert req.notification_request.keystroke_monitor_request.advanced is True

    @pytest.mark.asyncio
    async def test_with_keystroke_filter_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        ks_filter = iterm2.api_pb2.KeystrokeFilterRequest()
        ks_filter.patterns_to_ignore.add(characters=["c"])

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.KEYSTROKE_FILTER,
            keystroke_filter_request=ks_filter)

        req = conn._captured_request
        assert len(req.notification_request.keystroke_filter_request.patterns_to_ignore) == 1

    @pytest.mark.asyncio
    async def test_with_variable_monitor_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        var_mon = iterm2.api_pb2.VariableMonitorRequest()
        var_mon.name = "myVar"

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE,
            variable_monitor_request=var_mon)

        req = conn._captured_request
        assert req.notification_request.variable_monitor_request.name == "myVar"

    @pytest.mark.asyncio
    async def test_with_profile_change_request(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        prof_change = iterm2.api_pb2.ProfileChangeRequest()
        prof_change.guid = "guid1"

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_PROFILE_CHANGE,
            profile_change_request=prof_change)

        req = conn._captured_request
        assert req.notification_request.profile_change_request.guid == "guid1"

    @pytest.mark.asyncio
    async def test_with_prompt_monitor_modes(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_notification_request(
            conn, True, iterm2.api_pb2.NOTIFY_ON_PROMPT,
            prompt_monitor_modes=[
                iterm2.api_pb2.PROMPT,
                iterm2.api_pb2.COMMAND_START,
            ])

        req = conn._captured_request
        assert iterm2.api_pb2.PROMPT in req.notification_request.prompt_monitor_request.modes
        assert iterm2.api_pb2.COMMAND_START in req.notification_request.prompt_monitor_request.modes

    @pytest.mark.asyncio
    async def test_session_subscribe_and_notification_type(self):
        conn = make_mock_connection()
        conn._captured_request = None

        original_send = conn.async_send_message
        async def capture_send(req):
            conn._captured_request = req
            await original_send(req)
        conn.async_send_message = capture_send

        await iterm2.rpc.async_notification_request(
            conn, False, iterm2.api_pb2.NOTIFY_ON_TERMINATE_SESSION,
            session="sess1")

        req = conn._captured_request
        assert req.notification_request.session == "sess1"
        assert req.notification_request.subscribe is False
        assert req.notification_request.notification_type == iterm2.api_pb2.NOTIFY_ON_TERMINATE_SESSION
