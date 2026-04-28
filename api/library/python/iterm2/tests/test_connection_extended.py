import asyncio
import pytest
import unittest.mock as mock
import os
import sys
import iterm2
import iterm2.connection
import iterm2.auth
import iterm2.api_pb2


class TestConnectionInit:
    def test_initial_state_all_fields(self):
        conn = iterm2.connection.Connection()
        assert conn.websocket is None
        assert conn.loop is None
        assert conn._Connection__dispatch_forever_future is None
        assert conn._Connection__tasks == []
        assert conn._Connection__receivers == []

    def test_multiple_inits_reset_state(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.loop = mock.MagicMock()
        conn2 = iterm2.connection.Connection()
        assert conn2.websocket is None
        assert conn2.loop is None


class TestCollectGarbage:
    def test_filters_done_tasks(self):
        conn = iterm2.connection.Connection()
        done_task = mock.MagicMock()
        done_task.done.return_value = True
        pending_task = mock.MagicMock()
        pending_task.done.return_value = False
        conn._Connection__tasks = [done_task, pending_task]
        conn._collect_garbage()
        assert conn._Connection__tasks == [pending_task]

    def test_removes_all_done_tasks(self):
        conn = iterm2.connection.Connection()
        t1 = mock.MagicMock()
        t1.done.return_value = True
        t2 = mock.MagicMock()
        t2.done.return_value = True
        conn._Connection__tasks = [t1, t2]
        conn._collect_garbage()
        assert conn._Connection__tasks == []

    def test_keeps_all_pending_tasks(self):
        conn = iterm2.connection.Connection()
        t1 = mock.MagicMock()
        t1.done.return_value = False
        t2 = mock.MagicMock()
        t2.done.return_value = False
        conn._Connection__tasks = [t1, t2]
        conn._collect_garbage()
        assert conn._Connection__tasks == [t1, t2]

    def test_empty_tasks_list(self):
        conn = iterm2.connection.Connection()
        conn._Connection__tasks = []
        conn._collect_garbage()
        assert conn._Connection__tasks == []


class TestSetMessageInFuture:
    def test_sets_result_on_pending_future(self):
        conn = iterm2.connection.Connection()
        loop = mock.MagicMock()
        future = mock.MagicMock()
        future.done.return_value = False
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 42
        conn.set_message_in_future(loop, msg, future)
        loop.call_soon.assert_called_once()
        callback = loop.call_soon.call_args[0][0]
        callback()
        future.set_result.assert_called_once_with(msg)

    def test_does_not_set_result_on_done_future(self):
        conn = iterm2.connection.Connection()
        loop = mock.MagicMock()
        future = mock.MagicMock()
        future.done.return_value = True
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        conn.set_message_in_future(loop, msg, future)
        callback = loop.call_soon.call_args[0][0]
        callback()
        future.set_result.assert_not_called()


class TestReceiverIndex:
    def test_found_receiver(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 1
        match_func = lambda m: m.id == 1
        conn._Connection__receivers = [(lambda m: False, mock.MagicMock()), (match_func, mock.MagicMock())]
        idx = conn._receiver_index(msg)
        assert idx == 1

    def test_no_matching_receiver(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 99
        conn._Connection__receivers = [(lambda m: m.id == 1, mock.MagicMock())]
        idx = conn._receiver_index(msg)
        assert idx is None

    def test_first_receiver_matches(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 5
        conn._Connection__receivers = [(lambda m: m.id == 5, mock.MagicMock())]
        idx = conn._receiver_index(msg)
        assert idx == 0

    def test_none_match_func_skipped(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        conn._Connection__receivers = [(None, mock.MagicMock())]
        idx = conn._receiver_index(msg)
        assert idx is None

    def test_empty_receivers(self):
        conn = iterm2.connection.Connection()
        conn._Connection__receivers = []
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        idx = conn._receiver_index(msg)
        assert idx is None


class TestGetReceiverFuture:
    def test_found_and_removed(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 7
        future = mock.MagicMock()
        conn._Connection__receivers = [(lambda m: m.id == 7, future)]
        result = conn._get_receiver_future(msg)
        assert result is future
        assert conn._Connection__receivers == []

    def test_not_found_returns_none(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 99
        future = mock.MagicMock()
        conn._Connection__receivers = [(lambda m: m.id == 1, future)]
        result = conn._get_receiver_future(msg)
        assert result is None
        assert len(conn._Connection__receivers) == 1

    def test_removes_correct_receiver_preserves_others(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 2
        f1 = mock.MagicMock()
        f2 = mock.MagicMock()
        f3 = mock.MagicMock()
        conn._Connection__receivers = [
            (lambda m: m.id == 1, f1),
            (lambda m: m.id == 2, f2),
            (lambda m: m.id == 3, f3),
        ]
        result = conn._get_receiver_future(msg)
        assert result is f2
        assert len(conn._Connection__receivers) == 2


class TestAsyncDispatchUntilId:
    @pytest.mark.asyncio
    async def test_registers_receiver_and_returns_message(self):
        conn = iterm2.connection.Connection()
        received_msg = iterm2.api_pb2.ServerOriginatedMessage()
        received_msg.id = 42
        loop = asyncio.get_event_loop()
        loop.call_soon(lambda: conn._Connection__receivers[0][1].set_result(received_msg))
        result = await conn.async_dispatch_until_id(42)
        assert result == received_msg
        # Receiver is removed by _get_receiver_future when dispatch loop runs;
        # here we just verify the receiver was registered and future resolved.
        assert len(conn._Connection__receivers) == 1
        # Verify _get_receiver_future removes it.
        returned_future = conn._get_receiver_future(received_msg)
        assert returned_future is not None
        assert len(conn._Connection__receivers) == 0

    @pytest.mark.asyncio
    async def test_match_func_checks_id(self):
        conn = iterm2.connection.Connection()
        wrong_msg = iterm2.api_pb2.ServerOriginatedMessage()
        wrong_msg.id = 99
        correct_msg = iterm2.api_pb2.ServerOriginatedMessage()
        correct_msg.id = 10
        loop = asyncio.get_event_loop()
        loop.call_soon(lambda: conn._Connection__receivers[0][1].set_result(correct_msg))
        result = await conn.async_dispatch_until_id(10)
        assert result.id == 10


class TestAsyncDispatchToHelper:
    @pytest.mark.asyncio
    async def test_iterates_helpers(self):
        conn = iterm2.connection.Connection()
        call_order = []

        async def helper1(c, m):
            call_order.append(1)
            return False

        async def helper2(c, m):
            call_order.append(2)
            return True

        iterm2.connection.Connection.helpers.append(helper1)
        iterm2.connection.Connection.helpers.append(helper2)
        try:
            msg = iterm2.api_pb2.ServerOriginatedMessage()
            await conn._async_dispatch_to_helper(msg)
            assert call_order == [1, 2]
        finally:
            iterm2.connection.Connection.helpers.remove(helper1)
            iterm2.connection.Connection.helpers.remove(helper2)

    @pytest.mark.asyncio
    async def test_breaks_on_true(self):
        conn = iterm2.connection.Connection()
        call_order = []

        async def helper1(c, m):
            call_order.append(1)
            return True

        async def helper2(c, m):
            call_order.append(2)
            return False

        iterm2.connection.Connection.helpers.append(helper1)
        iterm2.connection.Connection.helpers.append(helper2)
        try:
            msg = iterm2.api_pb2.ServerOriginatedMessage()
            await conn._async_dispatch_to_helper(msg)
            assert call_order == [1]
        finally:
            iterm2.connection.Connection.helpers.remove(helper1)
            iterm2.connection.Connection.helpers.remove(helper2)

    @pytest.mark.asyncio
    async def test_raises_on_helper_exception(self):
        conn = iterm2.connection.Connection()

        async def bad_helper(c, m):
            raise ValueError("boom")

        iterm2.connection.Connection.helpers.append(bad_helper)
        try:
            msg = iterm2.api_pb2.ServerOriginatedMessage()
            with pytest.raises(ValueError, match="boom"):
                await conn._async_dispatch_to_helper(msg)
        finally:
            iterm2.connection.Connection.helpers.remove(bad_helper)

    @pytest.mark.asyncio
    async def test_no_helpers(self):
        conn = iterm2.connection.Connection()
        initial_helpers = iterm2.connection.Connection.helpers.copy()
        iterm2.connection.Connection.helpers.clear()
        try:
            msg = iterm2.api_pb2.ServerOriginatedMessage()
            await conn._async_dispatch_to_helper(msg)
        finally:
            iterm2.connection.Connection.helpers.extend(initial_helpers)


class TestIterm2ProtocolVersion:
    def test_valid_version(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.websocket.response_headers = {"X-iTerm2-Protocol-Version": "3.4"}
        assert conn.iterm2_protocol_version == (3, 4)

    def test_missing_header(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.websocket.response_headers = {}
        assert conn.iterm2_protocol_version == (0, 0)

    def test_malformed_header_no_dot(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.websocket.response_headers = {"X-iTerm2-Protocol-Version": "3"}
        assert conn.iterm2_protocol_version == (0, 0)

    def test_malformed_header_three_parts(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.websocket.response_headers = {"X-iTerm2-Protocol-Version": "1.2.3"}
        assert conn.iterm2_protocol_version == (0, 0)

    def test_malformed_header_non_numeric(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.websocket.response_headers = {"X-iTerm2-Protocol-Version": "a.b"}
        with pytest.raises(ValueError):
            _ = conn.iterm2_protocol_version

    def test_zero_version(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.MagicMock()
        conn.websocket.response_headers = {"X-iTerm2-Protocol-Version": "0.0"}
        assert conn.iterm2_protocol_version == (0, 0)


class TestGetConnectCoro:
    @mock.patch('os.path.exists')
    def test_returns_unix_connect_when_socket_exists(self, mock_exists):
        mock_exists.return_value = True
        conn = iterm2.connection.Connection()
        with mock.patch.object(conn, '_get_unix_connect_coro') as mock_unix:
            mock_unix.return_value = mock.MagicMock()
            coro = conn._get_connect_coro()
            mock_unix.assert_called_once()

    @mock.patch('os.path.exists')
    def test_returns_tcp_connect_when_socket_missing(self, mock_exists):
        mock_exists.return_value = False
        conn = iterm2.connection.Connection()
        with mock.patch.object(conn, '_get_tcp_connect_coro') as mock_tcp:
            mock_tcp.return_value = mock.MagicMock()
            coro = conn._get_connect_coro()
            mock_tcp.assert_called_once()


class TestGetTcpConnectCoro:
    def test_returns_websocket_connect_coro(self):
        conn = iterm2.connection.Connection()
        with mock.patch('iterm2.connection.websockets_connect') as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            coro = conn._get_tcp_connect_coro()
            mock_connect.assert_called_once()
            call_args = mock_connect.call_args
            assert call_args[0][0] == "ws://localhost:1912"
            assert call_args[1]['ping_interval'] is None
            assert call_args[1]['close_timeout'] == 0


class TestAuthenticate:
    @mock.patch.object(iterm2.auth, 'authenticate')
    def test_success(self, mock_auth):
        mock_auth.return_value = True
        conn = iterm2.connection.Connection()
        result = conn.authenticate(False)
        assert result is True
        mock_auth.assert_called_once()

    @mock.patch.object(iterm2.auth, 'authenticate')
    def test_force_removes_auth_first(self, mock_auth):
        mock_auth.return_value = True
        os.environ['ITERM2_COOKIE'] = 'old'
        os.environ['ITERM2_KEY'] = 'old'
        try:
            conn = iterm2.connection.Connection()
            result = conn.authenticate(True)
            assert result is True
            assert 'ITERM2_COOKIE' not in os.environ
            assert 'ITERM2_KEY' not in os.environ
        finally:
            os.environ.pop('ITERM2_COOKIE', None)
            os.environ.pop('ITERM2_KEY', None)

    @mock.patch.object(iterm2.auth, 'authenticate')
    def test_authentication_exception_returns_false(self, mock_auth):
        mock_auth.side_effect = iterm2.auth.AuthenticationException("denied")
        conn = iterm2.connection.Connection()
        result = conn.authenticate(False)
        assert result is False

    @mock.patch.object(iterm2.auth, 'authenticate')
    def test_auth_returns_false_passthrough(self, mock_auth):
        mock_auth.return_value = False
        conn = iterm2.connection.Connection()
        result = conn.authenticate(False)
        assert result is False


class TestRunUntilComplete:
    def test_delegates_to_run(self):
        conn = iterm2.connection.Connection()
        with mock.patch.object(conn, 'run') as mock_run:
            mock_run.return_value = 42
            result = conn.run_until_complete(mock.MagicMock(), False)
            mock_run.assert_called_once_with(False, mock_run.call_args[0][1], False, False)

    def test_delegates_with_debug(self):
        conn = iterm2.connection.Connection()
        with mock.patch.object(conn, 'run') as mock_run:
            mock_run.return_value = None
            coro = mock.MagicMock()
            result = conn.run_until_complete(coro, True, debug=True)
            mock_run.assert_called_once_with(False, coro, True, True)


class TestRunForever:
    def test_delegates_to_run(self):
        conn = iterm2.connection.Connection()
        with mock.patch.object(conn, 'run') as mock_run:
            coro = mock.MagicMock()
            conn.run_forever(coro, False)
            mock_run.assert_called_once_with(True, coro, False, False)

    def test_delegates_with_debug(self):
        conn = iterm2.connection.Connection()
        with mock.patch.object(conn, 'run') as mock_run:
            coro = mock.MagicMock()
            conn.run_forever(coro, True, debug=True)
            mock_run.assert_called_once_with(True, coro, True, True)


class TestAsyncSendMessage:
    @pytest.mark.asyncio
    async def test_sends_serialized_message(self):
        conn = iterm2.connection.Connection()
        conn.websocket = mock.AsyncMock()
        msg = iterm2.api_pb2.ClientOriginatedMessage()
        msg.id = 1
        await conn.async_send_message(msg)
        conn.websocket.send.assert_called_once()
        sent_data = conn.websocket.send.call_args[0][0]
        verify_msg = iterm2.api_pb2.ClientOriginatedMessage()
        verify_msg.ParseFromString(sent_data)
        assert verify_msg.id == 1


class TestModuleRunUntilComplete:
    def test_creates_connection_and_runs(self):
        with mock.patch.object(iterm2.connection.Connection, '__new__') as mock_new:
            fake_conn = mock.MagicMock()
            fake_conn.run_until_complete.return_value = "result"
            mock_new.return_value = fake_conn
            coro = mock.MagicMock()
            result = iterm2.connection.run_until_complete(coro)
            fake_conn.run_until_complete.assert_called_once_with(coro, False, False)
            assert result == "result"

    def test_exits_on_connection_refused(self):
        with mock.patch.object(iterm2.connection.Connection, '__new__') as mock_new:
            fake_conn = mock.MagicMock()
            fake_conn.run_until_complete.side_effect = ConnectionRefusedError("refused")
            mock_new.return_value = fake_conn
            with mock.patch.object(sys, 'exit') as mock_exit:
                iterm2.connection.run_until_complete(mock.MagicMock())
                mock_exit.assert_called_once_with(1)


class TestModuleRunForever:
    def test_creates_connection_and_runs(self):
        with mock.patch.object(iterm2.connection.Connection, '__new__') as mock_new:
            fake_conn = mock.MagicMock()
            mock_new.return_value = fake_conn
            coro = mock.MagicMock()
            iterm2.connection.run_forever(coro)
            fake_conn.run_forever.assert_called_once_with(coro, False, False)

    def test_exits_on_connection_refused(self):
        with mock.patch.object(iterm2.connection.Connection, '__new__') as mock_new:
            fake_conn = mock.MagicMock()
            fake_conn.run_forever.side_effect = ConnectionRefusedError("refused")
            mock_new.return_value = fake_conn
            with mock.patch.object(sys, 'exit') as mock_exit:
                iterm2.connection.run_forever(mock.MagicMock())
                mock_exit.assert_called_once_with(1)


class TestAddDisconnectCallback:
    def test_adds_callback_to_global_list(self):
        initial_len = len(iterm2.connection.gDisconnectCallbacks)
        cb = mock.MagicMock()
        iterm2.connection.add_disconnect_callback(cb)
        try:
            assert len(iterm2.connection.gDisconnectCallbacks) == initial_len + 1
            assert cb in iterm2.connection.gDisconnectCallbacks
        finally:
            iterm2.connection.gDisconnectCallbacks.remove(cb)

    def test_multiple_callbacks(self):
        initial_len = len(iterm2.connection.gDisconnectCallbacks)
        cb1 = mock.MagicMock()
        cb2 = mock.MagicMock()
        iterm2.connection.add_disconnect_callback(cb1)
        iterm2.connection.add_disconnect_callback(cb2)
        try:
            assert len(iterm2.connection.gDisconnectCallbacks) == initial_len + 2
        finally:
            iterm2.connection.gDisconnectCallbacks.remove(cb1)
            iterm2.connection.gDisconnectCallbacks.remove(cb2)


class TestAsyncCreate:
    @pytest.mark.asyncio
    async def test_creates_connection_authenticates_and_connects(self):
        mock_ws = mock.AsyncMock()

        async def fake_connect_coro(self):
            return mock_ws

        with mock.patch.object(iterm2.connection.Connection, 'authenticate', return_value=True), \
             mock.patch.object(iterm2.connection.Connection, '_get_connect_coro', fake_connect_coro):
            result = await iterm2.connection.Connection.async_create()
            assert result.websocket is mock_ws
            assert result._Connection__dispatch_forever_future is not None
            result._Connection__dispatch_forever_future.cancel()
            try:
                await result._Connection__dispatch_forever_future
            except asyncio.CancelledError:
                pass


class TestRun:
    def test_run_with_forever_false(self):
        conn = iterm2.connection.Connection()
        coro_result = "done"

        async def fake_coro(c):
            return coro_result

        with mock.patch.object(conn, 'async_connect') as mock_async_connect:
            mock_async_connect.return_value = coro_result
            result = conn.run(False, fake_coro, False)
            assert result == coro_result
            mock_async_connect.assert_called_once()

    def test_run_with_forever_true(self):
        conn = iterm2.connection.Connection()

        async def fake_coro(c):
            return "forever"

        with mock.patch.object(conn, 'async_connect') as mock_async_connect:
            mock_async_connect.return_value = "forever"
            result = conn.run(True, fake_coro, False)
            assert result == "forever"

    def test_run_with_debug(self):
        conn = iterm2.connection.Connection()

        async def fake_coro(c):
            return "debug"

        with mock.patch('asyncio.new_event_loop') as mock_new_loop, \
             mock.patch('asyncio.set_event_loop'):
            fake_loop = mock.MagicMock()
            mock_new_loop.return_value = fake_loop
            fake_loop.run_until_complete.return_value = "debug"
            result = conn.run(False, fake_coro, False, debug=True)
            fake_loop.set_debug.assert_called_once_with(True)
            assert result == "debug"

    def test_run_calls_disconnect_callbacks(self):
        conn = iterm2.connection.Connection()
        callback_called = []

        def my_callback():
            callback_called.append(True)

        iterm2.connection.gDisconnectCallbacks.append(my_callback)

        async def fake_coro(c):
            return "ok"

        try:
            with mock.patch.object(conn, 'async_connect') as mock_async_connect:
                mock_async_connect.return_value = "ok"
                conn.run(False, fake_coro, False)
                assert callback_called == [True]
                assert iterm2.connection.gDisconnectCallbacks == []
        finally:
            iterm2.connection.gDisconnectCallbacks.clear()

    def test_run_closes_existing_loop(self):
        conn = iterm2.connection.Connection()
        old_loop = mock.MagicMock()
        conn.loop = old_loop

        async def fake_coro(c):
            return "ok"

        with mock.patch.object(conn, 'async_connect') as mock_async_connect:
            mock_async_connect.return_value = "ok"
            conn.run(False, fake_coro, False)
            old_loop.close.assert_called_once()


class TestAsyncDispatchForever:
    @pytest.mark.asyncio
    async def test_dispatches_to_receiver(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 1
        msg_data = msg.SerializeToString()

        ws = mock.AsyncMock()
        ws.recv = mock.AsyncMock(side_effect=[msg_data, asyncio.CancelledError()])
        conn.websocket = ws

        loop = asyncio.get_event_loop()
        receiver_future = loop.create_future()

        def match_func(m):
            return m.id == 1

        conn._Connection__receivers = [(match_func, receiver_future)]
        conn._Connection__tasks = []

        task = asyncio.ensure_future(conn._async_dispatch_forever(conn, loop))
        result = await receiver_future
        assert result.id == 1
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_dispatches_to_helper_when_no_receiver(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 99
        msg_data = msg.SerializeToString()

        ws = mock.AsyncMock()
        ws.recv = mock.AsyncMock(side_effect=[msg_data, asyncio.CancelledError()])
        conn.websocket = ws

        helper_called = []

        async def test_helper(c, m):
            helper_called.append(m.id)
            return True

        iterm2.connection.Connection.helpers.append(test_helper)

        try:
            loop = asyncio.get_event_loop()
            conn._Connection__receivers = []
            conn._Connection__tasks = []

            task = asyncio.ensure_future(conn._async_dispatch_forever(conn, loop))
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            assert helper_called == [99]
        finally:
            iterm2.connection.Connection.helpers.remove(test_helper)

    @pytest.mark.asyncio
    async def test_handles_cancelled_error(self):
        conn = iterm2.connection.Connection()
        ws = mock.AsyncMock()
        ws.recv = mock.AsyncMock(side_effect=asyncio.CancelledError())
        conn.websocket = ws

        loop = asyncio.get_event_loop()
        conn._Connection__tasks = []
        conn._Connection__receivers = []

        task = asyncio.ensure_future(conn._async_dispatch_forever(conn, loop))
        await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_collects_garbage_each_iteration(self):
        conn = iterm2.connection.Connection()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        msg.id = 1
        msg_data = msg.SerializeToString()

        ws = mock.AsyncMock()
        ws.recv = mock.AsyncMock(side_effect=[msg_data, asyncio.CancelledError()])
        conn.websocket = ws

        gc_called = []
        original_gc = conn._collect_garbage
        def tracked_gc():
            gc_called.append(True)
            original_gc()
        conn._collect_garbage = tracked_gc

        loop = asyncio.get_event_loop()
        receiver_future = loop.create_future()

        def match_func(m):
            return m.id == 1

        conn._Connection__receivers = [(match_func, receiver_future)]
        conn._Connection__tasks = []

        task = asyncio.ensure_future(conn._async_dispatch_forever(conn, loop))
        await receiver_future
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(gc_called) >= 1


class TestRunCancelsTasks:
    def test_run_cancels_helper_tasks(self):
        conn = iterm2.connection.Connection()
        captured_tasks = []

        async def fake_coro(c):
            fake_task = mock.MagicMock()
            c._Connection__tasks = [fake_task]
            captured_tasks.append(fake_task)
            return "done"

        async def fake_async_connect(main_coro, retry=False):
            return await main_coro(conn)

        conn.async_connect = fake_async_connect
        conn.run(False, fake_coro, False)
        # Clean up the loop created by run()
        if conn.loop is not None and not conn.loop.is_closed():
            conn.loop.close()

        assert len(captured_tasks) == 1
        captured_tasks[0].cancel.assert_called_once()


class TestGetUnixConnectCoro:
    def test_returns_unix_connect_coro(self):
        conn = iterm2.connection.Connection()
        with mock.patch('iterm2.connection.websockets_client') as mock_ws_client:
            mock_ws_client.unix_connect.return_value = mock.MagicMock()
            coro = conn._get_unix_connect_coro()
            mock_ws_client.unix_connect.assert_called_once()
            call_kwargs = mock_ws_client.unix_connect.call_args[1]
            assert call_kwargs['ping_interval'] is None
            assert call_kwargs['close_timeout'] == 0
            assert call_kwargs['max_size'] is None
