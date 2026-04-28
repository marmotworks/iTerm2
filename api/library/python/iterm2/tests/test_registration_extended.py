import asyncio
import inspect
import json
import unittest.mock as mock
import pytest
import websockets.exceptions

import iterm2
import iterm2.registration
import iterm2.notifications
import iterm2.api_pb2


def _make_rpc_notification(request_id=1, arguments=None):
    """Build a proper notification with server_originated_rpc_notification field."""
    notif = mock.Mock()
    server_rpc_notif = mock.Mock()
    server_rpc_notif.request_id = request_id
    rpc = iterm2.api_pb2.ServerOriginatedRPC()
    if arguments:
        for name, json_value in arguments:
            arg = rpc.arguments.add()
            arg.name = name
            if json_value is not None:
                arg.json_value = json_value
    server_rpc_notif.rpc = rpc
    notif.server_originated_rpc_notification = server_rpc_notif
    return notif


class TestGenericHandleRPCSuccess:
    @pytest.mark.asyncio
    async def test_successful_coroutine_sends_result(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def my_coro(x, y):
            return x + y

        notif = _make_rpc_notification(
            request_id=123,
            arguments=[
                ("x", json.dumps(10)),
                ("y", json.dumps(20)),
            ],
        )

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(my_coro, connection, notif)

            mock_send.assert_called_once_with(
                connection, 123, False, 30,
            )

    @pytest.mark.asyncio
    async def test_parses_json_arguments(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        received_args = {}

        async def capture_coro(**kwargs):
            received_args.update(kwargs)
            return "ok"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("data", json.dumps({"nested": True}))],
        )

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            await iterm2.registration.generic_handle_rpc(capture_coro, connection, notif)

        assert received_args["data"] == {"nested": True}

    @pytest.mark.asyncio
    async def test_handles_null_json_argument(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        received_args = {}

        async def capture_coro(opt=None):
            received_args["opt"] = opt
            return "ok"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("opt", None)],
        )

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            await iterm2.registration.generic_handle_rpc(capture_coro, connection, notif)

        assert received_args["opt"] is None

    @pytest.mark.asyncio
    async def test_empty_arguments(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def no_args_coro():
            return "ok"

        notif = _make_rpc_notification(request_id=1, arguments=[])

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(no_args_coro, connection, notif)

            mock_send.assert_called_once_with(connection, 1, False, "ok")


class TestGenericHandleRPCExceptionHandling:
    @pytest.mark.asyncio
    async def test_sends_exception_result_on_error(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def failing_coro():
            raise ValueError("something broke")

        notif = _make_rpc_notification(request_id=42, arguments=[])

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(failing_coro, connection, notif)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] is connection
            assert call_args[1] == 42
            assert call_args[2] is True
            exc_info = call_args[3]
            assert isinstance(exc_info, dict)
            assert "reason" in exc_info
            assert "traceback" in exc_info
            assert "something broke" in exc_info["reason"]

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_reraised(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def interrupt_coro():
            raise KeyboardInterrupt("stop")

        notif = _make_rpc_notification(request_id=1, arguments=[])

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            with pytest.raises(KeyboardInterrupt):
                await iterm2.registration.generic_handle_rpc(
                    interrupt_coro, connection, notif,
                )

    @pytest.mark.asyncio
    async def test_connection_closed_reraised(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def disconnect_coro():
            raise websockets.exceptions.ConnectionClosed(None, None)

        notif = _make_rpc_notification(request_id=1, arguments=[])

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            with pytest.raises(websockets.exceptions.ConnectionClosed):
                await iterm2.registration.generic_handle_rpc(
                    disconnect_coro, connection, notif,
                )

    @pytest.mark.asyncio
    async def test_type_error_included_in_exception_result(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def type_error_coro(x):
            return x + "string"

        notif = _make_rpc_notification(request_id=7, arguments=[])

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(
                type_error_coro, connection, notif,
            )

            call_args = mock_send.call_args[0]
            assert call_args[2] is True
            exc_info = call_args[3]
            assert "TypeError" in exc_info["reason"]

    @pytest.mark.asyncio
    async def test_traceback_included_in_exception_result(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def failing_coro():
            raise RuntimeError("fail")

        notif = _make_rpc_notification(request_id=1, arguments=[])

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(failing_coro, connection, notif)

            exc_info = mock_send.call_args[0][3]
            tb = exc_info["traceback"]
            assert isinstance(tb, str)
            assert len(tb) > 0
            assert "RuntimeError" in tb

    @pytest.mark.asyncio
    async def test_successful_does_not_send_exception(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def ok_coro():
            return "success"

        notif = _make_rpc_notification(request_id=1, arguments=[])

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(ok_coro, connection, notif)

            call_args = mock_send.call_args[0]
            assert call_args[2] is False
            assert call_args[3] == "success"

    @pytest.mark.asyncio
    async def test_exception_does_not_send_success(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        async def failing_coro():
            raise ValueError("oops")

        notif = _make_rpc_notification(request_id=1, arguments=[])

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(failing_coro, connection, notif)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[2] is True


class TestGenericHandleRPCJsonParsing:
    @pytest.mark.asyncio
    async def test_parses_nested_json(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        received = {}

        async def capture(**kwargs):
            received.update(kwargs)
            return "ok"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("config", json.dumps(
                {"level1": {"level2": [1, 2, {"deep": True}]}},
            ))],
        )

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            await iterm2.registration.generic_handle_rpc(capture, connection, notif)

        assert received["config"] == {"level1": {"level2": [1, 2, {"deep": True}]}}

    @pytest.mark.asyncio
    async def test_parses_empty_string_json(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        received = {}

        async def capture(val=None):
            received["val"] = val
            return "ok"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("val", '""')],
        )

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            await iterm2.registration.generic_handle_rpc(capture, connection, notif)

        assert received["val"] == ""

    @pytest.mark.asyncio
    async def test_parses_array_json(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        received = {}

        async def capture(items=None):
            received["items"] = items
            return "ok"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("items", json.dumps([1, 2, 3]))],
        )

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            await iterm2.registration.generic_handle_rpc(capture, connection, notif)

        assert received["items"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_parses_bool_json(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        received = {}

        async def capture(flag=None):
            received["flag"] = flag
            return "ok"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("flag", json.dumps(True))],
        )

        with mock.patch.object(iterm2.rpc, 'async_send_rpc_result'):
            await iterm2.registration.generic_handle_rpc(capture, connection, notif)

        assert received["flag"] is True


class TestReferenceEdgeCases:
    def test_empty_name(self):
        ref = iterm2.registration.Reference("")
        assert ref.name == ""
        assert repr(ref) == ""

    def test_unicode_name(self):
        ref = iterm2.registration.Reference("session_日本語")
        assert ref.name == "session_日本語"
        assert repr(ref) == "session_日本語"

    def test_name_with_spaces(self):
        ref = iterm2.registration.Reference("my variable")
        assert ref.name == "my variable"
        assert repr(ref) == "my variable"

    def test_name_with_dots(self):
        ref = iterm2.registration.Reference("com.example.var")
        assert ref.name == "com.example.var"
        assert repr(ref) == "com.example.var"

    def test_reference_equality(self):
        ref1 = iterm2.registration.Reference("id")
        ref2 = iterm2.registration.Reference("id")
        assert ref1.name == ref2.name
        assert repr(ref1) == repr(ref2)

    def test_reference_identity(self):
        ref = iterm2.registration.Reference("x")
        assert ref is ref

    def test_reference_is_not_string(self):
        ref = iterm2.registration.Reference("id")
        assert not isinstance(ref, str)

    def test_reference_with_question_mark(self):
        ref = iterm2.registration.Reference("autoName?")
        assert ref.name == "autoName?"
        assert repr(ref) == "autoName?"


class TestRPCDecoratorSignatures:
    def test_async_register_is_coroutine_function(self):
        @iterm2.registration.RPC
        async def my_rpc(x):
            return x

        assert inspect.iscoroutinefunction(my_rpc.async_register)

    def test_decorated_function_preserves_name(self):
        @iterm2.registration.RPC
        async def my_special_rpc():
            return "ok"

        assert my_special_rpc.__name__ == "my_special_rpc"

    def test_decorated_function_with_many_args(self):
        @iterm2.registration.RPC
        async def multi_arg_rpc(a, b, c, d=10, e="default"):
            return a + b + c + d

        assert hasattr(multi_arg_rpc, 'async_register')
        assert multi_arg_rpc.__name__ == "multi_arg_rpc"

    def test_decorated_function_with_reference_default(self):
        @iterm2.registration.RPC
        async def ref_rpc(
            session_id=iterm2.registration.Reference("id"),
            title=iterm2.registration.Reference("title"),
        ):
            return f"{session_id}: {title}"

        assert hasattr(ref_rpc, 'async_register')
        assert ref_rpc.__name__ == "ref_rpc"

    def test_decorated_function_no_args(self):
        @iterm2.registration.RPC
        async def no_args_rpc():
            return "no args"

        assert hasattr(no_args_rpc, 'async_register')
        assert no_args_rpc.__name__ == "no_args_rpc"


class TestContextMenuProviderRPCDecorator:
    def test_async_register_is_coroutine(self):
        @iterm2.registration.ContextMenuProviderRPC
        async def my_menu(x):
            return x

        assert inspect.iscoroutinefunction(my_menu.async_register)

    def test_preserves_name(self):
        @iterm2.registration.ContextMenuProviderRPC
        async def context_menu_handler(data):
            return data

        assert context_menu_handler.__name__ == "context_menu_handler"

    def test_with_reference_default(self):
        @iterm2.registration.ContextMenuProviderRPC
        async def menu_with_ref(session_id=iterm2.registration.Reference("id")):
            return session_id

        assert hasattr(menu_with_ref, 'async_register')


class TestTitleProviderRPCDecorator:
    def test_async_register_is_coroutine(self):
        @iterm2.registration.TitleProviderRPC
        async def my_title(name):
            return name

        assert inspect.iscoroutinefunction(my_title.async_register)

    def test_preserves_name(self):
        @iterm2.registration.TitleProviderRPC
        async def title_fn(auto_name=iterm2.registration.Reference("autoName?")):
            return auto_name or ""

        assert title_fn.__name__ == "title_fn"

    def test_with_multiple_references(self):
        @iterm2.registration.TitleProviderRPC
        async def complex_title(
            auto=iterm2.registration.Reference("autoName?"),
            cwd=iterm2.registration.Reference("cwd"),
        ):
            return f"{auto} {cwd}"

        assert hasattr(complex_title, 'async_register')


class TestStatusBarRPCDecorator:
    def test_async_register_is_coroutine(self):
        @iterm2.registration.StatusBarRPC
        async def my_bar(knobs):
            return "status"

        assert inspect.iscoroutinefunction(my_bar.async_register)

    def test_preserves_name(self):
        @iterm2.registration.StatusBarRPC
        async def status_component(knobs, session_id=iterm2.registration.Reference("id")):
            return session_id

        assert status_component.__name__ == "status_component"

    @pytest.mark.asyncio
    async def test_wrapper_parses_knobs_json(self):
        @iterm2.registration.StatusBarRPC
        async def knob_bar(knobs, session_id=iterm2.registration.Reference("id")):
            return f"knobs={knobs}, id={session_id}"

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[
                ("knobs", json.dumps({"color": "red", "size": 12})),
                ("session_id", json.dumps("sess-123")),
            ],
        )

        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(
                knob_bar, connection, notif,
            )

            result = mock_send.call_args[0][3]
            assert isinstance(result, str)
            assert "sess-123" in result

    @pytest.mark.asyncio
    async def test_wrapper_handles_empty_knobs(self):
        @iterm2.registration.StatusBarRPC
        async def no_knobs_bar(knobs):
            return knobs

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("knobs", json.dumps({}))],
        )

        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(
                no_knobs_bar, connection, notif,
            )

            result = mock_send.call_args[0][3]
            assert result == {}

    @pytest.mark.asyncio
    async def test_wrapper_with_complex_knobs(self):
        @iterm2.registration.StatusBarRPC
        async def complex_knobs(knobs):
            return knobs.get("items", [])

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("knobs", json.dumps({
                "items": ["a", "b", "c"],
                "config": {"enabled": True},
            }))],
        )

        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(
                complex_knobs, connection, notif,
            )

            result = mock_send.call_args[0][3]
            assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_wrapper_without_knobs_arg(self):
        @iterm2.registration.StatusBarRPC
        async def no_knobs_arg(session_id=iterm2.registration.Reference("id")):
            return session_id

        notif = _make_rpc_notification(
            request_id=1,
            arguments=[("session_id", json.dumps("sess-99"))],
        )

        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.rpc,
            'async_send_rpc_result',
        ) as mock_send:
            await iterm2.registration.generic_handle_rpc(
                no_knobs_arg, connection, notif,
            )

            result = mock_send.call_args[0][3]
            assert result == "sess-99"


class TestRPCDecoratorDoesNotCallSubscribe:
    def test_rpc_decorator_only_attaches_async_register(self):
        @iterm2.registration.RPC
        async def test_rpc(x):
            return x

        assert hasattr(test_rpc, 'async_register')
        assert not hasattr(test_rpc, 'rpc_token')
        assert not hasattr(test_rpc, 'rpc_connection')

    def test_context_menu_decorator_only_attaches_async_register(self):
        @iterm2.registration.ContextMenuProviderRPC
        async def test_menu(x):
            return x

        assert hasattr(test_menu, 'async_register')
        assert not hasattr(test_menu, 'rpc_token')

    def test_title_provider_decorator_only_attaches_async_register(self):
        @iterm2.registration.TitleProviderRPC
        async def test_title(name):
            return name

        assert hasattr(test_title, 'async_register')
        assert not hasattr(test_title, 'rpc_token')

    def test_status_bar_decorator_only_attaches_async_register(self):
        @iterm2.registration.StatusBarRPC
        async def test_bar(knobs):
            return "ok"

        assert hasattr(test_bar, 'async_register')
        assert not hasattr(test_bar, 'rpc_token')
