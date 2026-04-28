import pytest
import iterm2.notifications
import iterm2


class TestSubscriptionException:
    def test_exception_message(self):
        exc = iterm2.notifications.SubscriptionException("sub failed")
        assert str(exc) == "sub failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.notifications.SubscriptionException, Exception)


class TestRPCRoleConstants:
    def test_generic(self):
        assert isinstance(iterm2.notifications.RPC_ROLE_GENERIC, int)

    def test_session_title(self):
        assert isinstance(iterm2.notifications.RPC_ROLE_SESSION_TITLE, int)

    def test_status_bar_component(self):
        assert isinstance(iterm2.notifications.RPC_ROLE_STATUS_BAR_COMPONENT, int)

    def test_context_menu(self):
        assert isinstance(iterm2.notifications.RPC_ROLE_CONTEXT_MENU, int)

    def test_roles_are_different(self):
        roles = {
            iterm2.notifications.RPC_ROLE_GENERIC,
            iterm2.notifications.RPC_ROLE_SESSION_TITLE,
            iterm2.notifications.RPC_ROLE_STATUS_BAR_COMPONENT,
            iterm2.notifications.RPC_ROLE_CONTEXT_MENU,
        }
        assert len(roles) == 4


class TestGetHandlers:
    def test_returns_dict(self):
        handlers = iterm2.notifications._get_handlers()
        assert isinstance(handlers, dict)

    def test_returns_same_dict(self):
        h1 = iterm2.notifications._get_handlers()
        h2 = iterm2.notifications._get_handlers()
        assert h1 is h2


class TestStringRPCRegistrationRequest:
    def test_none_returns_none(self):
        assert iterm2.notifications._string_rpc_registration_request(None) is None

    def test_basic_rpc(self):
        rpc = iterm2.api_pb2.RPCRegistrationRequest()
        rpc.name = "test_func"
        result = iterm2.notifications._string_rpc_registration_request(rpc)
        assert result == "test_func()"

    def test_rpc_with_args(self):
        rpc = iterm2.api_pb2.RPCRegistrationRequest()
        rpc.name = "my_func"
        arg1 = rpc.arguments.add()
        arg1.name = "z"
        arg2 = rpc.arguments.add()
        arg2.name = "a"
        result = iterm2.notifications._string_rpc_registration_request(rpc)
        assert result == "my_func(a,z)"


class TestRegisterUnregisterNotificationHandler:
    def setup_method(self):
        iterm2.notifications._get_handlers().clear()

    def test_register_adds_handler(self):
        async def handler(conn, msg):
            pass
        iterm2.notifications._register_notification_handler(
            "session1", None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, handler)
        handlers = iterm2.notifications._get_handlers()
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        assert key in handlers
        assert handler in handlers[key]

    def test_register_with_rpc_string(self):
        async def handler(conn, msg):
            pass
        iterm2.notifications._register_notification_handler(
            "session1", "my_func()", iterm2.api_pb2.NOTIFY_ON_SERVER_ORIGINATED_RPC, handler)
        handlers = iterm2.notifications._get_handlers()
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_SERVER_ORIGINATED_RPC, "my_func()")
        assert key in handlers
        assert handler in handlers[key]

    def test_register_multiple_handlers_same_key(self):
        async def h1(conn, msg):
            pass
        async def h2(conn, msg):
            pass
        iterm2.notifications._register_notification_handler(
            "session1", None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, h1)
        iterm2.notifications._register_notification_handler(
            "session1", None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, h2)
        handlers = iterm2.notifications._get_handlers()
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        assert len(handlers[key]) == 2

    def test_unregister_removes_handler(self):
        async def handler(conn, msg):
            pass
        iterm2.notifications._register_notification_handler(
            "session1", None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, handler)
        iterm2.notifications._unregister_notification_handler(
            "session1", None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION, handler)
        handlers = iterm2.notifications._get_handlers()
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        assert handler not in handlers.get(key, [])

    def test_unregister_impl_removes_handler(self):
        async def handler(conn, msg):
            pass
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        iterm2.notifications._register_notification_handler_impl(key, handler)
        iterm2.notifications._unregister_notification_handler_impl(key, handler)
        handlers = iterm2.notifications._get_handlers()
        assert key not in handlers or handler not in handlers.get(key, [])

    def test_register_impl_appends_to_existing(self):
        async def h1(conn, msg):
            pass
        async def h2(conn, msg):
            pass
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        iterm2.notifications._register_notification_handler_impl(key, h1)
        iterm2.notifications._register_notification_handler_impl(key, h2)
        handlers = iterm2.notifications._get_handlers()
        assert len(handlers[key]) == 2

    def test_unregister_only_removes_matching_handler(self):
        async def h1(conn, msg):
            pass
        async def h2(conn, msg):
            pass
        key = ("session1", iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        iterm2.notifications._register_notification_handler_impl(key, h1)
        iterm2.notifications._register_notification_handler_impl(key, h2)
        iterm2.notifications._unregister_notification_handler_impl(key, h1)
        handlers = iterm2.notifications._get_handlers()
        assert h1 not in handlers.get(key, [])
        assert h2 in handlers.get(key, [])


class TestGetHandlerKeyFromNotification:
    def test_keystroke_notification(self):
        notif = iterm2.api_pb2.Notification()
        ks = notif.keystroke_notification
        ks.session = "sess123"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] == "sess123"
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_KEYSTROKE
        assert sub is ks

    def test_screen_update_notification(self):
        notif = iterm2.api_pb2.Notification()
        su = notif.screen_update_notification
        su.session = "sess456"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] == "sess456"
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_SCREEN_UPDATE

    def test_new_session_notification(self):
        notif = iterm2.api_pb2.Notification()
        ns = notif.new_session_notification
        ns.session_id = "new123"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] is None
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_NEW_SESSION

    def test_terminate_session_notification(self):
        notif = iterm2.api_pb2.Notification()
        ts = notif.terminate_session_notification
        ts.session_id = "term123"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] is None
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_TERMINATE_SESSION

    def test_layout_changed_notification(self):
        notif = iterm2.api_pb2.Notification()
        lc = notif.layout_changed_notification
        lc.SetInParent()
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] is None
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_LAYOUT_CHANGE

    def test_focus_changed_notification(self):
        notif = iterm2.api_pb2.Notification()
        fc = notif.focus_changed_notification
        fc.SetInParent()
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] is None
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_FOCUS_CHANGE

    def test_broadcast_domains_changed(self):
        notif = iterm2.api_pb2.Notification()
        bd = notif.broadcast_domains_changed
        bd.SetInParent()
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] is None
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_BROADCAST_CHANGE

    def test_prompt_notification(self):
        notif = iterm2.api_pb2.Notification()
        pn = notif.prompt_notification
        pn.session = "sess789"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] == "sess789"
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_PROMPT

    def test_custom_escape_sequence_notification(self):
        notif = iterm2.api_pb2.Notification()
        ces = notif.custom_escape_sequence_notification
        ces.session = "sessCES"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] == "sessCES"
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_CUSTOM_ESCAPE_SEQUENCE

    def test_server_originated_rpc_notification(self):
        notif = iterm2.api_pb2.Notification()
        sorpc = notif.server_originated_rpc_notification
        rpc = sorpc.rpc
        rpc.name = "test_func"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] is None
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_SERVER_ORIGINATED_RPC
        assert "test_func(" in key[2]

    def test_variable_changed_notification(self):
        notif = iterm2.api_pb2.Notification()
        vc = notif.variable_changed_notification
        vc.scope = iterm2.api_pb2.VariableScope.Value("SESSION")
        vc.identifier = "sessVar"
        vc.name = "myVar"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] == iterm2.api_pb2.VariableScope.Value("SESSION")
        assert key[1] == "sessVar"
        assert key[2] == "myVar"
        assert key[3] == iterm2.api_pb2.NOTIFY_ON_VARIABLE_CHANGE

    def test_profile_changed_notification(self):
        notif = iterm2.api_pb2.Notification()
        pc = notif.profile_changed_notification
        pc.guid = "profile-guid-123"
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key[0] == "profile-guid-123"
        assert key[1] == iterm2.api_pb2.NOTIFY_ON_PROFILE_CHANGE

    def test_unknown_notification(self):
        notif = iterm2.api_pb2.Notification()
        key, sub = iterm2.notifications._get_handler_key_from_notification(notif)
        assert key is None
        assert sub is notif


class TestGetNotificationHandlers:
    def setup_method(self):
        iterm2.notifications._get_handlers().clear()

    def test_no_handlers_returns_empty(self):
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        notif = msg.notification
        ns = notif.new_session_notification
        ns.session_id = "new1"
        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handlers == []
        assert sub is None

    def test_registered_handler_found(self):
        async def handler(conn, msg):
            pass
        key = (None, iterm2.api_pb2.NOTIFY_ON_NEW_SESSION)
        iterm2.notifications._register_notification_handler_impl(key, handler)
        msg = iterm2.api_pb2.ServerOriginatedMessage()
        notif = msg.notification
        ns = notif.new_session_notification
        ns.session_id = "new1"
        handlers, sub = iterm2.notifications._get_notification_handlers(msg)
        assert handler in handlers


class TestRegisterHelperIfNeeded:
    def test_registers_helper_once(self):
        if hasattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper'):
            delattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper')
        iterm2.notifications._register_helper_if_needed()
        assert hasattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper')
        assert iterm2.notifications._register_helper_if_needed.haveRegisteredHelper is True

    def test_idempotent(self):
        if hasattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper'):
            delattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper')
        initial_count = len(iterm2.connection.Connection.helpers)
        iterm2.notifications._register_helper_if_needed()
        iterm2.notifications._register_helper_if_needed()
        assert len(iterm2.connection.Connection.helpers) == initial_count + 1

    def test_helper_registered_in_connection(self):
        if hasattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper'):
            delattr(iterm2.notifications._register_helper_if_needed, 'haveRegisteredHelper')
        iterm2.notifications._register_helper_if_needed()
        assert iterm2.notifications._async_dispatch_helper in iterm2.connection.Connection.helpers
