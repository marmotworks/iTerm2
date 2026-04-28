import pytest
import json
import iterm2.binding
import iterm2.mainmenu


class TestNoParamConstructor:
    def test_returns_empty_string(self):
        result = iterm2.binding.NoParamConstructor("anything")
        assert result == ""


class TestMenuItemIdentifierConstructor:
    def test_title_only(self):
        result = iterm2.binding.MenuItemIdentifierConstructor("My Title")
        assert isinstance(result, iterm2.mainmenu.MenuItemIdentifier)
        assert result.title == "My Title"
        assert result.identifier is None

    def test_title_and_identifier(self):
        result = iterm2.binding.MenuItemIdentifierConstructor("My Title\ncom.example.id")
        assert isinstance(result, iterm2.mainmenu.MenuItemIdentifier)
        assert result.title == "My Title"
        assert result.identifier == "com.example.id"


class TestPasteConfigurationConstructor:
    def test_none_param_returns_defaults(self):
        result = iterm2.binding.PasteConfigurationConstructor(None)
        assert result.base64 is False
        assert result.wait_for_prompts is False
        assert result.tab_transform == iterm2.binding.PasteConfiguration.TabTransform.NONE
        assert result.tab_stop_size is False
        assert result.delay == 0.01
        assert result.chunk_size == 1024
        assert result.convert_newlines is False
        assert result.remove_newlines is False
        assert result.convert_unicode_punctuation is False
        assert result.escape_for_shell is False
        assert result.remove_controls is False
        assert result.bracket_allowed is True
        assert result.use_regex_substitution is False
        assert result.regex == ""
        assert result.substitution == ""

    def test_json_param(self):
        param = json.dumps({
            "Base64": True,
            "WaitForPrompts": True,
            "TabTransform": 1,
            "TabStopSize": 4,
            "Delay": 0.1,
            "ChunkSize": 2048,
            "ConvertNewlines": True,
            "RemoveNewlines": True,
            "ConvertUnicodePunctuation": True,
            "EscapeForShell": True,
            "RemoveControls": True,
            "BracketAllowed": False,
            "UseRegexSubstitution": True,
            "Regex": "foo",
            "Substitution": "bar"
        })
        result = iterm2.binding.PasteConfigurationConstructor(param)
        assert result.base64 is True
        assert result.wait_for_prompts is True
        assert result.tab_transform == iterm2.binding.PasteConfiguration.TabTransform.CONVERT_TO_SPACES
        assert result.tab_stop_size == 4
        assert result.delay == 0.1
        assert result.chunk_size == 2048
        assert result.convert_newlines is True
        assert result.remove_newlines is True
        assert result.convert_unicode_punctuation is True
        assert result.escape_for_shell is True
        assert result.remove_controls is True
        assert result.bracket_allowed is False
        assert result.use_regex_substitution is True
        assert result.regex == "foo"
        assert result.substitution == "bar"


class TestPasteConfiguration:
    def test_tab_transform_enum(self):
        assert iterm2.binding.PasteConfiguration.TabTransform.NONE.value == 0
        assert iterm2.binding.PasteConfiguration.TabTransform.CONVERT_TO_SPACES.value == 1
        assert iterm2.binding.PasteConfiguration.TabTransform.ESCAPE_WITH_CONTROL_V.value == 2

    def test_init_all_fields(self):
        config = iterm2.binding.PasteConfiguration(
            base64=True,
            wait_for_prompts=False,
            tab_transform=iterm2.binding.PasteConfiguration.TabTransform.NONE,
            tab_stop_size=4,
            delay=0.05,
            chunk_size=512,
            convert_newlines=True,
            remove_newlines=False,
            convert_unicode_punctuation=False,
            escape_for_shell=False,
            remove_controls=False,
            bracket_allowed=True,
            use_regex_substitution=False,
            regex="",
            substitution=""
        )
        assert config.base64 is True
        assert config.wait_for_prompts is False
        assert config.tab_transform == iterm2.binding.PasteConfiguration.TabTransform.NONE
        assert config.tab_stop_size == 4
        assert config.delay == 0.05
        assert config.chunk_size == 512
        assert config.convert_newlines is True
        assert config.remove_newlines is False
        assert config.convert_unicode_punctuation is False
        assert config.escape_for_shell is False
        assert config.remove_controls is False
        assert config.bracket_allowed is True
        assert config.use_regex_substitution is False
        assert config.regex == ""
        assert config.substitution == ""

    def test_encode_roundtrip(self):
        config = iterm2.binding.PasteConfiguration(
            base64=True,
            wait_for_prompts=True,
            tab_transform=iterm2.binding.PasteConfiguration.TabTransform.CONVERT_TO_SPACES,
            tab_stop_size=8,
            delay=0.5,
            chunk_size=4096,
            convert_newlines=False,
            remove_newlines=True,
            convert_unicode_punctuation=True,
            escape_for_shell=True,
            remove_controls=True,
            bracket_allowed=False,
            use_regex_substitution=True,
            regex="test",
            substitution="replaced"
        )
        j = config._encode()
        parsed = json.loads(j)
        assert parsed["Base64"] is True
        assert parsed["WaitForPrompts"] is True
        assert parsed["TabTransform"] == 1
        assert parsed["TabStopSize"] == 8
        assert parsed["Delay"] == 0.5
        assert parsed["ChunkSize"] == 4096
        assert parsed["ConvertNewlines"] is False
        assert parsed["RemoveNewlines"] is True
        assert parsed["ConvertUnicodePunctuation"] is True
        assert parsed["EscapeForShell"] is True
        assert parsed["RemoveControls"] is True
        assert parsed["BracketAllowed"] is False
        assert parsed["UseRegexSubstitution"] is True
        assert parsed["Regex"] == "test"
        assert parsed["Substitution"] == "replaced"

    def test_encode_roundtrip_via_constructor(self):
        original = iterm2.binding.PasteConfiguration(
            base64=True,
            wait_for_prompts=False,
            tab_transform=iterm2.binding.PasteConfiguration.TabTransform.ESCAPE_WITH_CONTROL_V,
            tab_stop_size=2,
            delay=0.02,
            chunk_size=256,
            convert_newlines=True,
            remove_newlines=False,
            convert_unicode_punctuation=False,
            escape_for_shell=False,
            remove_controls=False,
            bracket_allowed=True,
            use_regex_substitution=False,
            regex="",
            substitution=""
        )
        reconstructed = iterm2.binding.PasteConfigurationConstructor(original._encode())
        assert reconstructed.base64 == original.base64
        assert reconstructed.tab_transform == original.tab_transform
        assert reconstructed.tab_stop_size == original.tab_stop_size
        assert reconstructed.delay == original.delay
        assert reconstructed.chunk_size == original.chunk_size
