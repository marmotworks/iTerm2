import asyncio
import unittest.mock as mock
import pytest

import iterm2
import iterm2.lifecycle
import iterm2.notifications
import iterm2.api_pb2


def _make_token():
    return ("key", "coro")


class TestEachSessionOnceMonitorInit:
    def test_init_stores_app_and_connection(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection

        monitor = iterm2.lifecycle.EachSessionOnceMonitor(app)

        assert monitor._EachSessionOnceMonitor__connection is connection
        assert monitor._EachSessionOnceMonitor__app is app
        assert monitor._EachSessionOnceMonitor__token is None

    def test_init_creates_queue(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection

        monitor = iterm2.lifecycle.EachSessionOnceMonitor(app)

        queue = monitor._EachSessionOnceMonitor__queue
        assert isinstance(queue, asyncio.Queue)
        assert queue.empty()


class TestEachSessionOnceMonitorAsyncEnter:
    @pytest.mark.asyncio
    async def test_subscribe_to_new_session_notification(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = []

        token = _make_token()
        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ) as mock_subscribe:
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app) as mon:
                    mock_subscribe.assert_called_once_with(connection, mock.ANY)
                    stored_token = mon._EachSessionOnceMonitor__token
                    assert stored_token is token

    @pytest.mark.asyncio
    async def test_enumerates_existing_sessions(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        session1 = mock.Mock()
        session1.session_id = "session-1"
        session2 = mock.Mock()
        session2.session_id = "session-2"

        tab1 = mock.Mock()
        tab1.all_sessions = [session1]
        tab2 = mock.Mock()
        tab2.all_sessions = [session2]

        window = mock.Mock()
        window.tabs = [tab1, tab2]

        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = [window]

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app) as mon:
                    queue = mon._EachSessionOnceMonitor__queue
                    assert queue.qsize() == 2
                    result1 = await queue.get()
                    result2 = await queue.get()
                    assert result1 is session1
                    assert result2 is session2
                    assert queue.empty()

    @pytest.mark.asyncio
    async def test_empty_windows(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = []

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app) as mon:
                    queue = mon._EachSessionOnceMonitor__queue
                    assert queue.empty()

    @pytest.mark.asyncio
    async def test_empty_tabs(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        window = mock.Mock()
        window.tabs = []

        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = [window]

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app) as mon:
                    queue = mon._EachSessionOnceMonitor__queue
                    assert queue.empty()

    @pytest.mark.asyncio
    async def test_multiple_windows_and_tabs(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        session1 = mock.Mock()
        session1.session_id = "s1"
        session2 = mock.Mock()
        session2.session_id = "s2"
        session3 = mock.Mock()
        session3.session_id = "s3"

        tab1 = mock.Mock()
        tab1.all_sessions = [session1]
        tab2 = mock.Mock()
        tab2.all_sessions = [session2, session3]

        window1 = mock.Mock()
        window1.tabs = [tab1]
        window2 = mock.Mock()
        window2.tabs = [tab2]

        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = [window1, window2]

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app) as mon:
                    queue = mon._EachSessionOnceMonitor__queue
                    assert queue.qsize() == 3


class TestEachSessionOnceMonitorAsyncExit:
    @pytest.mark.asyncio
    async def test_unsubscribes_on_exit(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = []

        token = _make_token()
        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
            ) as mock_unsub:
                async with iterm2.lifecycle.EachSessionOnceMonitor(app):
                    pass

                mock_unsub.assert_called_once_with(connection, token)

    @pytest.mark.asyncio
    async def test_swallows_subscription_exception(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = []

        token = _make_token()
        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=iterm2.notifications.SubscriptionException("gone"),
            ):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app):
                    pass

    @pytest.mark.asyncio
    async def test_propagates_other_exceptions(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = []

        token = _make_token()
        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=RuntimeError("boom"),
            ):
                with pytest.raises(RuntimeError, match="boom"):
                    async with iterm2.lifecycle.EachSessionOnceMonitor(app):
                        pass


class TestEachSessionOnceMonitorAsyncGet:
    @pytest.mark.asyncio
    async def test_returns_session_id(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        app = mock.Mock()
        app.connection = connection
        app.terminal_windows = []

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.EachSessionOnceMonitor(app) as mon:
                    notif = iterm2.api_pb2.NewSessionNotification()
                    notif.session_id = "test-session-42"
                    queue = mon._EachSessionOnceMonitor__queue
                    await queue.put(notif)

                    result = await mon.async_get()
                    assert result == "test-session-42"


class TestSessionTerminationMonitorInit:
    def test_init_stores_connection(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.lifecycle.SessionTerminationMonitor(connection)

        assert monitor._SessionTerminationMonitor__connection is connection
        assert monitor._SessionTerminationMonitor__token is None

    def test_init_creates_queue(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.lifecycle.SessionTerminationMonitor(connection)

        queue = monitor._SessionTerminationMonitor__queue
        assert isinstance(queue, asyncio.Queue)
        assert queue.empty()


class TestSessionTerminationMonitorAsyncEnter:
    @pytest.mark.asyncio
    async def test_subscribes_to_termination_notification(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_terminate_session_notification',
            return_value=token,
        ) as mock_subscribe:
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.SessionTerminationMonitor(connection) as mon:
                    mock_subscribe.assert_called_once_with(connection, mock.ANY)
                    stored_token = mon._SessionTerminationMonitor__token
                    assert stored_token is token


class TestSessionTerminationMonitorAsyncExit:
    @pytest.mark.asyncio
    async def test_unsubscribes_on_exit(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_terminate_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
            ) as mock_unsub:
                async with iterm2.lifecycle.SessionTerminationMonitor(connection):
                    pass

                mock_unsub.assert_called_once_with(connection, token)

    @pytest.mark.asyncio
    async def test_swallows_subscription_exception(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_terminate_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=iterm2.notifications.SubscriptionException("gone"),
            ):
                async with iterm2.lifecycle.SessionTerminationMonitor(connection):
                    pass


class TestSessionTerminationMonitorAsyncGet:
    @pytest.mark.asyncio
    async def test_returns_session_id(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_terminate_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.SessionTerminationMonitor(connection) as mon:
                    notif = iterm2.api_pb2.TerminateSessionNotification()
                    notif.session_id = "terminated-session"
                    queue = mon._SessionTerminationMonitor__queue
                    await queue.put(notif.session_id)

                    result = await mon.async_get()
                    assert result == "terminated-session"


class TestLayoutChangeMonitorInit:
    def test_init_stores_connection(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.lifecycle.LayoutChangeMonitor(connection)

        assert monitor._LayoutChangeMonitor__connection is connection
        assert monitor._LayoutChangeMonitor__token is None

    def test_init_creates_queue(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.lifecycle.LayoutChangeMonitor(connection)

        queue = monitor._LayoutChangeMonitor__queue
        assert isinstance(queue, asyncio.Queue)


class TestLayoutChangeMonitorAsyncEnter:
    @pytest.mark.asyncio
    async def test_subscribes_to_layout_change(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_layout_change_notification',
            return_value=token,
        ) as mock_subscribe:
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.LayoutChangeMonitor(connection) as mon:
                    mock_subscribe.assert_called_once_with(connection, mock.ANY)
                    assert mon._LayoutChangeMonitor__token is token


class TestLayoutChangeMonitorAsyncExit:
    @pytest.mark.asyncio
    async def test_unsubscribes_on_exit(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_layout_change_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
            ) as mock_unsub:
                async with iterm2.lifecycle.LayoutChangeMonitor(connection):
                    pass

                mock_unsub.assert_called_once_with(connection, token)

    @pytest.mark.asyncio
    async def test_swallows_subscription_exception(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_layout_change_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=iterm2.notifications.SubscriptionException("gone"),
            ):
                async with iterm2.lifecycle.LayoutChangeMonitor(connection):
                    pass


class TestLayoutChangeMonitorAsyncGet:
    @pytest.mark.asyncio
    async def test_returns_none_on_layout_change(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_layout_change_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.LayoutChangeMonitor(connection) as mon:
                    notif = iterm2.api_pb2.LayoutChangedNotification()
                    queue = mon._LayoutChangeMonitor__queue
                    await queue.put(notif)

                    result = await mon.async_get()
                    assert result is None


class TestNewSessionMonitorInit:
    def test_init_stores_connection(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.lifecycle.NewSessionMonitor(connection)

        assert monitor._NewSessionMonitor__connection is connection
        assert monitor._NewSessionMonitor__token is None

    def test_init_creates_queue(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        monitor = iterm2.lifecycle.NewSessionMonitor(connection)

        queue = monitor._NewSessionMonitor__queue
        assert isinstance(queue, asyncio.Queue)


class TestNewSessionMonitorAsyncEnter:
    @pytest.mark.asyncio
    async def test_subscribes_to_new_session(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ) as mock_subscribe:
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.NewSessionMonitor(connection) as mon:
                    mock_subscribe.assert_called_once_with(connection, mock.ANY)
                    assert mon._NewSessionMonitor__token is token


class TestNewSessionMonitorAsyncExit:
    @pytest.mark.asyncio
    async def test_unsubscribes_on_exit(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
            ) as mock_unsub:
                async with iterm2.lifecycle.NewSessionMonitor(connection):
                    pass

                mock_unsub.assert_called_once_with(connection, token)

    @pytest.mark.asyncio
    async def test_swallows_subscription_exception(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)
        token = _make_token()

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=token,
        ):
            with mock.patch.object(
                iterm2.notifications,
                'async_unsubscribe',
                side_effect=iterm2.notifications.SubscriptionException("gone"),
            ):
                async with iterm2.lifecycle.NewSessionMonitor(connection):
                    pass


class TestNewSessionMonitorAsyncGet:
    @pytest.mark.asyncio
    async def test_returns_session_id(self):
        connection = mock.Mock(spec=iterm2.connection.Connection)

        with mock.patch.object(
            iterm2.notifications,
            'async_subscribe_to_new_session_notification',
            return_value=_make_token(),
        ):
            with mock.patch.object(iterm2.notifications, 'async_unsubscribe'):
                async with iterm2.lifecycle.NewSessionMonitor(connection) as mon:
                    notif = iterm2.api_pb2.NewSessionNotification()
                    notif.session_id = "brand-new-session"
                    queue = mon._NewSessionMonitor__queue
                    await queue.put(notif)

                    result = await mon.async_get()
                    assert result == "brand-new-session"
