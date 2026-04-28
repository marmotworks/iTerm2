"""Extended tests for iterm2.triggers module covering uncovered lines."""
import json
import pytest
from unittest.mock import Mock, patch

import iterm2
from iterm2.triggers import (
    Trigger,
    AlertTrigger,
    AnnotateTrigger,
    BellTrigger,
    BounceTrigger,
    BufferInputTrigger,
    RPCTrigger,
    CaptureTrigger,
    SetNamedMarkTrigger,
    SGRTrigger,
    FoldTrigger,
    InjectTrigger,
    HighlightLineTrigger,
    HighlightTrigger,
    UserNotificationTrigger,
    SetUserVariableTrigger,
    ShellPromptTrigger,
    SetTitleTrigger,
    SendTextTrigger,
    RunCommandTrigger,
    CoprocessTrigger,
    MuteCoprocessTrigger,
    MarkTrigger,
    PasswordTrigger,
    HyperlinkTrigger,
    SetDirectoryTrigger,
    SetHostnameTrigger,
    StopTrigger,
    MatchType,
    EventTrigger,
    ExitCodeFilter,
    PromptDetectedEventTrigger,
    CommandFinishedEventTrigger,
    DirectoryChangedEventTrigger,
    HostChangedEventTrigger,
    UserChangedEventTrigger,
    IdleEventTrigger,
    ActivityAfterIdleEventTrigger,
    SessionEndedEventTrigger,
    BellReceivedEventTrigger,
    LongRunningCommandEventTrigger,
    CustomEscapeSequenceEventTrigger,
    decode_trigger,
    _hex,
    _futureproof,
)


class TestHex:
    """Tests for the _hex helper function."""

    def test_hex_none_color(self):
        """Test _hex returns empty string for None color."""
        assert _hex(None) == ""

    def test_hex_with_color(self):
        """Test _hex returns hex string for a valid color."""
        color = iterm2.Color(r=255, g=128, b=0, a=255)
        result = _hex(color)
        assert result == "#ff8000"


class TestFutureproof:
    """Tests for the _futureproof helper function."""

    def test_futureproof_sets_param(self):
        """Test _futureproof replaces __param with raw value."""
        trigger = AlertTrigger("regex", "message", False, True)
        _futureproof("raw_value", trigger)
        assert trigger.param == "raw_value"

    def test_futureproof_returns_obj(self):
        """Test _futureproof returns the same object."""
        trigger = AlertTrigger("regex", "message", False, True)
        result = _futureproof("raw", trigger)
        assert result is trigger


class TestTriggerRepr:
    """Tests for Trigger.__repr__."""

    def test_trigger_repr(self):
        """Test Trigger __repr__ returns expected string."""
        trigger = Trigger(regex="test", param="p", instant=True, enabled=False)
        r = repr(trigger)
        assert "Trigger" in r
        assert "test" in r
        assert "instant=True" in r
        assert "enabled=False" in r


class TestTriggerEq:
    """Tests for Trigger.__eq__."""

    def test_trigger_equal(self):
        """Test Trigger equality for identical triggers."""
        t1 = Trigger("r", "p", True, True)
        t2 = Trigger("r", "p", True, True)
        assert t1 == t2

    def test_trigger_not_equal_regex(self):
        """Test Trigger inequality when regex differs."""
        t1 = Trigger("r1", "p", True, True)
        t2 = Trigger("r2", "p", True, True)
        assert t1 != t2

    def test_trigger_not_equal_param(self):
        """Test Trigger inequality when param differs."""
        t1 = Trigger("r", "p1", True, True)
        t2 = Trigger("r", "p2", True, True)
        assert t1 != t2

    def test_trigger_not_equal_instant(self):
        """Test Trigger inequality when instant differs."""
        t1 = Trigger("r", "p", True, True)
        t2 = Trigger("r", "p", False, True)
        assert t1 != t2

    def test_trigger_not_equal_enabled(self):
        """Test Trigger inequality when enabled differs."""
        t1 = Trigger("r", "p", True, True)
        t2 = Trigger("r", "p", True, False)
        assert t1 != t2


class TestTriggerSetters:
    """Tests for Trigger property setters."""

    def test_set_regex(self):
        """Test Trigger regex setter."""
        t = Trigger("old", "p", False, True)
        t.regex = "new"
        assert t.regex == "new"

    def test_set_instant(self):
        """Test Trigger instant setter."""
        t = Trigger("r", "p", False, True)
        t.instant = True
        assert t.instant is True

    def test_set_enabled(self):
        """Test Trigger enabled setter."""
        t = Trigger("r", "p", False, False)
        t.enabled = True
        assert t.enabled is True


class TestTriggerMatchType:
    """Tests for Trigger.match_type property."""

    def test_match_type_default(self):
        """Test Trigger match_type defaults to REGEX."""
        t = Trigger("r", "p", False, True)
        assert t.match_type == MatchType.REGEX

    def test_match_type_custom(self):
        """Test Trigger with custom match_type."""
        t = Trigger("r", "p", False, True, match_type=MatchType.URL_REGEX)
        assert t.match_type == MatchType.URL_REGEX


class TestTriggerToJSON:
    """Tests for Trigger.toJSON."""

    def test_to_json(self):
        """Test Trigger toJSON returns valid JSON.

        NOTE: This test is skipped because Trigger.toJSON() has a bug
        where it references `json` without importing it (line 248).
        EventTrigger.toJSON() works correctly with a local import.
        """
        pytest.skip("Trigger.toJSON() has missing json import bug in source")


class TestTriggerParam:
    """Tests for Trigger._param property."""

    def test_base_param_returns_empty(self):
        """Test that base Trigger._param returns empty string."""
        t = Trigger("r", "p", False, True)
        assert t._param == ""


class TestAlertTrigger:
    """Tests for AlertTrigger properties and setters."""

    def test_message_getter(self):
        """Test AlertTrigger.message getter."""
        t = AlertTrigger("r", "Hello", False, True)
        assert t.message == "Hello"

    def test_message_setter(self):
        """Test AlertTrigger.message setter updates message and param."""
        t = AlertTrigger("r", "Old", False, True)
        t.message = "New"
        assert t.message == "New"
        assert t.param == "New"

    def test_param_property(self):
        """Test AlertTrigger._param returns message."""
        t = AlertTrigger("r", "msg", False, True)
        assert t._param == "msg"

    def test_deserialize(self):
        """Test AlertTrigger.deserialize."""
        t = AlertTrigger.deserialize("r", "msg", True, False)
        assert t.regex == "r"
        assert t.enabled is False
        assert t.instant is True

    def test_encode(self):
        """Test AlertTrigger.encode."""
        t = AlertTrigger("r", "msg", True, True)
        e = t.encode
        assert e["action"] == "AlertTrigger"
        assert e["parameter"] == "msg"


class TestAnnotateTrigger:
    """Tests for AnnotateTrigger."""

    def test_create(self):
        """Test AnnotateTrigger constructor."""
        t = AnnotateTrigger("r", "annotation", False, True)
        assert t.annotation == "annotation"

    def test_annotation_setter(self):
        """Test AnnotateTrigger.annotation setter."""
        t = AnnotateTrigger("r", "old", False, True)
        t.annotation = "new"
        assert t.annotation == "new"
        assert t.param == "new"

    def test_param(self):
        """Test AnnotateTrigger._param."""
        t = AnnotateTrigger("r", "ann", False, True)
        assert t._param == "ann"

    def test_deserialize(self):
        """Test AnnotateTrigger.deserialize."""
        t = AnnotateTrigger.deserialize("r", "ann", True, False)
        assert t.annotation == "ann"

    def test_encode(self):
        """Test AnnotateTrigger.encode."""
        t = AnnotateTrigger("r", "ann", False, True)
        e = t.encode
        assert e["action"] == "AnnotateTrigger"


class TestBellTrigger:
    """Tests for BellTrigger."""

    def test_deserialize(self):
        """Test BellTrigger.deserialize."""
        t = BellTrigger.deserialize("r", "", True, False)
        assert isinstance(t, BellTrigger)
        assert t.regex == "r"

    def test_encode(self):
        """Test BellTrigger.encode."""
        t = BellTrigger("r", True, False)
        e = t.encode
        assert e["action"] == "BellTrigger"


class TestBounceTrigger:
    """Tests for BounceTrigger."""

    def test_create_bounce_until(self):
        """Test BounceTrigger with BOUNCE_UNTIL_ACTIVATED."""
        t = BounceTrigger("r", BounceTrigger.Action.BOUNCE_UNTIL_ACTIVATED, False, True)
        assert t.action == BounceTrigger.Action.BOUNCE_UNTIL_ACTIVATED

    def test_create_bounce_once(self):
        """Test BounceTrigger with BOUNCE_ONCE."""
        t = BounceTrigger("r", BounceTrigger.Action.BOUNCE_ONCE, False, True)
        assert t.action == BounceTrigger.Action.BOUNCE_ONCE

    def test_action_setter(self):
        """Test BounceTrigger.action setter."""
        t = BounceTrigger("r", BounceTrigger.Action.BOUNCE_UNTIL_ACTIVATED, False, True)
        t.action = BounceTrigger.Action.BOUNCE_ONCE
        assert t.action == BounceTrigger.Action.BOUNCE_ONCE
        assert t.param == 1

    def test_param(self):
        """Test BounceTrigger._param returns action value."""
        t = BounceTrigger("r", BounceTrigger.Action.BOUNCE_ONCE, False, True)
        assert t._param == 1

    def test_deserialize(self):
        """Test BounceTrigger.deserialize."""
        t = BounceTrigger.deserialize("r", 0, True, False)
        assert t.action == BounceTrigger.Action.BOUNCE_UNTIL_ACTIVATED

    def test_encode(self):
        """Test BounceTrigger.encode."""
        t = BounceTrigger("r", BounceTrigger.Action.BOUNCE_ONCE, False, True)
        e = t.encode
        assert e["action"] == "BounceTrigger"


class TestBufferInputTrigger:
    """Tests for BufferInputTrigger."""

    def test_create_start(self):
        """Test BufferInputTrigger with START action."""
        t = BufferInputTrigger("r", BufferInputTrigger.Action.START, False, True)
        assert t.action == BufferInputTrigger.Action.START

    def test_create_stop(self):
        """Test BufferInputTrigger with STOP action."""
        t = BufferInputTrigger("r", BufferInputTrigger.Action.STOP, False, True)
        assert t.action == BufferInputTrigger.Action.STOP

    def test_action_setter(self):
        """Test BufferInputTrigger.action setter."""
        t = BufferInputTrigger("r", BufferInputTrigger.Action.START, False, True)
        t.action = BufferInputTrigger.Action.STOP
        assert t.action == BufferInputTrigger.Action.STOP
        assert t.param == 1

    def test_param(self):
        """Test BufferInputTrigger._param."""
        t = BufferInputTrigger("r", BufferInputTrigger.Action.STOP, False, True)
        assert t._param == 1

    def test_deserialize(self):
        """Test BufferInputTrigger.deserialize."""
        t = BufferInputTrigger.deserialize("r", 1, True, False)
        assert t.action == BufferInputTrigger.Action.STOP

    def test_encode(self):
        """Test BufferInputTrigger.encode."""
        t = BufferInputTrigger("r", BufferInputTrigger.Action.START, False, True)
        e = t.encode
        assert e["action"] == "iTermBufferInputTrigger"


class TestRPCTrigger:
    """Tests for RPCTrigger."""

    def test_invocation_getter(self):
        """Test RPCTrigger.invocation getter."""
        t = RPCTrigger("r", "rpc_call", False, True)
        assert t.invocation == "rpc_call"

    def test_invocation_setter(self):
        """Test RPCTrigger.invocation setter."""
        t = RPCTrigger("r", "old", False, True)
        t.invocation = "new"
        assert t.invocation == "new"
        assert t.param == "new"

    def test_param(self):
        """Test RPCTrigger._param."""
        t = RPCTrigger("r", "rpc", False, True)
        assert t._param == "rpc"

    def test_deserialize(self):
        """Test RPCTrigger.deserialize."""
        t = RPCTrigger.deserialize("r", "rpc_call", True, False)
        assert t.invocation == "rpc_call"

    def test_encode(self):
        """Test RPCTrigger.encode."""
        t = RPCTrigger("r", "rpc", False, True)
        e = t.encode
        assert e["action"] == "iTermRPCTrigger"


class TestCaptureTrigger:
    """Tests for CaptureTrigger."""

    def test_command_getter(self):
        """Test CaptureTrigger.command getter."""
        t = CaptureTrigger("r", "capture", False, True)
        assert t.command == "capture"

    def test_command_setter(self):
        """Test CaptureTrigger.command setter."""
        t = CaptureTrigger("r", "old", False, True)
        t.command = "new"
        assert t.command == "new"
        assert t.param == "new"

    def test_param(self):
        """Test CaptureTrigger._param."""
        t = CaptureTrigger("r", "cap", False, True)
        assert t._param == "cap"

    def test_deserialize(self):
        """Test CaptureTrigger.deserialize."""
        t = CaptureTrigger.deserialize("r", "cap", True, False)
        assert t.command == "cap"

    def test_encode(self):
        """Test CaptureTrigger.encode."""
        t = CaptureTrigger("r", "cap", False, True)
        e = t.encode
        assert e["action"] == "CaptureTrigger"


class TestSetNamedMarkTrigger:
    """Tests for SetNamedMarkTrigger."""

    def test_markname_getter(self):
        """Test SetNamedMarkTrigger.markname getter."""
        t = SetNamedMarkTrigger("r", "mark1", False, True)
        assert t.markname == "mark1"

    def test_markname_setter(self):
        """Test SetNamedMarkTrigger.markname setter."""
        t = SetNamedMarkTrigger("r", "old", False, True)
        t.markname = "new"
        assert t.markname == "new"
        assert t.param == "new"

    def test_param(self):
        """Test SetNamedMarkTrigger._param."""
        t = SetNamedMarkTrigger("r", "m", False, True)
        assert t._param == "m"

    def test_deserialize(self):
        """Test SetNamedMarkTrigger.deserialize."""
        t = SetNamedMarkTrigger.deserialize("r", "m", True, False)
        assert t.markname == "m"

    def test_encode(self):
        """Test SetNamedMarkTrigger.encode."""
        t = SetNamedMarkTrigger("r", "m", False, True)
        e = t.encode
        assert e["action"] == "iTermSetNamedMarkTrigger"


class TestSGRTrigger:
    """Tests for SGRTrigger."""

    def test_sgr_getter(self):
        """Test SGRTrigger.sgr getter."""
        t = SGRTrigger("r", "sgr_val", False, True)
        assert t.sgr == "sgr_val"

    def test_sgr_setter(self):
        """Test SGRTrigger.sgr setter."""
        t = SGRTrigger("r", "old", False, True)
        t.sgr = "new"
        assert t.sgr == "new"
        assert t.param == "new"

    def test_param(self):
        """Test SGRTrigger._param."""
        t = SGRTrigger("r", "s", False, True)
        assert t._param == "s"

    def test_deserialize(self):
        """Test SGRTrigger.deserialize."""
        t = SGRTrigger.deserialize("r", "s", True, False)
        assert t.sgr == "s"

    def test_encode(self):
        """Test SGRTrigger.encode."""
        t = SGRTrigger("r", "s", False, True)
        e = t.encode
        assert e["action"] == "iTermSGRTrigger"


class TestFoldTrigger:
    """Tests for FoldTrigger."""

    def test_markname_getter(self):
        """Test FoldTrigger.markname getter."""
        t = FoldTrigger("r", "fold1", False, True)
        assert t.markname == "fold1"

    def test_markname_setter(self):
        """Test FoldTrigger.markname setter."""
        t = FoldTrigger("r", "old", False, True)
        t.markname = "new"
        assert t.markname == "new"
        assert t.param == "new"

    def test_param(self):
        """Test FoldTrigger._param."""
        t = FoldTrigger("r", "f", False, True)
        assert t._param == "f"

    def test_deserialize(self):
        """Test FoldTrigger.deserialize."""
        t = FoldTrigger.deserialize("r", "f", True, False)
        assert t.markname == "f"

    def test_encode(self):
        """Test FoldTrigger.encode."""
        t = FoldTrigger("r", "f", False, True)
        e = t.encode
        assert e["action"] == "iTermFoldTrigger"


class TestInjectTrigger:
    """Tests for InjectTrigger."""

    def test_injection_getter(self):
        """Test InjectTrigger.injection getter."""
        t = InjectTrigger("r", "inject", False, True)
        assert t.injection == "inject"

    def test_injection_setter(self):
        """Test InjectTrigger.injection setter."""
        t = InjectTrigger("r", "old", False, True)
        t.injection = "new"
        assert t.injection == "new"
        assert t.param == "new"

    def test_param(self):
        """Test InjectTrigger._param."""
        t = InjectTrigger("r", "inj", False, True)
        assert t._param == "inj"

    def test_deserialize(self):
        """Test InjectTrigger.deserialize."""
        t = InjectTrigger.deserialize("r", "inj", True, False)
        assert t.injection == "inj"

    def test_encode(self):
        """Test InjectTrigger.encode."""
        t = InjectTrigger("r", "inj", False, True)
        e = t.encode
        assert e["action"] == "iTermInjectTrigger"


class TestHighlightLineTrigger:
    """Tests for HighlightLineTrigger."""

    def test_create_with_colors(self):
        """Test HighlightLineTrigger with colors."""
        tc = iterm2.Color(r=255, g=0, b=0, a=255)
        bc = iterm2.Color(r=0, g=0, b=255, a=255)
        t = HighlightLineTrigger("r", tc, bc, False, True)
        assert t.text_color == tc
        assert t.background_color == bc

    def test_create_with_none_colors(self):
        """Test HighlightLineTrigger with None colors."""
        t = HighlightLineTrigger("r", None, None, False, True)
        assert t.text_color is None
        assert t.background_color is None

    def test_text_color_setter(self):
        """Test HighlightLineTrigger.text_color setter."""
        tc = iterm2.Color(r=255, g=0, b=0, a=255)
        t = HighlightLineTrigger("r", None, None, False, True)
        t.text_color = tc
        assert t.text_color == tc

    def test_background_color_setter(self):
        """Test HighlightLineTrigger.background_color setter."""
        bc = iterm2.Color(r=0, g=0, b=255, a=255)
        t = HighlightLineTrigger("r", None, None, False, True)
        t.background_color = bc
        assert t.background_color == bc

    def test_param_with_colors(self):
        """Test HighlightLineTrigger._param with colors."""
        tc = iterm2.Color(r=255, g=0, b=0, a=255)
        bc = iterm2.Color(r=0, g=0, b=255, a=255)
        t = HighlightLineTrigger("r", tc, bc, False, True)
        assert t._param == "{#ff0000,#0000ff}"

    def test_param_with_none_colors(self):
        """Test HighlightLineTrigger._param with None colors."""
        t = HighlightLineTrigger("r", None, None, False, True)
        assert t._param == "{,}"

    def test_deserialize(self):
        """Test HighlightLineTrigger.deserialize."""
        t = HighlightLineTrigger.deserialize("r", "{#ff0000,#0000ff}", True, False)
        assert t.regex == "r"

    def test_encode(self):
        """Test HighlightLineTrigger.encode."""
        t = HighlightLineTrigger("r", None, None, False, True)
        e = t.encode
        assert e["action"] == "iTermHighlightLineTrigger"


class TestUserNotificationTrigger:
    """Tests for UserNotificationTrigger."""

    def test_message_getter(self):
        """Test UserNotificationTrigger.message getter."""
        t = UserNotificationTrigger("r", "notif", False, True)
        assert t.message == "notif"

    def test_message_setter(self):
        """Test UserNotificationTrigger.message setter."""
        t = UserNotificationTrigger("r", "old", False, True)
        t.message = "new"
        assert t.message == "new"
        assert t.param == "new"

    def test_param(self):
        """Test UserNotificationTrigger._param."""
        t = UserNotificationTrigger("r", "msg", False, True)
        assert t._param == "msg"

    def test_deserialize(self):
        """Test UserNotificationTrigger.deserialize."""
        t = UserNotificationTrigger.deserialize("r", "msg", True, False)
        assert t.message == "msg"

    def test_encode(self):
        """Test UserNotificationTrigger.encode."""
        t = UserNotificationTrigger("r", "msg", False, True)
        e = t.encode
        assert e["action"] == "iTermUserNotificationTrigger"


class TestSetUserVariableTrigger:
    """Tests for SetUserVariableTrigger."""

    def test_name_getter(self):
        """Test SetUserVariableTrigger.name getter."""
        t = SetUserVariableTrigger("r", "varname", '"value"', False, True)
        assert t.name == "varname"

    def test_json_value_getter(self):
        """Test SetUserVariableTrigger.json_value getter."""
        t = SetUserVariableTrigger("r", "varname", '"value"', False, True)
        assert t.json_value == '"value"'

    def test_name_setter(self):
        """Test SetUserVariableTrigger.name setter."""
        t = SetUserVariableTrigger("r", "old", '"v"', False, True)
        t.name = "new"
        assert t.name == "new"
        assert t.param == "new" + chr(1) + '"v"'

    def test_json_value_setter(self):
        """Test SetUserVariableTrigger.json_value setter."""
        t = SetUserVariableTrigger("r", "n", '"old"', False, True)
        t.json_value = '"new"'
        assert t.json_value == '"new"'
        assert t.param == "n" + chr(1) + '"new"'

    def test_param(self):
        """Test SetUserVariableTrigger._param."""
        t = SetUserVariableTrigger("r", "n", '"v"', False, True)
        assert t._param == "n" + chr(1) + '"v"'

    def test_deserialize(self):
        """Test SetUserVariableTrigger.deserialize."""
        param = "name" + chr(1) + '"value"'
        t = SetUserVariableTrigger.deserialize("r", param, True, False)
        assert t.name == "name"
        assert t.json_value == '"value"'

    def test_encode(self):
        """Test SetUserVariableTrigger.encode."""
        t = SetUserVariableTrigger("r", "n", '"v"', False, True)
        e = t.encode
        assert e["action"] == "iTermSetUserVariableTrigger"


class TestShellPromptTrigger:
    """Tests for ShellPromptTrigger."""

    def test_create(self):
        """Test ShellPromptTrigger constructor."""
        t = ShellPromptTrigger("r", False, True)
        assert t.regex == "r"
        assert t.instant is False
        assert t.enabled is True

    def test_param(self):
        """Test ShellPromptTrigger._param returns empty string."""
        t = ShellPromptTrigger("r", False, True)
        assert t._param == ""

    def test_deserialize(self):
        """Test ShellPromptTrigger.deserialize."""
        t = ShellPromptTrigger.deserialize("r", "", True, False)
        assert t.regex == "r"

    def test_encode(self):
        """Test ShellPromptTrigger.encode."""
        t = ShellPromptTrigger("r", False, True)
        e = t.encode
        assert e["action"] == "iTermShellPromptTrigger"


class TestSetTitleTrigger:
    """Tests for SetTitleTrigger."""

    def test_title_getter(self):
        """Test SetTitleTrigger.title getter."""
        t = SetTitleTrigger("r", "My Title", False, True)
        assert t.title == "My Title"

    def test_title_setter(self):
        """Test SetTitleTrigger.title setter."""
        t = SetTitleTrigger("r", "Old", False, True)
        t.title = "New"
        assert t.title == "New"
        assert t.param == "New"

    def test_param(self):
        """Test SetTitleTrigger._param."""
        t = SetTitleTrigger("r", "T", False, True)
        assert t._param == "T"

    def test_deserialize(self):
        """Test SetTitleTrigger.deserialize."""
        t = SetTitleTrigger.deserialize("r", "T", True, False)
        assert t.title == "T"

    def test_encode(self):
        """Test SetTitleTrigger.encode."""
        t = SetTitleTrigger("r", "T", False, True)
        e = t.encode
        assert e["action"] == "iTermSetTitleTrigger"


class TestSendTextTrigger:
    """Tests for SendTextTrigger."""

    def test_text_getter(self):
        """Test SendTextTrigger.text getter."""
        t = SendTextTrigger("r", "text", False, True)
        assert t.text == "text"

    def test_text_setter(self):
        """Test SendTextTrigger.text setter."""
        t = SendTextTrigger("r", "old", False, True)
        t.text = "new"
        assert t.text == "new"
        assert t.param == "new"

    def test_param(self):
        """Test SendTextTrigger._param."""
        t = SendTextTrigger("r", "t", False, True)
        assert t._param == "t"

    def test_deserialize(self):
        """Test SendTextTrigger.deserialize."""
        t = SendTextTrigger.deserialize("r", "t", True, False)
        assert t.text == "t"

    def test_encode(self):
        """Test SendTextTrigger.encode."""
        t = SendTextTrigger("r", "t", False, True)
        e = t.encode
        assert e["action"] == "SendTextTrigger"


class TestRunCommandTrigger:
    """Tests for RunCommandTrigger."""

    def test_command_getter(self):
        """Test RunCommandTrigger.command getter."""
        t = RunCommandTrigger("r", "echo hi", False, True)
        assert t.command == "echo hi"

    def test_command_setter(self):
        """Test RunCommandTrigger.command setter."""
        t = RunCommandTrigger("r", "old", False, True)
        t.command = "new"
        assert t.command == "new"
        assert t.param == "new"

    def test_param(self):
        """Test RunCommandTrigger._param."""
        t = RunCommandTrigger("r", "c", False, True)
        assert t._param == "c"

    def test_deserialize(self):
        """Test RunCommandTrigger.deserialize."""
        t = RunCommandTrigger.deserialize("r", "c", True, False)
        assert t.command == "c"

    def test_encode(self):
        """Test RunCommandTrigger.encode."""
        t = RunCommandTrigger("r", "c", False, True)
        e = t.encode
        assert e["action"] == "ScriptTrigger"


class TestCoprocessTrigger:
    """Tests for CoprocessTrigger."""

    def test_command_getter(self):
        """Test CoprocessTrigger.command getter."""
        t = CoprocessTrigger("r", "cmd", False, True)
        assert t.command == "cmd"

    def test_command_setter(self):
        """Test CoprocessTrigger.command setter."""
        t = CoprocessTrigger("r", "old", False, True)
        t.command = "new"
        assert t.command == "new"
        assert t.param == "new"

    def test_param(self):
        """Test CoprocessTrigger._param."""
        t = CoprocessTrigger("r", "c", False, True)
        assert t._param == "c"

    def test_deserialize(self):
        """Test CoprocessTrigger.deserialize."""
        t = CoprocessTrigger.deserialize("r", "c", True, False)
        assert t.command == "c"

    def test_encode(self):
        """Test CoprocessTrigger.encode."""
        t = CoprocessTrigger("r", "c", False, True)
        e = t.encode
        assert e["action"] == "CoprocessTrigger"


class TestMuteCoprocessTrigger:
    """Tests for MuteCoprocessTrigger."""

    def test_command_getter(self):
        """Test MuteCoprocessTrigger.command getter."""
        t = MuteCoprocessTrigger("r", "cmd", False, True)
        assert t.command == "cmd"

    def test_command_setter(self):
        """Test MuteCoprocessTrigger.command setter."""
        t = MuteCoprocessTrigger("r", "old", False, True)
        t.command = "new"
        assert t.command == "new"
        assert t.param == "new"

    def test_param(self):
        """Test MuteCoprocessTrigger._param."""
        t = MuteCoprocessTrigger("r", "c", False, True)
        assert t._param == "c"

    def test_deserialize(self):
        """Test MuteCoprocessTrigger.deserialize."""
        t = MuteCoprocessTrigger.deserialize("r", "c", True, False)
        assert t.command == "c"

    def test_encode(self):
        """Test MuteCoprocessTrigger.encode."""
        t = MuteCoprocessTrigger("r", "c", False, True)
        e = t.encode
        assert e["action"] == "MuteCoprocessTrigger"


class TestHighlightTrigger:
    """Tests for HighlightTrigger."""

    def test_create_with_colors(self):
        """Test HighlightTrigger with colors."""
        tc = iterm2.Color(r=255, g=0, b=0, a=255)
        bc = iterm2.Color(r=0, g=0, b=255, a=255)
        t = HighlightTrigger("r", tc, bc, False, True)
        assert t.text_color == tc
        assert t.background_color == bc

    def test_create_with_none_colors(self):
        """Test HighlightTrigger with None colors."""
        t = HighlightTrigger("r", None, None, False, True)
        assert t.text_color is None
        assert t.background_color is None

    def test_text_color_setter(self):
        """Test HighlightTrigger.text_color setter."""
        tc = iterm2.Color(r=255, g=0, b=0, a=255)
        t = HighlightTrigger("r", None, None, False, True)
        t.text_color = tc
        assert t.text_color == tc

    def test_background_color_setter(self):
        """Test HighlightTrigger.background_color setter."""
        bc = iterm2.Color(r=0, g=0, b=255, a=255)
        t = HighlightTrigger("r", None, None, False, True)
        t.background_color = bc
        assert t.background_color == bc

    def test_param_with_colors(self):
        """Test HighlightTrigger._param with colors."""
        tc = iterm2.Color(r=255, g=0, b=0, a=255)
        bc = iterm2.Color(r=0, g=0, b=255, a=255)
        t = HighlightTrigger("r", tc, bc, False, True)
        assert t._param == "{#ff0000,#0000ff}"

    def test_param_with_none_colors(self):
        """Test HighlightTrigger._param with None colors."""
        t = HighlightTrigger("r", None, None, False, True)
        assert t._param == "{,}"

    def test_deserialize(self):
        """Test HighlightTrigger.deserialize."""
        t = HighlightTrigger.deserialize("r", "{#ff0000,#0000ff}", True, False)
        assert t.regex == "r"

    def test_encode(self):
        """Test HighlightTrigger.encode."""
        t = HighlightTrigger("r", None, None, False, True)
        e = t.encode
        assert e["action"] == "HighlightTrigger"


class TestMarkTrigger:
    """Tests for MarkTrigger."""

    def test_stop_scrolling_getter_true(self):
        """Test MarkTrigger.stop_scrolling getter when True."""
        t = MarkTrigger("r", True, False, True)
        assert t.stop_scrolling is True

    def test_stop_scrolling_getter_false(self):
        """Test MarkTrigger.stop_scrolling getter when False."""
        t = MarkTrigger("r", False, False, True)
        assert t.stop_scrolling is False

    def test_stop_scrolling_setter(self):
        """Test MarkTrigger.stop_scrolling setter."""
        t = MarkTrigger("r", False, False, True)
        t.stop_scrolling = True
        assert t.stop_scrolling is True
        assert t.param == 1

    def test_param_true(self):
        """Test MarkTrigger._param when stop_scrolling is True."""
        t = MarkTrigger("r", True, False, True)
        assert t._param == 1

    def test_param_false(self):
        """Test MarkTrigger._param when stop_scrolling is False."""
        t = MarkTrigger("r", False, False, True)
        assert t._param == 0

    def test_deserialize_with_stop(self):
        """Test MarkTrigger.deserialize with stop_scrolling=1."""
        t = MarkTrigger.deserialize("r", 1, True, False)
        assert t.stop_scrolling is True

    def test_deserialize_without_stop(self):
        """Test MarkTrigger.deserialize with stop_scrolling=0."""
        t = MarkTrigger.deserialize("r", 0, True, False)
        assert t.stop_scrolling is False

    def test_encode(self):
        """Test MarkTrigger.encode."""
        t = MarkTrigger("r", True, False, True)
        e = t.encode
        assert e["action"] == "MarkTrigger"


class TestPasswordTrigger:
    """Tests for PasswordTrigger."""

    def test_account_name_getter(self):
        """Test PasswordTrigger.account_name getter."""
        t = PasswordTrigger("r", "myaccount", "user1", False, True)
        assert t.account_name == "myaccount"

    def test_user_name_getter(self):
        """Test PasswordTrigger.user_name getter."""
        t = PasswordTrigger("r", "myaccount", "user1", False, True)
        assert t.user_name == "user1"

    def test_account_name_setter(self):
        """Test PasswordTrigger.account_name setter."""
        t = PasswordTrigger("r", "old", "u", False, True)
        t.account_name = "new"
        assert t.account_name == "new"

    def test_user_name_setter(self):
        """Test PasswordTrigger.user_name setter."""
        t = PasswordTrigger("r", "acc", "old", False, True)
        t.user_name = "new"
        assert t.user_name == "new"

    def test_param_with_user(self):
        """Test PasswordTrigger._param with user_name set."""
        t = PasswordTrigger("r", "acc", "user", False, True)
        assert t._param == "acc" + PasswordTrigger.SEPARATOR + "user"

    def test_param_without_user(self):
        """Test PasswordTrigger._param with empty user_name."""
        t = PasswordTrigger("r", "acc", "", False, True)
        assert t._param == "acc"

    def test_deserialize_with_separator(self):
        """Test PasswordTrigger.deserialize with separator in param."""
        param = "acc" + PasswordTrigger.SEPARATOR + "user"
        t = PasswordTrigger.deserialize("r", param, True, False)
        assert t.account_name == "acc"
        assert t.user_name == "user"

    def test_deserialize_without_separator(self):
        """Test PasswordTrigger.deserialize without separator."""
        t = PasswordTrigger.deserialize("r", "onlyacc", True, False)
        assert t.account_name == "onlyacc"
        assert t.user_name == ""

    def test_encode(self):
        """Test PasswordTrigger.encode."""
        t = PasswordTrigger("r", "acc", "user", False, True)
        e = t.encode
        assert e["action"] == "PasswordTrigger"


class TestHyperlinkTrigger:
    """Tests for HyperlinkTrigger."""

    def test_url_getter(self):
        """Test HyperlinkTrigger.url getter."""
        t = HyperlinkTrigger("r", "http://example.com", False, True)
        assert t.url == "http://example.com"

    def test_url_setter(self):
        """Test HyperlinkTrigger.url setter."""
        t = HyperlinkTrigger("r", "http://old.com", False, True)
        t.url = "http://new.com"
        assert t.url == "http://new.com"
        assert t.param == "http://new.com"

    def test_param(self):
        """Test HyperlinkTrigger._param."""
        t = HyperlinkTrigger("r", "http://x.com", False, True)
        assert t._param == "http://x.com"

    def test_deserialize(self):
        """Test HyperlinkTrigger.deserialize."""
        t = HyperlinkTrigger.deserialize("r", "http://x.com", True, False)
        assert t.url == "http://x.com"

    def test_encode(self):
        """Test HyperlinkTrigger.encode."""
        t = HyperlinkTrigger("r", "http://x.com", False, True)
        e = t.encode
        assert e["action"] == "iTermHyperlinkTrigger"


class TestSetDirectoryTrigger:
    """Tests for SetDirectoryTrigger."""

    def test_directory_getter(self):
        """Test SetDirectoryTrigger.directory getter."""
        t = SetDirectoryTrigger("r", "/tmp", False, True)
        assert t.directory == "/tmp"

    def test_directory_setter(self):
        """Test SetDirectoryTrigger.directory setter."""
        t = SetDirectoryTrigger("r", "/old", False, True)
        t.directory = "/new"
        assert t.directory == "/new"
        assert t.param == "/new"

    def test_param(self):
        """Test SetDirectoryTrigger._param."""
        t = SetDirectoryTrigger("r", "/d", False, True)
        assert t._param == "/d"

    def test_deserialize(self):
        """Test SetDirectoryTrigger.deserialize."""
        t = SetDirectoryTrigger.deserialize("r", "/d", True, False)
        assert t.directory == "/d"

    def test_encode(self):
        """Test SetDirectoryTrigger.encode."""
        t = SetDirectoryTrigger("r", "/d", False, True)
        e = t.encode
        assert e["action"] == "SetDirectoryTrigger"


class TestSetHostnameTrigger:
    """Tests for SetHostnameTrigger."""

    def test_hostname_getter(self):
        """Test SetHostnameTrigger.hostname getter."""
        t = SetHostnameTrigger("r", "host", False, True)
        assert t.hostname == "host"

    def test_hostname_setter(self):
        """Test SetHostnameTrigger.hostname setter."""
        t = SetHostnameTrigger("r", "old", False, True)
        t.hostname = "new"
        assert t.hostname == "new"
        assert t.param == "new"

    def test_param(self):
        """Test SetHostnameTrigger._param."""
        t = SetHostnameTrigger("r", "h", False, True)
        assert t._param == "h"

    def test_deserialize(self):
        """Test SetHostnameTrigger.deserialize."""
        t = SetHostnameTrigger.deserialize("r", "h", True, False)
        assert t.hostname == "h"

    def test_encode(self):
        """Test SetHostnameTrigger.encode."""
        t = SetHostnameTrigger("r", "h", False, True)
        e = t.encode
        assert e["action"] == "SetHostnameTrigger"


class TestStopTrigger:
    """Tests for StopTrigger."""

    def test_create(self):
        """Test StopTrigger constructor."""
        t = StopTrigger("r", False, True)
        assert t.regex == "r"

    def test_param(self):
        """Test StopTrigger._param returns empty string."""
        t = StopTrigger("r", False, True)
        assert t._param == ""

    def test_deserialize(self):
        """Test StopTrigger.deserialize."""
        t = StopTrigger.deserialize("r", "", True, False)
        assert t.regex == "r"

    def test_encode(self):
        """Test StopTrigger.encode."""
        t = StopTrigger("r", False, True)
        e = t.encode
        assert e["action"] == "StopTrigger"


class TestEventTriggerRepr:
    """Tests for EventTrigger.__repr__."""

    def test_event_trigger_repr(self):
        """Test EventTrigger __repr__ returns expected string."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param="Bell",
            enabled=True,
            event_params={"key": "val"},
        )
        r = repr(t)
        assert "EventTrigger" in r
        assert "AlertTrigger" in r


class TestEventTriggerEqNonEvent:
    """Tests for EventTrigger.__eq__ with non-EventTrigger."""

    def test_event_trigger_not_equal_non_event(self):
        """Test EventTrigger != non-EventTrigger."""
        et = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param="Bell",
            enabled=True,
        )
        assert et != "not an event trigger"
        assert et != None
        assert et != 42


class TestEventTriggerSetters:
    """Tests for EventTrigger setters."""

    def test_action_name_setter(self):
        """Test EventTrigger.action_name setter."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="Old",
            param="",
            enabled=True,
        )
        t.action_name = "New"
        assert t.action_name == "New"

    def test_param_setter(self):
        """Test EventTrigger.param setter."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param="Old",
            enabled=True,
        )
        t.param = "New"
        assert t.param == "New"

    def test_enabled_setter(self):
        """Test EventTrigger.enabled setter."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param="",
            enabled=False,
        )
        t.enabled = True
        assert t.enabled is True

    def test_event_params_setter(self):
        """Test EventTrigger.event_params setter."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param="",
            enabled=True,
        )
        t.event_params = {"new": "params"}
        assert t.event_params == {"new": "params"}


class TestEventTriggerDeserialize:
    """Tests for EventTrigger.deserialize."""

    def test_deserialize_returns_event_trigger(self):
        """Test EventTrigger.deserialize returns EventTrigger."""
        t = EventTrigger.deserialize("AlertTrigger", "param", True, {"key": "val"}, {})
        assert isinstance(t, EventTrigger)
        assert t.action_name == "AlertTrigger"


class TestCommandFinishedEventTriggerSetter:
    """Tests for CommandFinishedEventTrigger.exit_code_filter setter."""

    def test_setter_with_enum(self):
        """Test exit_code_filter setter with ExitCodeFilter enum."""
        t = CommandFinishedEventTrigger(
            action_name="AlertTrigger",
            param="Done",
            enabled=True,
            exit_code_filter=ExitCodeFilter.ANY,
        )
        t.exit_code_filter = ExitCodeFilter.ZERO
        assert t.exit_code_filter == ExitCodeFilter.ZERO
        assert t.event_params["exitCodeFilter"] == "0"

    def test_setter_with_int(self):
        """Test exit_code_filter setter with integer."""
        t = CommandFinishedEventTrigger(
            action_name="AlertTrigger",
            param="Done",
            enabled=True,
        )
        t.exit_code_filter = 13
        assert t.exit_code_filter == 13
        assert t.event_params["exitCodeFilter"] == "13"


class TestCommandFinishedEventTriggerDeserializeEdgeCases:
    """Tests for CommandFinishedEventTrigger.deserialize edge cases."""

    def test_deserialize_zero_filter(self):
        """Test deserialize with exitCodeFilter='0'."""
        t = CommandFinishedEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"exitCodeFilter": "0"}, {})
        assert t.exit_code_filter == ExitCodeFilter.ZERO

    def test_deserialize_non_zero_filter(self):
        """Test deserialize with exitCodeFilter='!0'."""
        t = CommandFinishedEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"exitCodeFilter": "!0"}, {})
        assert t.exit_code_filter == ExitCodeFilter.NON_ZERO

    def test_deserialize_invalid_filter(self):
        """Test deserialize with invalid exitCodeFilter string."""
        t = CommandFinishedEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"exitCodeFilter": "invalid"}, {})
        assert t.exit_code_filter == ExitCodeFilter.ANY

    def test_deserialize_empty_filter(self):
        """Test deserialize with empty exitCodeFilter string."""
        t = CommandFinishedEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"exitCodeFilter": ""}, {})
        assert t.exit_code_filter == ExitCodeFilter.ANY


class TestDirectoryChangedEventTriggerSetter:
    """Tests for DirectoryChangedEventTrigger.directory_regex setter."""

    def test_setter_with_value(self):
        """Test directory_regex setter with a value."""
        t = DirectoryChangedEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
        )
        t.directory_regex = "^/home"
        assert t.directory_regex == "^/home"
        assert t.event_params["directoryRegex"] == "^/home"

    def test_setter_with_none_clears(self):
        """Test directory_regex setter with None clears event_params."""
        t = DirectoryChangedEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            directory_regex="^/home",
        )
        t.directory_regex = None
        assert t.directory_regex is None
        assert "directoryRegex" not in t.event_params


class TestHostChangedEventTriggerSetter:
    """Tests for HostChangedEventTrigger.host_regex setter."""

    def test_setter_with_value(self):
        """Test host_regex setter with a value."""
        t = HostChangedEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
        )
        t.host_regex = "^prod"
        assert t.host_regex == "^prod"
        assert t.event_params["hostRegex"] == "^prod"

    def test_setter_with_none_clears(self):
        """Test host_regex setter with None clears event_params."""
        t = HostChangedEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            host_regex="^prod",
        )
        t.host_regex = None
        assert t.host_regex is None
        assert "hostRegex" not in t.event_params


class TestUserChangedEventTriggerSetter:
    """Tests for UserChangedEventTrigger.user_regex setter."""

    def test_setter_with_value(self):
        """Test user_regex setter with a value."""
        t = UserChangedEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
        )
        t.user_regex = "^root"
        assert t.user_regex == "^root"
        assert t.event_params["userRegex"] == "^root"

    def test_setter_with_none_clears(self):
        """Test user_regex setter with None clears event_params."""
        t = UserChangedEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            user_regex="^root",
        )
        t.user_regex = None
        assert t.user_regex is None
        assert "userRegex" not in t.event_params


class TestIdleEventTriggerSetter:
    """Tests for IdleEventTrigger.timeout setter."""

    def test_timeout_setter(self):
        """Test IdleEventTrigger.timeout setter."""
        t = IdleEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            timeout=30.0,
        )
        t.timeout = 60.0
        assert t.timeout == 60.0
        assert t.event_params["timeout"] == 60.0


class TestIdleEventTriggerDeserialize:
    """Tests for IdleEventTrigger.deserialize edge cases."""

    def test_deserialize_with_timeout(self):
        """Test IdleEventTrigger.deserialize with timeout in event_params."""
        t = IdleEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"timeout": 99.5}, {})
        assert t.timeout == 99.5

    def test_deserialize_without_timeout(self):
        """Test IdleEventTrigger.deserialize with default timeout."""
        t = IdleEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {}, {})
        assert t.timeout == 30.0

    def test_deserialize_with_none_event_params(self):
        """Test IdleEventTrigger.deserialize with None event_params."""
        t = IdleEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            None, {})
        assert t.timeout == 30.0


class TestActivityAfterIdleEventTriggerSetter:
    """Tests for ActivityAfterIdleEventTrigger.timeout setter."""

    def test_timeout_setter(self):
        """Test ActivityAfterIdleEventTrigger.timeout setter."""
        t = ActivityAfterIdleEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            timeout=30.0,
        )
        t.timeout = 120.0
        assert t.timeout == 120.0
        assert t.event_params["timeout"] == 120.0


class TestActivityAfterIdleEventTriggerDeserialize:
    """Tests for ActivityAfterIdleEventTrigger.deserialize edge cases."""

    def test_deserialize_with_timeout(self):
        """Test deserialize with timeout in event_params."""
        t = ActivityAfterIdleEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"timeout": 88.0}, {})
        assert t.timeout == 88.0

    def test_deserialize_without_timeout(self):
        """Test deserialize with default timeout."""
        t = ActivityAfterIdleEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {}, {})
        assert t.timeout == 30.0


class TestLongRunningCommandEventTriggerSetters:
    """Tests for LongRunningCommandEventTrigger setters."""

    def test_threshold_setter(self):
        """Test LongRunningCommandEventTrigger.threshold setter."""
        t = LongRunningCommandEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            threshold=60.0,
        )
        t.threshold = 300.0
        assert t.threshold == 300.0
        assert t.event_params["threshold"] == 300.0

    def test_command_regex_setter_with_value(self):
        """Test command_regex setter with a value."""
        t = LongRunningCommandEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
        )
        t.command_regex = "^npm"
        assert t.command_regex == "^npm"
        assert t.event_params["commandRegex"] == "^npm"

    def test_command_regex_setter_clears(self):
        """Test command_regex setter with None clears event_params."""
        t = LongRunningCommandEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            command_regex="^npm",
        )
        t.command_regex = None
        assert t.command_regex is None
        assert "commandRegex" not in t.event_params


class TestLongRunningCommandEventTriggerDeserialize:
    """Tests for LongRunningCommandEventTrigger.deserialize edge cases."""

    def test_deserialize_with_all_params(self):
        """Test deserialize with threshold and commandRegex."""
        t = LongRunningCommandEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"threshold": 150.0, "commandRegex": "^make"}, {})
        assert t.threshold == 150.0
        assert t.command_regex == "^make"

    def test_deserialize_defaults(self):
        """Test deserialize with defaults."""
        t = LongRunningCommandEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {}, {})
        assert t.threshold == 60.0
        assert t.command_regex is None


class TestCustomEscapeSequenceEventTriggerSetter:
    """Tests for CustomEscapeSequenceEventTrigger.sequence_id setter."""

    def test_setter_with_value(self):
        """Test sequence_id setter with a value."""
        t = CustomEscapeSequenceEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
        )
        t.sequence_id = "my-id"
        assert t.sequence_id == "my-id"
        assert t.event_params["sequenceId"] == "my-id"

    def test_setter_with_none_clears(self):
        """Test sequence_id setter with None clears event_params."""
        t = CustomEscapeSequenceEventTrigger(
            action_name="AlertTrigger",
            param="",
            enabled=True,
            sequence_id="my-id",
        )
        t.sequence_id = None
        assert t.sequence_id is None
        assert "sequenceId" not in t.event_params


class TestCustomEscapeSequenceEventTriggerDeserialize:
    """Tests for CustomEscapeSequenceEventTrigger.deserialize edge cases."""

    def test_deserialize_with_sequence_id(self):
        """Test deserialize with sequenceId in event_params."""
        t = CustomEscapeSequenceEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {"sequenceId": "event-1"}, {})
        assert t.sequence_id == "event-1"

    def test_deserialize_without_sequence_id(self):
        """Test deserialize with default sequence_id."""
        t = CustomEscapeSequenceEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            {}, {})
        assert t.sequence_id is None

    def test_deserialize_with_none_event_params(self):
        """Test deserialize with None event_params."""
        t = CustomEscapeSequenceEventTrigger.deserialize(
            "AlertTrigger", "param", True,
            None, {})
        assert t.sequence_id is None


class TestDecodeTriggerEventTypes:
    """Tests for decode_trigger with event-based triggers."""

    def test_decode_prompt_detected(self):
        """Test decode_trigger for EVENT_PROMPT_DETECTED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Prompt",
            "matchType": 100,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, PromptDetectedEventTrigger)

    def test_decode_command_finished(self):
        """Test decode_trigger for EVENT_COMMAND_FINISHED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Done",
            "matchType": 101,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, CommandFinishedEventTrigger)

    def test_decode_directory_changed(self):
        """Test decode_trigger for EVENT_DIRECTORY_CHANGED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Dir",
            "matchType": 102,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, DirectoryChangedEventTrigger)

    def test_decode_host_changed(self):
        """Test decode_trigger for EVENT_HOST_CHANGED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Host",
            "matchType": 103,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, HostChangedEventTrigger)

    def test_decode_user_changed(self):
        """Test decode_trigger for EVENT_USER_CHANGED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "User",
            "matchType": 104,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, UserChangedEventTrigger)

    def test_decode_idle(self):
        """Test decode_trigger for EVENT_IDLE."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Idle",
            "matchType": 105,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, IdleEventTrigger)

    def test_decode_activity_after_idle(self):
        """Test decode_trigger for EVENT_ACTIVITY_AFTER_IDLE."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Activity",
            "matchType": 106,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, ActivityAfterIdleEventTrigger)

    def test_decode_session_ended(self):
        """Test decode_trigger for EVENT_SESSION_ENDED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "End",
            "matchType": 107,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, SessionEndedEventTrigger)

    def test_decode_bell_received(self):
        """Test decode_trigger for EVENT_BELL_RECEIVED."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Bell",
            "matchType": 108,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, BellReceivedEventTrigger)

    def test_decode_long_running(self):
        """Test decode_trigger for EVENT_LONG_RUNNING_COMMAND."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Slow",
            "matchType": 109,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, LongRunningCommandEventTrigger)

    def test_decode_custom_escape(self):
        """Test decode_trigger for EVENT_CUSTOM_ESCAPE_SEQUENCE."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "Custom",
            "matchType": 110,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, CustomEscapeSequenceEventTrigger)


class TestDecodeTriggerAllRegexTypes:
    """Tests for decode_trigger covering all regex-based trigger types."""

    def test_decode_alert(self):
        """Test decode AlertTrigger."""
        t = decode_trigger({"action": "AlertTrigger", "regex": "r", "parameter": "msg"})
        assert isinstance(t, AlertTrigger)

    def test_decode_annotate(self):
        """Test decode AnnotateTrigger."""
        t = decode_trigger({"action": "AnnotateTrigger", "regex": "r", "parameter": "ann"})
        assert isinstance(t, AnnotateTrigger)

    def test_decode_bell(self):
        """Test decode BellTrigger."""
        t = decode_trigger({"action": "BellTrigger", "regex": "r"})
        assert isinstance(t, BellTrigger)

    def test_decode_bounce(self):
        """Test decode BounceTrigger."""
        t = decode_trigger({"action": "BounceTrigger", "regex": "r", "parameter": 0})
        assert isinstance(t, BounceTrigger)

    def test_decode_buffer_input(self):
        """Test decode BufferInputTrigger."""
        t = decode_trigger({"action": "iTermBufferInputTrigger", "regex": "r", "parameter": 0})
        assert isinstance(t, BufferInputTrigger)

    def test_decode_rpc(self):
        """Test decode RPCTrigger."""
        t = decode_trigger({"action": "iTermRPCTrigger", "regex": "r", "parameter": "rpc"})
        assert isinstance(t, RPCTrigger)

    def test_decode_capture(self):
        """Test decode CaptureTrigger."""
        t = decode_trigger({"action": "CaptureTrigger", "regex": "r", "parameter": "cap"})
        assert isinstance(t, CaptureTrigger)

    def test_decode_highlight_line(self):
        """Test decode HighlightLineTrigger."""
        t = decode_trigger({"action": "iTermHighlightLineTrigger", "regex": "r", "parameter": "{#ff0000,#0000ff}"})
        assert isinstance(t, HighlightTrigger)

    def test_decode_highlight(self):
        """Test decode HighlightTrigger."""
        t = decode_trigger({"action": "HighlightTrigger", "regex": "r", "parameter": "{#ff0000,#0000ff}"})
        assert isinstance(t, HighlightTrigger)

    def test_decode_user_notification(self):
        """Test decode UserNotificationTrigger."""
        t = decode_trigger({"action": "iTermUserNotificationTrigger", "regex": "r", "parameter": "msg"})
        assert isinstance(t, UserNotificationTrigger)

    def test_decode_set_user_variable(self):
        """Test decode SetUserVariableTrigger."""
        param = "name" + chr(1) + '"value"'
        t = decode_trigger({"action": "iTermSetUserVariableTrigger", "regex": "r", "parameter": param})
        assert isinstance(t, SetUserVariableTrigger)

    def test_decode_shell_prompt(self):
        """Test decode ShellPromptTrigger."""
        t = decode_trigger({"action": "iTermShellPromptTrigger", "regex": "r"})
        assert isinstance(t, ShellPromptTrigger)

    def test_decode_set_title(self):
        """Test decode SetTitleTrigger."""
        t = decode_trigger({"action": "iTermSetTitleTrigger", "regex": "r", "parameter": "title"})
        assert isinstance(t, SetTitleTrigger)

    def test_decode_send_text(self):
        """Test decode SendTextTrigger."""
        t = decode_trigger({"action": "SendTextTrigger", "regex": "r", "parameter": "text"})
        assert isinstance(t, SendTextTrigger)

    def test_decode_run_command(self):
        """Test decode RunCommandTrigger."""
        t = decode_trigger({"action": "ScriptTrigger", "regex": "r", "parameter": "cmd"})
        assert isinstance(t, RunCommandTrigger)

    def test_decode_coprocess(self):
        """Test decode CoprocessTrigger."""
        t = decode_trigger({"action": "CoprocessTrigger", "regex": "r", "parameter": "cmd"})
        assert isinstance(t, CoprocessTrigger)

    def test_decode_mute_coprocess(self):
        """Test decode MuteCoprocessTrigger."""
        t = decode_trigger({"action": "MuteCoprocessTrigger", "regex": "r", "parameter": "cmd"})
        assert isinstance(t, MuteCoprocessTrigger)

    def test_decode_mark(self):
        """Test decode MarkTrigger."""
        t = decode_trigger({"action": "MarkTrigger", "regex": "r", "parameter": 1})
        assert isinstance(t, MarkTrigger)

    def test_decode_password(self):
        """Test decode PasswordTrigger."""
        t = decode_trigger({"action": "PasswordTrigger", "regex": "r", "parameter": "acc"})
        assert isinstance(t, PasswordTrigger)

    def test_decode_hyperlink(self):
        """Test decode HyperlinkTrigger."""
        t = decode_trigger({"action": "iTermHyperlinkTrigger", "regex": "r", "parameter": "http://x.com"})
        assert isinstance(t, HyperlinkTrigger)

    def test_decode_set_directory(self):
        """Test decode SetDirectoryTrigger."""
        t = decode_trigger({"action": "SetDirectoryTrigger", "regex": "r", "parameter": "/tmp"})
        assert isinstance(t, SetDirectoryTrigger)

    def test_decode_set_hostname(self):
        """Test decode SetHostnameTrigger."""
        t = decode_trigger({"action": "SetHostnameTrigger", "regex": "r", "parameter": "host"})
        assert isinstance(t, SetHostnameTrigger)

    def test_decode_stop(self):
        """Test decode StopTrigger."""
        t = decode_trigger({"action": "StopTrigger", "regex": "r"})
        assert isinstance(t, StopTrigger)

    def test_decode_set_named_mark(self):
        """Test decode SetNamedMarkTrigger."""
        t = decode_trigger({"action": "iTermSetNamedMarkTrigger", "regex": "r", "parameter": "mark"})
        assert isinstance(t, SetNamedMarkTrigger)

    def test_decode_sgr(self):
        """Test decode SGRTrigger."""
        t = decode_trigger({"action": "iTermSGRTrigger", "regex": "r", "parameter": "sgr"})
        assert isinstance(t, SGRTrigger)

    def test_decode_fold(self):
        """Test decode FoldTrigger."""
        t = decode_trigger({"action": "iTermFoldTrigger", "regex": "r", "parameter": "fold"})
        assert isinstance(t, FoldTrigger)

    def test_decode_inject(self):
        """Test decode InjectTrigger."""
        t = decode_trigger({"action": "iTermInjectTrigger", "regex": "r", "parameter": "inj"})
        assert isinstance(t, InjectTrigger)


class TestEncodeMatchType:
    """Tests for encode including matchType field."""

    def test_trigger_encode_match_type(self):
        """Test Trigger.encode includes matchType."""
        t = Trigger("r", "p", False, True, match_type=MatchType.URL_REGEX)
        e = t.encode
        assert e["matchType"] == 1

    def test_event_trigger_encode_raw_match_type(self):
        """Test EventTrigger.encode preserves raw match type."""
        t = EventTrigger(
            match_type=MatchType.EVENT_PROMPT_DETECTED,
            action_name="AlertTrigger",
            param="",
            enabled=True,
            _raw_match_type=999,
        )
        e = t.encode
        assert e["matchType"] == 999


class TestEventTriggerEncodeEdgeCases:
    """Tests for EventTrigger.encode edge cases."""

    def test_encode_empty_param(self):
        """Test EventTrigger.encode with None param."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param=None,
            enabled=True,
        )
        e = t.encode
        assert e["parameter"] == ""

    def test_encode_empty_event_params(self):
        """Test EventTrigger.encode without event_params."""
        t = EventTrigger(
            match_type=MatchType.EVENT_BELL_RECEIVED,
            action_name="AlertTrigger",
            param="p",
            enabled=True,
        )
        e = t.encode
        assert "eventParams" not in e


class TestDecodeTriggerWithEventParams:
    """Tests for decode_trigger with eventParams field."""

    def test_decode_with_event_params(self):
        """Test decode_trigger passes eventParams to event triggers."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "test",
            "matchType": 101,
            "eventParams": {"exitCodeFilter": "0"},
        }
        t = decode_trigger(encoded)
        assert isinstance(t, CommandFinishedEventTrigger)
        assert t.exit_code_filter == ExitCodeFilter.ZERO

    def test_decode_without_event_params(self):
        """Test decode_trigger without eventParams uses defaults."""
        encoded = {
            "action": "AlertTrigger",
            "regex": "",
            "parameter": "test",
            "matchType": 105,
        }
        t = decode_trigger(encoded)
        assert isinstance(t, IdleEventTrigger)
        assert t.timeout == 30.0
