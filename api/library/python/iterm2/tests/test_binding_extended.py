import pytest
import iterm2.binding
import iterm2.keyboard
import iterm2.mainmenu
import iterm2


class TestBindingAction:
    def test_enum_values(self):
        assert iterm2.binding.BindingAction.NEXT_SESSION.value == 0
        assert iterm2.binding.BindingAction.NEXT_WINDOW.value == 1
        assert iterm2.binding.BindingAction.PREVIOUS_SESSION.value == 2
        assert iterm2.binding.BindingAction.PREVIOUS_WINDOW.value == 3
        assert iterm2.binding.BindingAction.SCROLL_END.value == 4
        assert iterm2.binding.BindingAction.SCROLL_HOME.value == 5
        assert iterm2.binding.BindingAction.ESCAPE_SEQUENCE.value == 10
        assert iterm2.binding.BindingAction.HEX_CODE.value == 11
        assert iterm2.binding.BindingAction.TEXT.value == 12
        assert iterm2.binding.BindingAction.IGNORE.value == 13
        assert iterm2.binding.BindingAction.PASTE_SPECIAL.value == 41
        assert iterm2.binding.BindingAction.SEND_SNIPPET.value == 63

    def test_all_actions_have_values(self):
        for action in iterm2.binding.BindingAction:
            assert isinstance(action.value, int)


class TestMoveSelectionUnit:
    def test_enum_values(self):
        assert iterm2.binding.MoveSelectionUnit.CHAR.value == 0
        assert iterm2.binding.MoveSelectionUnit.WORD.value == 1
        assert iterm2.binding.MoveSelectionUnit.LINE.value == 2
        assert iterm2.binding.MoveSelectionUnit.MARK.value == 3
        assert iterm2.binding.MoveSelectionUnit.BIG_WORD.value == 4

    def test_encode(self):
        for unit in iterm2.binding.MoveSelectionUnit:
            assert unit._encode() == unit.value

    def test_constructor(self):
        unit = iterm2.binding.MoveSelectionUnitConstructor("2")
        assert unit == iterm2.binding.MoveSelectionUnit.LINE


class TestSnippetIdentifier:
    def test_from_string(self):
        sid = iterm2.binding.SnippetIdentifier("My Snippet")
        assert sid._encode() == "My Snippet"

    def test_from_dict(self):
        sid = iterm2.binding.SnippetIdentifier({"guid": "abc123"})
        assert sid._encode() == {"guid": "abc123"}


class TestGetConstructor:
    def test_no_param_actions(self):
        for action in [
            iterm2.binding.BindingAction.NEXT_SESSION,
            iterm2.binding.BindingAction.NEXT_WINDOW,
            iterm2.binding.BindingAction.PREVIOUS_SESSION,
            iterm2.binding.BindingAction.PREVIOUS_WINDOW,
            iterm2.binding.BindingAction.SCROLL_END,
            iterm2.binding.BindingAction.SCROLL_HOME,
            iterm2.binding.BindingAction.IGNORE,
            iterm2.binding.BindingAction.UNDO,
        ]:
            assert iterm2.binding.get_constructor(action) == iterm2.binding.NoParamConstructor

    def test_string_actions(self):
        for action in [
            iterm2.binding.BindingAction.ESCAPE_SEQUENCE,
            iterm2.binding.BindingAction.HEX_CODE,
            iterm2.binding.BindingAction.TEXT,
        ]:
            assert iterm2.binding.get_constructor(action) == str

    def test_menu_item_action(self):
        assert iterm2.binding.get_constructor(
            iterm2.binding.BindingAction.SELECT_MENU_ITEM) == iterm2.binding.MenuItemIdentifierConstructor

    def test_paste_special_action(self):
        assert iterm2.binding.get_constructor(
            iterm2.binding.BindingAction.PASTE_SPECIAL) == iterm2.binding.PasteConfigurationConstructor

    def test_move_selection_action(self):
        assert iterm2.binding.get_constructor(
            iterm2.binding.BindingAction.MOVE_END_OF_SELECTION_LEFT) == iterm2.binding.MoveSelectionUnitConstructor

    def test_snippet_action(self):
        assert iterm2.binding.get_constructor(
            iterm2.binding.BindingAction.SEND_SNIPPET) == iterm2.binding.SnippetIdentifier


class TestNoParamConstructor:
    def test_returns_empty_string(self):
        assert iterm2.binding.NoParamConstructor("anything") == ""


class TestMenuItemIdentifierConstructor:
    def test_title_only(self):
        result = iterm2.binding.MenuItemIdentifierConstructor("My Menu")
        assert isinstance(result, iterm2.mainmenu.MenuItemIdentifier)
        assert result.title == "My Menu"
        assert result.identifier is None

    def test_title_and_identifier(self):
        result = iterm2.binding.MenuItemIdentifierConstructor("My Menu\ncom.example.action")
        assert result.title == "My Menu"
        assert result.identifier == "com.example.action"


class TestPasteConfigurationConstructor:
    def test_none_param(self):
        result = iterm2.binding.PasteConfigurationConstructor(None)
        assert result.base64 is False
        assert result.wait_for_prompts is False
        assert result.tab_transform == iterm2.binding.PasteConfiguration.TabTransform.NONE
        assert result.tab_stop_size is False
        assert result.delay == 0.01
        assert result.chunk_size == 1024

    def test_json_param(self):
        import json
        param = json.dumps({
            'Base64': True,
            'WaitForPrompts': True,
            'TabTransform': 1,
            'TabStopSize': 4,
            'Delay': 0.1,
            'ChunkSize': 2048,
            'ConvertNewlines': True,
            'RemoveNewlines': True,
            'ConvertUnicodePunctuation': True,
            'EscapeForShell': True,
            'RemoveControls': True,
            'BracketAllowed': False,
            'UseRegexSubstitution': False,
            'Regex': '',
            'Substitution': ''
        })
        result = iterm2.binding.PasteConfigurationConstructor(param)
        assert result.base64 is True
        assert result.wait_for_prompts is True
        assert result.tab_transform == iterm2.binding.PasteConfiguration.TabTransform.CONVERT_TO_SPACES
        assert result.tab_stop_size == 4
        assert result.delay == 0.1
        assert result.chunk_size == 2048


class TestKeyBinding:
    def test_basic_binding(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=None,
            action=iterm2.binding.BindingAction.IGNORE,
            param="",
            version=None,
            label=None)
        assert kb.character == 0x41
        assert kb.keycode is None
        assert kb.action == iterm2.binding.BindingAction.IGNORE
        assert kb.modifiers == []

    def test_binding_with_modifiers(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[iterm2.keyboard.Modifier.COMMAND],
            keycode=None,
            action=iterm2.binding.BindingAction.IGNORE,
            param="",
            version=None,
            label=None)
        assert iterm2.keyboard.Modifier.COMMAND in kb.modifiers

    def test_binding_with_keycode(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=iterm2.keyboard.Keycode.ANSI_B,
            action=iterm2.binding.BindingAction.IGNORE,
            param="",
            version=None,
            label=None)
        assert kb.keycode == iterm2.keyboard.Keycode.ANSI_B

    def test_binding_with_version_and_label(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=None,
            action=iterm2.binding.BindingAction.TEXT,
            param="hello",
            version=1,
            label="My Label")
        value = kb._value
        assert value['Version'] == 1
        assert value['Label'] == "My Label"

    def test_key_no_keycode(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=None,
            action=iterm2.binding.BindingAction.IGNORE,
            param="",
            version=None,
            label=None)
        assert kb.key == "0x41-0x0"

    def test_key_with_keycode(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=iterm2.keyboard.Keycode.ANSI_B,
            action=iterm2.binding.BindingAction.IGNORE,
            param="",
            version=None,
            label=None)
        assert kb.key == "0x41-0x0-0xb"

    def test_value_encoding(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=None,
            action=iterm2.binding.BindingAction.TEXT,
            param="hello",
            version=None,
            label=None)
        value = kb._value
        assert value['Action'] == iterm2.binding.BindingAction.TEXT.value
        assert value['Text'] == "hello"
        assert 'Version' not in value
        assert 'Label' not in value

    def test_encode_property(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41,
            modifiers=[],
            keycode=None,
            action=iterm2.binding.BindingAction.IGNORE,
            param="",
            version=None,
            label=None)
        assert kb.encode == kb._value

    def test_equality(self):
        kb1 = iterm2.binding.KeyBinding(
            character=0x41, modifiers=[], keycode=None,
            action=iterm2.binding.BindingAction.IGNORE, param="",
            version=None, label=None)
        kb2 = iterm2.binding.KeyBinding(
            character=0x41, modifiers=[], keycode=None,
            action=iterm2.binding.BindingAction.IGNORE, param="",
            version=None, label=None)
        assert kb1 == kb2

    def test_inequality(self):
        kb1 = iterm2.binding.KeyBinding(
            character=0x41, modifiers=[], keycode=None,
            action=iterm2.binding.BindingAction.IGNORE, param="",
            version=None, label=None)
        kb2 = iterm2.binding.KeyBinding(
            character=0x42, modifiers=[], keycode=None,
            action=iterm2.binding.BindingAction.IGNORE, param="",
            version=None, label=None)
        assert kb1 != kb2

    def test_repr(self):
        kb = iterm2.binding.KeyBinding(
            character=0x41, modifiers=[], keycode=None,
            action=iterm2.binding.BindingAction.IGNORE, param="",
            version=None, label=None)
        result = repr(kb)
        assert "KeyBinding" in result


class TestDecodeKeyBinding:
    def test_decode_ignore_binding(self):
        key = "0x41-0x0"
        entry = {'Action': 13, 'Text': ''}
        kb = iterm2.binding.decode_key_binding(key, entry)
        assert kb.character == 0x41
        assert kb.action == iterm2.binding.BindingAction.IGNORE

    def test_decode_with_keycode(self):
        key = "0x41-0x0-0x0b"
        entry = {'Action': 13, 'Text': ''}
        kb = iterm2.binding.decode_key_binding(key, entry)
        assert kb.keycode == iterm2.keyboard.Keycode.ANSI_B

    def test_decode_text_binding(self):
        key = "0x41-0x0"
        entry = {'Action': 12, 'Text': 'hello'}
        kb = iterm2.binding.decode_key_binding(key, entry)
        assert kb.action == iterm2.binding.BindingAction.TEXT
        assert kb.param == 'hello'

    def test_decode_with_version_and_label(self):
        key = "0x41-0x0"
        entry = {'Action': 12, 'Text': 'hello', 'Version': 1, 'Label': 'My Label'}
        kb = iterm2.binding.decode_key_binding(key, entry)
        value = kb._value
        assert value['Version'] == 1
        assert value['Label'] == 'My Label'


class TestGlobalKeyMapConstant:
    def test_constant_value(self):
        assert iterm2.binding.GLOBAL_KEY_MAP_USER_DEFAULTS_KEY == 'GlobalKeyMap'
