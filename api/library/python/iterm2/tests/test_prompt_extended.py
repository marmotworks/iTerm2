import asyncio
import unittest.mock as mock

import pytest
import iterm2
import iterm2.prompt
import iterm2.util
import iterm2.rpc
import iterm2.capabilities
import iterm2.notifications


class TestPromptStateEdgeCases:
    def test_unknown_value_is_negative(self):
        assert iterm2.prompt.PromptState.UNKNOWN.value < 0

    def test_editing_is_zero(self):
        assert iterm2.prompt.PromptState.EDITING.value == 0

    def test_running_value(self):
        assert iterm2.prompt.PromptState.RUNNING.value == 1

    def test_finished_value(self):
        assert iterm2.prompt.PromptState.FINISHED.value == 3

    def test_from_int_unknown(self):
        state = iterm2.prompt.PromptState(-1)
        assert state == iterm2.prompt.PromptState.UNKNOWN

    def test_from_int_editing(self):
        state = iterm2.prompt.PromptState(0)
        assert state == iterm2.prompt.PromptState.EDITING

    def test_from_int_running(self):
        state = iterm2.prompt.PromptState(1)
        assert state == iterm2.prompt.PromptState.RUNNING

    def test_from_int_finished(self):
        state = iterm2.prompt.PromptState(3)
        assert state == iterm2.prompt.PromptState.FINISHED

    def test_state_count(self):
        assert len(iterm2.prompt.PromptState) == 4


class TestPromptAllStates:
    def _make_proto(self, state):
        from iterm2.api_pb2 import GetPromptResponse
        proto = GetPromptResponse()
        proto.status = iterm2.api_pb2.GetPromptResponse.Status.Value("OK")
        proto.prompt_state = state
        return proto

    def test_state_editing(self):
        proto = self._make_proto(iterm2.prompt.PromptState.EDITING.value)
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.state == iterm2.prompt.PromptState.EDITING

    def test_state_running(self):
        proto = self._make_proto(iterm2.prompt.PromptState.RUNNING.value)
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.state == iterm2.prompt.PromptState.RUNNING


class TestPromptEmptyFields:
    def _make_minimal_proto(self):
        from iterm2.api_pb2 import GetPromptResponse
        proto = GetPromptResponse()
        proto.status = iterm2.api_pb2.GetPromptResponse.Status.Value("OK")
        return proto

    def test_working_directory_empty(self):
        proto = self._make_minimal_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.working_directory == ""

    def test_command_empty(self):
        proto = self._make_minimal_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.command == ""

    def test_prompt_range_defaults(self):
        proto = self._make_minimal_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.prompt_range
        assert isinstance(rng, iterm2.util.CoordRange)
        assert rng.start.x == 0
        assert rng.start.y == 0
        assert rng.end.x == 0
        assert rng.end.y == 0

    def test_command_range_defaults(self):
        proto = self._make_minimal_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.command_range
        assert rng.start.x == 0
        assert rng.end.x == 0

    def test_output_range_defaults(self):
        proto = self._make_minimal_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.output_range
        assert rng.start.x == 0
        assert rng.end.x == 0

    def test_all_optional_fields_missing(self):
        proto = self._make_minimal_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.state == iterm2.prompt.PromptState.UNKNOWN
        assert prompt.unique_id is None
        assert prompt.working_directory == ""
        assert prompt.command == ""


class TestPromptMultiLineRanges:
    def _make_proto(self):
        from iterm2.api_pb2 import GetPromptResponse
        proto = GetPromptResponse()
        proto.status = iterm2.api_pb2.GetPromptResponse.Status.Value("OK")
        proto.prompt_range.start.x = 0
        proto.prompt_range.start.y = 5
        proto.prompt_range.end.x = 79
        proto.prompt_range.end.y = 7
        proto.command_range.start.x = 0
        proto.command_range.start.y = 8
        proto.command_range.end.x = 40
        proto.command_range.end.y = 10
        proto.output_range.start.x = 0
        proto.output_range.start.y = 10
        proto.output_range.end.x = 79
        proto.output_range.end.y = 24
        return proto

    def test_prompt_range_multiline(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.prompt_range
        assert rng.start.y == 5
        assert rng.end.y == 7
        assert rng.start.x == 0
        assert rng.end.x == 79

    def test_command_range_multiline(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.command_range
        assert rng.start.y == 8
        assert rng.end.y == 10

    def test_output_range_multiline(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.output_range
        assert rng.start.y == 10
        assert rng.end.y == 24


@pytest.mark.asyncio
class TestAsyncGetLastPrompt:
    def _make_response(self, status_str):
        from iterm2.api_pb2 import GetPromptResponse, ServerOriginatedMessage
        msg = ServerOriginatedMessage()
        msg.get_prompt_response.status = iterm2.api_pb2.GetPromptResponse.Status.Value(status_str)
        if status_str == "OK":
            msg.get_prompt_response.working_directory = "/home/user"
            msg.get_prompt_response.command = "echo hello"
            msg.get_prompt_response.unique_prompt_id = "pid-99"
        return mock.AsyncMock(return_value=msg)

    async def test_ok_returns_prompt(self):
        mock_rpc = self._make_response("OK")
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            conn = mock.Mock()
            result = await iterm2.prompt.async_get_last_prompt(conn, "sess-1")
        assert result is not None
        assert isinstance(result, iterm2.prompt.Prompt)
        assert result.working_directory == "/home/user"
        assert result.command == "echo hello"
        assert result.unique_id == "pid-99"

    async def test_prompt_unavailable_returns_none(self):
        mock_rpc = self._make_response("PROMPT_UNAVAILABLE")
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            conn = mock.Mock()
            result = await iterm2.prompt.async_get_last_prompt(conn, "sess-1")
        assert result is None

    async def test_session_not_found_raises_rpc_exception(self):
        mock_rpc = self._make_response("SESSION_NOT_FOUND")
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            conn = mock.Mock()
            with pytest.raises(iterm2.rpc.RPCException):
                await iterm2.prompt.async_get_last_prompt(conn, "sess-1")

    async def test_request_malformed_raises_rpc_exception(self):
        mock_rpc = self._make_response("REQUEST_MALFORMED")
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            conn = mock.Mock()
            with pytest.raises(iterm2.rpc.RPCException):
                await iterm2.prompt.async_get_last_prompt(conn, "sess-1")


@pytest.mark.asyncio
class TestAsyncGetPromptById:
    def _make_response(self, status_str):
        from iterm2.api_pb2 import GetPromptResponse, ServerOriginatedMessage
        msg = ServerOriginatedMessage()
        msg.get_prompt_response.status = iterm2.api_pb2.GetPromptResponse.Status.Value(status_str)
        if status_str == "OK":
            msg.get_prompt_response.unique_prompt_id = "pid-42"
        return mock.AsyncMock(return_value=msg)

    async def test_ok_returns_prompt(self):
        mock_rpc = self._make_response("OK")
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            result = await iterm2.prompt.async_get_prompt_by_id(mock_conn, "sess-1", "pid-42")
        assert result is not None
        assert result.unique_id == "pid-42"

    async def test_prompt_unavailable_returns_none(self):
        mock_rpc = self._make_response("PROMPT_UNAVAILABLE")
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            result = await iterm2.prompt.async_get_prompt_by_id(mock_conn, "sess-1", "pid-42")
        assert result is None

    async def test_session_not_found_raises_rpc_exception(self):
        mock_rpc = self._make_response("SESSION_NOT_FOUND")
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            with pytest.raises(iterm2.rpc.RPCException):
                await iterm2.prompt.async_get_prompt_by_id(mock_conn, "sess-1", "pid-42")

    async def test_request_malformed_raises_rpc_exception(self):
        mock_rpc = self._make_response("REQUEST_MALFORMED")
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            with pytest.raises(iterm2.rpc.RPCException):
                await iterm2.prompt.async_get_prompt_by_id(mock_conn, "sess-1", "pid-42")

    async def test_old_version_raises_app_version_too_old(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(0, 99))
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            await iterm2.prompt.async_get_prompt_by_id(mock_conn, "sess-1", "pid-42")

    async def test_calls_rpc_with_prompt_id(self):
        mock_rpc = self._make_response("OK")
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_get_prompt', mock_rpc):
            await iterm2.prompt.async_get_prompt_by_id(mock_conn, "sess-1", "pid-42")
        mock_rpc.assert_called_once_with(mock_conn, "sess-1", "pid-42")


@pytest.mark.asyncio
class TestAsyncListPrompts:
    def _make_response(self, status_str, prompt_ids=None):
        from iterm2.api_pb2 import ListPromptsResponse, ServerOriginatedMessage
        msg = ServerOriginatedMessage()
        msg.list_prompts_response.status = iterm2.api_pb2.ListPromptsResponse.Status.Value(status_str)
        if status_str == "OK" and prompt_ids:
            msg.list_prompts_response.unique_prompt_id.extend(prompt_ids)
        return mock.AsyncMock(return_value=msg)

    async def test_ok_returns_prompt_ids(self):
        mock_rpc = self._make_response("OK", ["id-1", "id-2", "id-3"])
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_list_prompts', mock_rpc):
            result = await iterm2.prompt.async_list_prompts(mock_conn, "sess-1")
        assert result == ["id-1", "id-2", "id-3"]

    async def test_ok_empty_list(self):
        mock_rpc = self._make_response("OK", [])
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_list_prompts', mock_rpc):
            result = await iterm2.prompt.async_list_prompts(mock_conn, "sess-1")
        assert result == []

    async def test_session_not_found_raises_rpc_exception(self):
        mock_rpc = self._make_response("SESSION_NOT_FOUND")
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_list_prompts', mock_rpc):
            with pytest.raises(iterm2.rpc.RPCException):
                await iterm2.prompt.async_list_prompts(mock_conn, "sess-1")

    async def test_old_version_raises_app_version_too_old(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(0, 99))
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            await iterm2.prompt.async_list_prompts(mock_conn, "sess-1")

    async def test_passes_first_and_last(self):
        mock_rpc = self._make_response("OK", ["id-1"])
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_list_prompts', mock_rpc):
            await iterm2.prompt.async_list_prompts(mock_conn, "sess-1", first="f1", last="l1")
        mock_rpc.assert_called_once_with(mock_conn, "sess-1", "f1", "l1")

    async def test_passes_none_for_first_and_last(self):
        mock_rpc = self._make_response("OK", ["id-1"])
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 5))
        with mock.patch.object(iterm2.rpc, 'async_list_prompts', mock_rpc):
            await iterm2.prompt.async_list_prompts(mock_conn, "sess-1")
        mock_rpc.assert_called_once_with(mock_conn, "sess-1", None, None)


class TestPromptMonitorInit:
    def test_default_modes(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")
        assert mon.connection == mock_conn
        assert mon.session_id == "sess-1"
        assert mon._PromptMonitor__modes == [iterm2.prompt.PromptMonitor.Mode.PROMPT]

    def test_custom_modes(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        modes = [
            iterm2.prompt.PromptMonitor.Mode.COMMAND_START,
            iterm2.prompt.PromptMonitor.Mode.COMMAND_END,
        ]
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1", modes=modes)
        assert mon._PromptMonitor__modes == modes

    def test_all_modes(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        modes = list(iterm2.prompt.PromptMonitor.Mode)
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1", modes=modes)
        assert len(mon._PromptMonitor__modes) == len(modes)

    def test_old_version_non_default_modes_raises(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(0, 99))
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.prompt.PromptMonitor(
                mock_conn, "sess-1",
                modes=[iterm2.prompt.PromptMonitor.Mode.COMMAND_START])

    def test_old_version_default_modes_does_not_raise(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(0, 99))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")
        assert mon is not None

    def test_queue_created(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")
        assert isinstance(mon._PromptMonitor__queue, asyncio.Queue)
        assert mon._PromptMonitor__queue.empty()

    def test_token_initially_none(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")
        assert mon._PromptMonitor__token is None


class TestPromptMonitorModeValues:
    def test_prompt_mode_value_is_int(self):
        assert isinstance(iterm2.prompt.PromptMonitor.Mode.PROMPT.value, int)

    def test_command_start_mode_value_is_int(self):
        assert isinstance(iterm2.prompt.PromptMonitor.Mode.COMMAND_START.value, int)

    def test_command_end_mode_value_is_int(self):
        assert isinstance(iterm2.prompt.PromptMonitor.Mode.COMMAND_END.value, int)

    def test_all_mode_values_distinct(self):
        values = [m.value for m in iterm2.prompt.PromptMonitor.Mode]
        assert len(values) == len(set(values))


@pytest.mark.asyncio
class TestPromptMonitorAsyncGet:
    async def test_async_get_include_id_false(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        msg.command_start.SetInParent()
        msg.command_start.command = "ls -la"
        msg.unique_prompt_id = "pid-77"
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get(include_id=False)
        assert len(result) == 2
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.COMMAND_START
        assert result[1] == "ls -la"

    async def test_async_get_include_id_true(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        msg.command_start.SetInParent()
        msg.command_start.command = "ls -la"
        msg.unique_prompt_id = "pid-77"
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get(include_id=True)
        assert len(result) == 3
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.COMMAND_START
        assert result[1] == "ls -la"
        assert result[2] == "pid-77"

    async def test_async_get_command_end(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        msg.command_end.SetInParent()
        msg.command_end.status = 0
        msg.unique_prompt_id = "pid-88"
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get(include_id=True)
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.COMMAND_END
        assert result[1] == 0
        assert result[2] == "pid-88"

    async def test_async_get_command_end_nonzero_status(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        msg.command_end.SetInParent()
        msg.command_end.status = 1
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get()
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.COMMAND_END
        assert result[1] == 1

    async def test_async_get_prompt_with_prompt_object(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification, GetPromptResponse
        msg = PromptNotification()
        msg.prompt.SetInParent()
        msg.prompt.prompt.status = iterm2.api_pb2.GetPromptResponse.Status.Value("OK")
        msg.prompt.prompt.working_directory = "/src"
        msg.unique_prompt_id = "pid-prompt"
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get(include_id=True)
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.PROMPT
        assert isinstance(result[1], iterm2.prompt.Prompt)
        assert result[1].working_directory == "/src"
        assert result[2] == "pid-prompt"

    async def test_async_get_prompt_no_prompt_object(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        msg.prompt.SetInParent()
        msg.unique_prompt_id = "pid-empty"
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get(include_id=True)
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.PROMPT
        assert result[1] is None
        assert result[2] == "pid-empty"

    async def test_async_get_old_version_returns_none_prompt(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(0, 99))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        msg.prompt.SetInParent()
        msg.prompt.prompt.status = iterm2.api_pb2.GetPromptResponse.Status.Value("OK")
        msg.prompt.prompt.working_directory = "/src"
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get(include_id=True)
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.PROMPT
        assert result[1] is None
        assert result[2] is None

    async def test_async_get_no_event_returns_prompt_none(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        from iterm2.api_pb2 import PromptNotification
        msg = PromptNotification()
        mon._PromptMonitor__queue.put_nowait(msg)

        result = await mon.async_get()
        assert result[0] == iterm2.prompt.PromptMonitor.Mode.PROMPT
        assert result[1] is None


@pytest.mark.asyncio
class TestPromptMonitorContextManager:
    async def test_aenter_subscribes_and_returns_self(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")

        mock_token = mock.Mock()
        async def mock_subscribe(*args, **kwargs):
            return mock_token

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_prompt_notification',
            mock_subscribe,
        ):
            result = await mon.__aenter__()

        assert result is mon
        assert mon._PromptMonitor__token == mock_token

    async def test_aexit_unsubscribes(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")
        mon._PromptMonitor__token = mock.Mock()

        async def mock_unsubscribe(conn, token):
            pass

        with mock.patch.object(
            iterm2.notifications,
            'async_unsubscribe',
            mock_unsubscribe,
        ):
            await mon.__aexit__(None, None, None)

    async def test_aexit_handles_subscription_exception(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1")
        mon._PromptMonitor__token = mock.Mock()

        async def mock_unsubscribe(conn, token):
            raise iterm2.notifications.SubscriptionException("gone")

        with mock.patch.object(
            iterm2.notifications,
            'async_unsubscribe',
            mock_unsubscribe,
        ):
            await mon.__aexit__(None, None, None)

    async def test_aenter_passes_modes_to_subscribe(self):
        mock_conn = mock.Mock(iterm2_protocol_version=(1, 1))
        modes = [
            iterm2.prompt.PromptMonitor.Mode.COMMAND_START,
            iterm2.prompt.PromptMonitor.Mode.COMMAND_END,
        ]
        mon = iterm2.prompt.PromptMonitor(mock_conn, "sess-1", modes=modes)

        captured_modes = None
        async def mock_subscribe(conn, cb, session, prompt_monitor_modes):
            nonlocal captured_modes
            captured_modes = prompt_monitor_modes
            return mock.Mock()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_prompt_notification',
            mock_subscribe,
        ):
            await mon.__aenter__()

        expected_values = [m.value for m in modes]
        assert captured_modes == expected_values


class TestPromptMonitorModeEnumIntegrity:
    def test_mode_enum_iterable(self):
        modes = list(iterm2.prompt.PromptMonitor.Mode)
        assert len(modes) == 3

    def test_mode_enum_names(self):
        names = {m.name for m in iterm2.prompt.PromptMonitor.Mode}
        assert names == {"PROMPT", "COMMAND_START", "COMMAND_END"}
