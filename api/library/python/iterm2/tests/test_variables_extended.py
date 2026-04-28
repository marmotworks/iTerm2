import asyncio
import json
import unittest.mock as mock
import pytest

import iterm2
import iterm2.variables
import iterm2.notifications
import iterm2.api_pb2


class TestVariableScopes:
    def test_session_value_is_int(self):
        assert isinstance(iterm2.variables.VariableScopes.SESSION.value, int)

    def test_tab_value_is_int(self):
        assert isinstance(iterm2.variables.VariableScopes.TAB.value, int)

    def test_window_value_is_int(self):
        assert isinstance(iterm2.variables.VariableScopes.WINDOW.value, int)

    def test_app_value_is_int(self):
        assert isinstance(iterm2.variables.VariableScopes.APP.value, int)

    def test_all_values_unique(self):
        values = {s.value for s in iterm2.variables.VariableScopes}
        assert len(values) == 4

    def test_iteration_order(self):
        scopes = list(iterm2.variables.VariableScopes)
        assert scopes[0].name == "SESSION"
        assert scopes[1].name == "TAB"
        assert scopes[2].name == "WINDOW"
        assert scopes[3].name == "APP"


class TestVariableMonitorInit:
    def test_init_with_session_scope(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.variables.VariableMonitor(
            connection,
            iterm2.variables.VariableScopes.SESSION,
            "myVar",
            "session-id-1",
        )

        assert monitor._VariableMonitor__connection is connection
        assert monitor._VariableMonitor__scope is iterm2.variables.VariableScopes.SESSION
        assert monitor._VariableMonitor__name == "myVar"
        assert monitor._VariableMonitor__identifier == "session-id-1"
        assert monitor._VariableMonitor__token is None

    def test_init_with_app_scope_and_none_identifier(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.variables.VariableMonitor(
            connection,
            iterm2.variables.VariableScopes.APP,
            "globalVar",
            None,
        )

        assert monitor._VariableMonitor__scope is iterm2.variables.VariableScopes.APP
        assert monitor._VariableMonitor__name == "globalVar"
        assert monitor._VariableMonitor__identifier is None

    def test_init_with_tab_scope(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.variables.VariableMonitor(
            connection,
            iterm2.variables.VariableScopes.TAB,
            "tabVar",
            "tab-id-1",
        )

        assert monitor._VariableMonitor__scope is iterm2.variables.VariableScopes.TAB
        assert monitor._VariableMonitor__name == "tabVar"
        assert monitor._VariableMonitor__identifier == "tab-id-1"

    def test_init_with_window_scope(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.variables.VariableMonitor(
            connection,
            iterm2.variables.VariableScopes.WINDOW,
            "windowVar",
            "window-id-1",
        )

        assert monitor._VariableMonitor__scope is iterm2.variables.VariableScopes.WINDOW
        assert monitor._VariableMonitor__name == "windowVar"
        assert monitor._VariableMonitor__identifier == "window-id-1"

    def test_init_creates_queue(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.variables.VariableMonitor(
            connection,
            iterm2.variables.VariableScopes.SESSION,
            "myVar",
            "session-id-1",
        )

        queue = monitor._VariableMonitor__queue
        assert isinstance(queue, asyncio.Queue)
        assert queue.empty()


class TestVariableMonitorAsyncEnter:
    @pytest.mark.asyncio
    async def test_subscribes_with_correct_params(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ) as mock_subscribe:
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    mock_subscribe.assert_called_once_with(
                        connection,
                        mock.ANY,
                        iterm2.variables.VariableScopes.SESSION.value,
                        "myVar",
                        "session-id-1",
                    )
                    assert mon._VariableMonitor__token is token

    @pytest.mark.asyncio
    async def test_subscribes_with_none_identifier(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ) as mock_subscribe:
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.APP,
                    "globalVar",
                    None,
                ):
                    call_args = mock_subscribe.call_args
                    assert call_args[0][0] is connection
                    assert call_args[0][2] == iterm2.variables.VariableScopes.APP.value
                    assert call_args[0][3] == "globalVar"
                    assert call_args[0][4] is None


class TestVariableMonitorAsyncExit:
    @pytest.mark.asyncio
    async def test_unsubscribes_on_exit(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
            ) as mock_unsub:
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ):
                    pass

                mock_unsub.assert_called_once_with(connection, token)

    @pytest.mark.asyncio
    async def test_swallows_subscription_exception(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=iterm2.notifications.SubscriptionException("gone"),
            ):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ):
                    pass

    @pytest.mark.asyncio
    async def test_propagates_other_exceptions(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=RuntimeError("unexpected"),
            ):
                with pytest.raises(RuntimeError, match="unexpected"):
                    async with iterm2.variables.VariableMonitor(
                        connection,
                        iterm2.variables.VariableScopes.SESSION,
                        "myVar",
                        "session-id-1",
                    ):
                        pass


class TestVariableMonitorAsyncGet:
    @pytest.mark.asyncio
    async def test_returns_string_value(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    msg = mock.Mock()
                    msg.json_new_value = json.dumps("hello")
                    queue = mon._VariableMonitor__queue
                    await queue.put(msg)

                    result = await mon.async_get()
                    assert result == "hello"

    @pytest.mark.asyncio
    async def test_returns_number_value(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    msg = mock.Mock()
                    msg.json_new_value = json.dumps(42)
                    queue = mon._VariableMonitor__queue
                    await queue.put(msg)

                    result = await mon.async_get()
                    assert result == 42

    @pytest.mark.asyncio
    async def test_returns_dict_value(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    msg = mock.Mock()
                    msg.json_new_value = json.dumps({"key": "value", "num": 3})
                    queue = mon._VariableMonitor__queue
                    await queue.put(msg)

                    result = await mon.async_get()
                    assert result == {"key": "value", "num": 3}

    @pytest.mark.asyncio
    async def test_returns_list_value(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    msg = mock.Mock()
                    msg.json_new_value = json.dumps([1, 2, 3])
                    queue = mon._VariableMonitor__queue
                    await queue.put(msg)

                    result = await mon.async_get()
                    assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_returns_none_value(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    msg = mock.Mock()
                    msg.json_new_value = json.dumps(None)
                    queue = mon._VariableMonitor__queue
                    await queue.put(msg)

                    result = await mon.async_get()
                    assert result is None

    @pytest.mark.asyncio
    async def test_returns_bool_value(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = ("key", "coro")

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_variable_change_notification',
            return_value=token,
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.variables.VariableMonitor(
                    connection,
                    iterm2.variables.VariableScopes.SESSION,
                    "myVar",
                    "session-id-1",
                ) as mon:
                    msg = mock.Mock()
                    msg.json_new_value = json.dumps(True)
                    queue = mon._VariableMonitor__queue
                    await queue.put(msg)

                    result = await mon.async_get()
                    assert result is True
