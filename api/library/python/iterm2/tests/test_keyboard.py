import pytest
import iterm2.keyboard
import iterm2


class TestModifier:
    def test_enum_values(self):
        for mod in iterm2.keyboard.Modifier:
            assert mod.value is not None

    def test_from_cocoa_control(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(1 << 18)
        assert iterm2.keyboard.Modifier.CONTROL in mods

    def test_from_cocoa_option(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(1 << 19)
        assert iterm2.keyboard.Modifier.OPTION in mods

    def test_from_cocoa_command(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(1 << 20)
        assert iterm2.keyboard.Modifier.COMMAND in mods

    def test_from_cocoa_shift(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(1 << 17)
        assert iterm2.keyboard.Modifier.SHIFT in mods

    def test_from_cocoa_function(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(1 << 23)
        assert iterm2.keyboard.Modifier.FUNCTION in mods

    def test_from_cocoa_numpad(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(1 << 21)
        assert iterm2.keyboard.Modifier.NUMPAD in mods

    def test_from_cocoa_combined(self):
        mods = iterm2.keyboard.Modifier.from_cocoa((1 << 18) | (1 << 17))
        assert iterm2.keyboard.Modifier.CONTROL in mods
        assert iterm2.keyboard.Modifier.SHIFT in mods
        assert len(mods) == 2

    def test_from_cocoa_none(self):
        mods = iterm2.keyboard.Modifier.from_cocoa(0)
        assert mods == []

    def test_to_cocoa_control(self):
        assert iterm2.keyboard.Modifier.CONTROL.to_cocoa() == 1 << 18

    def test_to_cocoa_option(self):
        assert iterm2.keyboard.Modifier.OPTION.to_cocoa() == 1 << 19

    def test_to_cocoa_command(self):
        assert iterm2.keyboard.Modifier.COMMAND.to_cocoa() == 1 << 20

    def test_to_cocoa_shift(self):
        assert iterm2.keyboard.Modifier.SHIFT.to_cocoa() == 1 << 17

    def test_to_cocoa_function(self):
        assert iterm2.keyboard.Modifier.FUNCTION.to_cocoa() == 1 << 23

    def test_to_cocoa_numpad(self):
        assert iterm2.keyboard.Modifier.NUMPAD.to_cocoa() == 1 << 21


class TestKeycode:
    def test_common_keys(self):
        assert iterm2.keyboard.Keycode.ANSI_A.value == 0x00
        assert iterm2.keyboard.Keycode.RETURN.value == 0x24
        assert iterm2.keyboard.Keycode.TAB.value == 0x30
        assert iterm2.keyboard.Keycode.SPACE.value == 0x31
        assert iterm2.keyboard.Keycode.ESCAPE.value == 0x35
        assert iterm2.keyboard.Keycode.DELETE.value == 0x33

    def test_arrow_keys(self):
        assert iterm2.keyboard.Keycode.LEFT_ARROW.value == 0x7B
        assert iterm2.keyboard.Keycode.RIGHT_ARROW.value == 0x7C
        assert iterm2.keyboard.Keycode.UP_ARROW.value == 0x7E
        assert iterm2.keyboard.Keycode.DOWN_ARROW.value == 0x7D

    def test_function_keys(self):
        assert iterm2.keyboard.Keycode.F1.value == 0x7A
        assert iterm2.keyboard.Keycode.F12.value == 0x6F

    def test_navigation_keys(self):
        assert iterm2.keyboard.Keycode.HOME.value == 0x73
        assert iterm2.keyboard.Keycode.END.value == 0x77
        assert iterm2.keyboard.Keycode.PAGE_UP.value == 0x74
        assert iterm2.keyboard.Keycode.PAGE_DOWN.value == 0x79


class TestKeystrokePattern:
    def test_default_empty(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        assert pattern.required_modifiers == []
        assert pattern.forbidden_modifiers == []
        assert pattern.keycodes == []
        assert pattern.characters == []
        assert pattern.characters_ignoring_modifiers == []

    def test_set_required_modifiers(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.required_modifiers = [iterm2.keyboard.Modifier.CONTROL]
        assert pattern.required_modifiers == [iterm2.keyboard.Modifier.CONTROL]

    def test_set_forbidden_modifiers(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.forbidden_modifiers = [iterm2.keyboard.Modifier.SHIFT]
        assert pattern.forbidden_modifiers == [iterm2.keyboard.Modifier.SHIFT]

    def test_set_keycodes(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.keycodes = [iterm2.keyboard.Keycode.ANSI_A]
        assert pattern.keycodes == [iterm2.keyboard.Keycode.ANSI_A]

    def test_set_characters(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.characters = ["a", "b"]
        assert pattern.characters == ["a", "b"]

    def test_set_characters_ignoring_modifiers(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.characters_ignoring_modifiers = ["a"]
        assert pattern.characters_ignoring_modifiers == ["a"]

    def test_to_proto(self):
        pattern = iterm2.keyboard.KeystrokePattern()
        pattern.required_modifiers = [iterm2.keyboard.Modifier.CONTROL]
        pattern.keycodes = [iterm2.keyboard.Keycode.ANSI_A]
        pattern.characters = ["a"]
        proto = pattern.to_proto()
        assert proto.required_modifiers[0] == iterm2.keyboard.Modifier.CONTROL.value
        assert proto.keycodes[0] == iterm2.keyboard.Keycode.ANSI_A.value
        assert proto.characters[0] == "a"


class TestKeystrokeAction:
    def test_enum_values(self):
        assert iterm2.keyboard.Keystroke.Action.NA.value == 0
        assert iterm2.keyboard.Keystroke.Action.KEY_DOWN.value == 1
        assert iterm2.keyboard.Keystroke.Action.KEY_UP.value == 2
        assert iterm2.keyboard.Keystroke.Action.FLAGS_CHANGED.value == 3
