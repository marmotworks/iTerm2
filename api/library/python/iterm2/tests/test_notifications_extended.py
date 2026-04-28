import pytest
from unittest.mock import Mock, AsyncMock, patch
import iterm2
import iterm2.api_pb2
import iterm2.notifications
import iterm2.rpc
import iterm2.connection
import iterm2.keyboard


def _make_response(status_str):
    """Build a ServerOriginatedMessage with a NotificationResponse of given status."""
    msg = iterm2.api_pb2.ServerOriginatedMessage()
    msg.notification_response.status = (
        iterm2.api_pb2.NotificationResponse.Status.Value(status_str))
    return msg


def _clean_handlers():
    iterm2.notifications._get_handlers().clear()


@pytest.fixture(autouse=True)
def cleanup():
    yield
    _clean_handlers()
    if hasattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper'):
        delattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper')


# -- async_unsubscribe -------------------------------------------------------

class TestAsyncUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribe_session_key_len2(self):
        """Unsubscribe with a (session, notification_type) key (len==2)."""
        conn = Mock()
        async def cb(c, n):
            pass
        ok_resp = _make_response("OK")
        with patch.object(iterm2.rpc, 'async_notification_request', new=AsyncMock(return_value=ok_resp)):
            token = await iterm2.notifications.async_subscribe_to_new_session_notification(conn, cb)
        assert token is not None
        key, _ = token
        # Ensure we're the only handler so RPC unsubscribe is triggered
        if key in iterm2.notifications._get_handlers():
            iterm2.notifications._get_handlers()[key] = [cb]
        unsub_mock = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', unsub_mock):
            await iterm2.notifications.async_unsubscribe(conn, token)
        unsub_mock.assert_called_once()
        call_args = unsub_mock.call_args
        assert call_args[0][1] is False

    @pytest.mark.asyncio
    async def test_unsubscribe_variable_monitor_key_len4(self):
        """Unsubscribe with a variable monitor key (len==4, NOTIFY_ON_VARIABLE_CHANGE)."""
        conn = Mock()
        async def cb(c, n):
            pass
        ok_resp = _make_response("OK")
        with patch.object(iterm2.rpc, 'async_notification_request', new=AsyncMock(return_value=ok_resp)):
            token = await iterm2.notifications.async_subscribe_to_variable_change_notification(
                conn, cb,
                iterm2.api_pb2.VariableScope.Value("SESSION"),
                "myVar",
                "sess123")
        assert len(token[0]) == 4
        unsub_mock = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', unsub_mock):
            await iterm2.notifications.async_unsubscribe(conn, token)
        unsub_mock.assert_called_once()
        assert unsub_mock.call_args[0][1] is False

    @pytest.mark.asyncio
    async def test_unsubscribe_custom_key_asserts_false(self):
        """Unsubscribe with a custom key that isn't len==2 or variable_change should assert."""
        conn = Mock()
        async def cb(c, n):
            pass
        custom_key = ("a", "b", "c")
        iterm2.notifications._get_handlers()[custom_key] = [cb]
        with pytest.raises(AssertionError):
            await iterm2.notifications.async_unsubscribe(conn, (custom_key, cb))


# -- async_subscribe_to_new_session_notification -----------------------------

class TestAsyncSubscribeToNewSessionNotification:
    @pytest.mark.asyncio
    async def test_subscribe_new_session(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_new_session_notification(conn, cb)
        mock_rpc.assert_called_once()
        args = mock_rpc.call_args
        assert args[0][1] is True
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_NEW_SESSION
        assert token is not None


# -- async_subscribe_to_keystroke_notification --------------------------------

class TestAsyncSubscribeToKeystrokeNotification:
    @pytest.mark.asyncio
    async def test_with_session_advanced_false(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_keystroke_notification(
                conn, cb, session="sess1", advanced=False)
        mock_rpc.assert_called_once()
        args = mock_rpc.call_args
        assert args[0][1] is True
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_KEYSTROKE
        assert args[0][3] == "sess1"
        kmr = args[0][5]
        assert kmr.advanced is False

    @pytest.mark.asyncio
    async def test_without_session_advanced_true(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_keystroke_notification(
                conn, cb, session=None, advanced=True)
        args = mock_rpc.call_args
        assert args[0][3] == "all"
        kmr = args[0][5]
        assert kmr.advanced is True


# -- async_filter_keystrokes --------------------------------------------------

class TestAsyncFilterKeystrokes:
    @pytest.mark.asyncio
    async def test_with_patterns(self):
        conn = Mock()
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.characters = ["a"]
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_filter_keystrokes(
                conn, [pattern], session="sess1")
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.KEYSTROKE_FILTER
        kfr = args[0][9]
        assert len(kfr.patterns_to_ignore) == 1

    @pytest.mark.asyncio
    async def test_without_session(self):
        conn = Mock()
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.characters = ["b"]
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_filter_keystrokes(
                conn, [pattern], session=None)
        args = mock_rpc.call_args
        assert args[0][3] == "all"


# -- async_subscribe_to_screen_update_notification ----------------------------

class TestAsyncSubscribeToScreenUpdateNotification:
    @pytest.mark.asyncio
    async def test_with_session(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_screen_update_notification(
                conn, cb, session="sess1")
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_SCREEN_UPDATE
        assert args[0][3] == "sess1"

    @pytest.mark.asyncio
    async def test_without_session(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_screen_update_notification(
                conn, cb, session=None)
        args = mock_rpc.call_args
        assert args[0][3] == "all"


# -- async_subscribe_to_prompt_notification -----------------------------------

class TestAsyncSubscribeToPromptNotification:
    @pytest.mark.asyncio
    async def test_with_modes(self):
        conn = Mock()
        async def cb(c, n):
            pass
        modes = [iterm2.api_pb2.PromptMonitorMode.Value("PROMPT")]
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_prompt_notification(
                conn, cb, session="sess1", modes=modes)
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_PROMPT
        assert args[0][3] == "sess1"
        assert args[0][8] is not None

    @pytest.mark.asyncio
    async def test_with_multiple_modes(self):
        conn = Mock()
        async def cb(c, n):
            pass
        modes = [
            iterm2.api_pb2.PromptMonitorMode.Value("PROMPT"),
            iterm2.api_pb2.PromptMonitorMode.Value("COMMAND_START"),
        ]
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_prompt_notification(
                conn, cb, session="sess1", modes=modes)
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_PROMPT


# -- async_subscribe_to_custom_escape_sequence_notification -------------------

class TestAsyncSubscribeToCustomEscapeSequenceNotification:
    @pytest.mark.asyncio
    async def test_with_session(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_custom_escape_sequence_notification(
                conn, cb, session="sess1")
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_CUSTOM_ESCAPE_SEQUENCE
        assert args[0][3] == "sess1"

    @pytest.mark.asyncio
    async def test_without_session(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_custom_escape_sequence_notification(
                conn, cb, session=None)
        args = mock_rpc.call_args
        assert args[0][3] == "all"


# -- async_subscribe_to_terminate_session_notification ------------------------

class TestAsyncSubscribeToTerminateSessionNotification:
    @pytest.mark.asyncio
    async def test_subscribe(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_terminate_session_notification(
                conn, cb)
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_TERMINATE_SESSION
        assert args[0][3] == "all"


# -- async_subscribe_to_layout_change_notification ----------------------------

class TestAsyncSubscribeToLayoutChangeNotification:
    @pytest.mark.asyncio
    async def test_subscribe(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_layout_change_notification(
                conn, cb)
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_LAYOUT_CHANGE
        assert args[0][3] == "all"


# -- async_subscribe_to_focus_change_notification -----------------------------

class TestAsyncSubscribeToFocusChangeNotification:
    @pytest.mark.asyncio
    async def test_subscribe(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_focus_change_notification(
                conn, cb)
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_FOCUS_CHANGE
        assert args[0][3] == "all"


# -- async_subscribe_to_broadcast_domains_change_notification -----------------

class TestAsyncSubscribeToBroadcastDomainsChangeNotification:
    @pytest.mark.asyncio
    async def test_subscribe(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_broadcast_domains_change_notification(
                conn, cb)
        args = mock_rpc.call_args
        assert args[0][2] == iterm2.api_pb2.NOTIFY_ON_BROADCAST_CHANGE
        assert args[0][3] == "all"


# -- async_subscribe_to_server_originated_rpc_notification --------------------

class TestAsyncSubscribeToServerOriginatedRPCNotification:
    @pytest.mark.asyncio
    async def test_basic_no_timeout(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func", timeout_seconds=None)
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        assert rpc_req.name == "my_func"
        assert not rpc_req.HasField("timeout")

    @pytest.mark.asyncio
    async def test_with_timeout(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func", timeout_seconds=10)
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        assert rpc_req.timeout == 10

    @pytest.mark.asyncio
    async def test_with_arguments(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func", arguments=["a", "b"])
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        assert len(rpc_req.arguments) == 2
        assert rpc_req.arguments[0].name == "a"
        assert rpc_req.arguments[1].name == "b"

    @pytest.mark.asyncio
    async def test_with_defaults(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func", arguments=["a", "b"], defaults={"a": "some.path"})
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        assert len(rpc_req.defaults) == 1
        assert rpc_req.defaults[0].name == "a"
        assert rpc_req.defaults[0].path == "some.path"

    @pytest.mark.asyncio
    async def test_defaults_not_in_arguments_raises(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            with pytest.raises(AssertionError):
                await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                    conn, cb, "my_func", arguments=["a"], defaults={"b": "some.path"})

    @pytest.mark.asyncio
    async def test_with_session_title(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func",
                role=iterm2.notifications.RPC_ROLE_SESSION_TITLE,
                session_title_display_name="My Title",
                session_title_unique_id="unique-id-1")
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        assert rpc_req.session_title_attributes.display_name == "My Title"
        assert rpc_req.session_title_attributes.unique_identifier == "unique-id-1"

    @pytest.mark.asyncio
    async def test_session_title_without_unique_id_raises(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            with pytest.raises(AssertionError):
                await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                    conn, cb, "my_func",
                    role=iterm2.notifications.RPC_ROLE_SESSION_TITLE,
                    session_title_display_name="My Title",
                    session_title_unique_id=None)

    @pytest.mark.asyncio
    async def test_with_status_bar_component(self):
        conn = Mock()
        async def cb(c, n):
            pass
        sbc_mock = Mock()
        sbc_mock.set_fields_in_proto = Mock()
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func",
                role=iterm2.notifications.RPC_ROLE_STATUS_BAR_COMPONENT,
                status_bar_component=sbc_mock)
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        sbc_mock.set_fields_in_proto.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_context_menu(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                conn, cb, "my_func",
                role=iterm2.notifications.RPC_ROLE_CONTEXT_MENU,
                context_menu_display_name="My Menu",
                context_menu_unique_id="menu-id-1")
        args = mock_rpc.call_args
        rpc_req = args[0][4]
        assert rpc_req.context_menu_attributes.display_name == "My Menu"
        assert rpc_req.context_menu_attributes.unique_identifier == "menu-id-1"

    @pytest.mark.asyncio
    async def test_context_menu_without_unique_id_raises(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            with pytest.raises(AssertionError):
                await iterm2.notifications.async_subscribe_to_server_originated_rpc_notification(
                    conn, cb, "my_func",
                    role=iterm2.notifications.RPC_ROLE_CONTEXT_MENU,
                    context_menu_display_name="My Menu",
                    context_menu_unique_id=None)


# -- async_subscribe_to_variable_change_notification --------------------------

class TestAsyncSubscribeToVariableChangeNotification:
    @pytest.mark.asyncio
    async def test_with_identifier_none(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_variable_change_notification(
                conn, cb,
                iterm2.api_pb2.VariableScope.Value("APP"),
                "myVar",
                None)
        args = mock_rpc.call_args
        vmr = args[0][6]
        assert vmr.name == "myVar"
        assert vmr.identifier == ""

    @pytest.mark.asyncio
    async def test_with_identifier(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications.async_subscribe_to_variable_change_notification(
                conn, cb,
                iterm2.api_pb2.VariableScope.Value("SESSION"),
                "myVar",
                "sess123")
        args = mock_rpc.call_args
        vmr = args[0][6]
        assert vmr.identifier == "sess123"
        assert len(token[0]) == 4


# -- async_subscribe_to_profile_change_notification ---------------------------

class TestAsyncSubscribeToProfileChangeNotification:
    @pytest.mark.asyncio
    async def test_raises_attribute_error_bug(self):
        """The function references iterm2.api_PB2 (uppercase) which doesn't exist."""
        conn = Mock()
        async def cb(c, n):
            pass
        with pytest.raises(AttributeError):
            await iterm2.notifications.async_subscribe_to_profile_change_notification(
                conn, cb, "guid-123")


# -- _async_subscribe ---------------------------------------------------------

class TestAsyncSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_ok_returns_token(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications._async_subscribe(
                conn, True, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, cb)
        assert token is not None
        key, handler = token
        assert key == (None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        assert handler is cb

    @pytest.mark.asyncio
    async def test_subscribe_already_subscribed_returns_token(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("ALREADY_SUBSCRIBED"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications._async_subscribe(
                conn, True, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, cb)
        assert token is not None

    @pytest.mark.asyncio
    async def test_subscribe_error_raises(self):
        conn = Mock()
        async def cb(c, n):
            pass
        err_resp = _make_response("SESSION_NOT_FOUND")
        mock_rpc = AsyncMock(return_value=err_resp)
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            with pytest.raises(iterm2.notifications.SubscriptionException):
                await iterm2.notifications._async_subscribe(
                    conn, True, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, cb)

    @pytest.mark.asyncio
    async def test_unsubscribe_ok(self):
        conn = Mock()
        async def cb(c, n):
            pass
        iterm2.notifications._register_notification_handler_impl(
            (None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION), cb)
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            await iterm2.notifications._async_subscribe(
                conn, False, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, cb)
        handlers = iterm2.notifications._get_handlers()
        key = (None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        assert cb not in handlers.get(key, [])

    @pytest.mark.asyncio
    async def test_subscribe_with_custom_key(self):
        conn = Mock()
        async def cb(c, n):
            pass
        custom_key = ("scope", "id", "name", iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE)
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications._async_subscribe(
                conn, True, iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE, cb,
                key=custom_key)
        assert token[0] == custom_key

    @pytest.mark.asyncio
    async def test_subscribe_error_with_key_unregisters(self):
        conn = Mock()
        async def cb(c, n):
            pass
        custom_key = ("scope", "id", "name", iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE)
        err_resp = _make_response("SESSION_NOT_FOUND")
        mock_rpc = AsyncMock(return_value=err_resp)
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            with pytest.raises(iterm2.notifications.SubscriptionException):
                await iterm2.notifications._async_subscribe(
                    conn, True, iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE, cb,
                    key=custom_key)
        handlers = iterm2.notifications._get_handlers()
        assert custom_key not in handlers or len(handlers.get(custom_key, [])) == 0

    @pytest.mark.asyncio
    async def test_subscribe_with_session(self):
        conn = Mock()
        async def cb(c, n):
            pass
        mock_rpc = AsyncMock(return_value=_make_response("OK"))
        with patch.object(iterm2.rpc, 'async_notification_request', mock_rpc):
            token = await iterm2.notifications._async_subscribe(
                conn, True, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE, cb,
                session="sess1")
        key, handler = token
        assert key[0] == "sess1"
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_KEYSTROKE


# -- _async_dispatch_helper ---------------------------------------------------

class TestAsyncDispatchHelper:
    @pytest.mark.asyncio
    async def test_dispatch_with_handlers(self):
        conn = Mock()
        called = []

        async def handler1(c, n):
            called.append(1)

        async def handler2(c, n):
            called.append(2)

        key = (None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        iterm2.notifications._register_notification_handler_impl(key, handler1)
        iterm2.notifications._register_notification_handler_impl(key, handler2)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ns = msg.notification.new_session_notification
        ns.session_id = "new1"

        result = await iterm2.notifications._async_dispatch_helper(conn, msg)
        assert result is True
        assert called == [1, 2]

    @pytest.mark.asyncio
    async def test_dispatch_without_handlers(self):
        conn = Mock()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ns = msg.notification.new_session_notification
        ns.session_id = "new1"

        result = await iterm2.notifications._async_dispatch_helper(conn, msg)
        assert result is False

    @pytest.mark.asyncio
    async def test_dispatch_unregistered_rpc(self):
        conn = Mock()
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        sorpc = msg.notification.server_originated_rpc_notification
        sorpc.request_id = "42"
        rpc_sig = sorpc.rpc
        rpc_sig.name = "unknown_func"

        send_mock = AsyncMock()
        with patch.object(iterm2.rpc, 'async_send_rpc_result', send_mock):
            result = await iterm2.notifications._async_dispatch_helper(conn, msg)

        assert result is False
        send_mock.assert_called_once()
        call_args = send_mock.call_args
        assert call_args[0][1] == "42"
        assert call_args[0][2] is True
        exc = call_args[0][3]
        assert "No such function" in exc["reason"]


# -- _get_all_sessions_handler_keys_from_notification -------------------------

class TestGetAllSessionsHandlerKeysFromNotification:
    def test_variable_changed_notification(self):
        notif = iterm2.api_pb2.Notification()
        vc = notif.variable_changed_notification
        vc.name = "myVar"
        keys = iterm2.notifications._get_all_sessions_handler_keys_from_notification(notif)
        assert len(keys) == 2
        assert iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE in keys[0]
        assert iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE in keys[1]
        assert keys[0][1] == "all"
        assert keys[1][1] == "all"

    def test_standard_notification(self):
        notif = iterm2.api_pb2.Notification()
        ns = notif.new_session_notification
        ns.session_id = "new1"
        keys = iterm2.notifications._get_all_sessions_handler_keys_from_notification(notif)
        assert len(keys) == 1
        assert keys[0] == (None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)

    def test_keystroke_notification_all_sessions_key(self):
        notif = iterm2.api_pb2.Notification()
        ks = notif.keystroke_notification
        ks.session = "sess1"
        keys = iterm2.notifications._get_all_sessions_handler_keys_from_notification(notif)
        assert len(keys) == 1
        assert keys[0] == (None, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE)


# -- _get_notification_handlers ----------------------------------------------

class TestGetNotificationHandlers:
    def test_exact_key_match(self):
        async def handler(c, n):
            pass
        key = ("sess1", iterm2.api_pb2.NOTIFY_ON_KEYSTROKE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ks = msg.notification.keystroke_notification
        ks.session = "sess1"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers
        assert sub is ks

    def test_all_objects_key_match(self):
        async def handler(c, n):
            pass
        all_key = (None, iterm2.api_pb2.NOTIFY_ON_KEYSTROKE)
        iterm2.notifications._register_notification_handler_impl(all_key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ks = msg.notification.keystroke_notification
        ks.session = "sess999"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_no_match_returns_empty(self):
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ks = msg.notification.keystroke_notification
        ks.session = "sess_no_match"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handlers == []
        assert sub is None

    def test_none_key_returns_empty(self):
        msg = iterm2.api_pb2.ServerOriginatedMessage()

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handlers == []
        assert sub is None

    def test_variable_changed_all_sessions_match(self):
        async def handler(c, n):
            pass
        scope = iterm2.api_pb2.VariableScope.Value("SESSION")
        all_key = (scope, "all", "myVar", iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE)
        iterm2.notifications._register_notification_handler_impl(all_key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        vc = msg.notification.variable_changed_notification
        vc.scope = scope
        vc.identifier = "sessSpecific"
        vc.name = "myVar"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers
        assert sub is vc

    def test_location_change_notification_key(self):
        async def handler(c, n):
            pass
        key = ("sess1", iterm2.api_pb2.NOTIFY_ON_LOCATION_CHANGE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        lc = msg.notification.location_change_notification
        lc.session = "sess1"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_prompt_notification_handlers(self):
        async def handler(c, n):
            pass
        key = ("sess1", iterm2.api_pb2.NOTIFY_ON_PROMPT)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        pn = msg.notification.prompt_notification
        pn.session = "sess1"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_custom_escape_sequence_handlers(self):
        async def handler(c, n):
            pass
        key = ("sess1", iterm2.api_pb2.NOTIFY_ON_CUSTOM_ESCAPE_SEQUENCE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ces = msg.notification.custom_escape_sequence_notification
        ces.session = "sess1"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_screen_update_handlers(self):
        async def handler(c, n):
            pass
        key = ("sess1", iterm2.api_pb2.NOTIFY_ON_SCREEN_UPDATE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        su = msg.notification.screen_update_notification
        su.session = "sess1"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_server_originated_rpc_handlers(self):
        async def handler(c, n):
            pass
        key = (None, iterm2.api_pb2.NOTIFY_ON_SERVER_ORIGINATED_RPC, "my_func()")
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        sorpc = msg.notification.server_originated_rpc_notification
        sorpc.rpc.name = "my_func"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_broadcast_domains_handlers(self):
        async def handler(c, n):
            pass
        key = (None, iterm2.api_pb2.NOTIFY_ON_BROADCAST_CHANGE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        bd = msg.notification.broadcast_domains_changed
        bd.SetInParent()

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_terminate_session_handlers(self):
        async def handler(c, n):
            pass
        key = (None, iterm2.api_pb2.NOTIFY_ON_TERMINATE_SESSION)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        ts = msg.notification.terminate_session_notification
        ts.session_id = "term1"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_layout_changed_handlers(self):
        async def handler(c, n):
            pass
        key = (None, iterm2.api_pb2.NOTIFY_ON_LAYOUT_CHANGE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        lc = msg.notification.layout_changed_notification
        lc.SetInParent()

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_focus_changed_handlers(self):
        async def handler(c, n):
            pass
        key = (None, iterm2.api_pb2.NOTIFY_ON_FOCUS_CHANGE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        fc = msg.notification.focus_changed_notification
        fc.SetInParent()

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers

    def test_profile_changed_handlers(self):
        async def handler(c, n):
            pass
        key = ("guid-123", iterm2.api_pb2.NOTIFY_ON_PROFILE_CHANGE)
        iterm2.notifications._register_notification_handler_impl(key, handler)

        msg = iterm2.api_pb2.ServerOriginatedMessage()
        pc = msg.notification.profile_changed_notification
        pc.guid = "guid-123"

        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers
