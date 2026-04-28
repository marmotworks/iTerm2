import pytest
import json
import iterm2


def _make_profile_prop(key, value):
    """Helper to create a ProfileProperty protobuf message."""
    prop = iterm2.api_pb2.ProfileProperty()
    prop.key = key
    prop.json_value = json.dumps(value)
    return prop


def _make_profile(props_dict):
    """Helper to create a Profile from a dict of key -> python value."""
    prop_list = []
    for key, value in props_dict.items():
        prop_list.append(_make_profile_prop(key, value))
    return iterm2.Profile(None, None, prop_list)


class TestLocalWriteOnlyProfileInit:
    def test_empty_init(self):
        prof = iterm2.LocalWriteOnlyProfile()
        assert prof.values == {}

    def test_init_with_dict(self):
        prof = iterm2.LocalWriteOnlyProfile({"foo": "bar", "baz": 42})
        assert prof.values["foo"] == json.dumps("bar")
        assert prof.values["baz"] == json.dumps(42)

    def test_values_returns_internal_dict(self):
        prof = iterm2.LocalWriteOnlyProfile({"a": 1})
        vals = prof.values
        assert vals is not None
        assert "a" in vals


class TestLocalWriteOnlyProfileSimpleSet:
    def test_simple_set_basic(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof._simple_set("Key", "value")
        assert prof.values["Key"] == json.dumps("value")

    def test_simple_set_none_key(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof._simple_set(None, None)
        assert prof.values[None] is None

    def test_simple_set_with_to_json_object(self):
        prof = iterm2.LocalWriteOnlyProfile()
        mode = iterm2.profile.BackgroundImageMode.STRETCH
        prof._simple_set("Mode", mode)
        assert prof.values["Mode"] == mode.toJSON()

    def test_simple_set_int(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof._simple_set("Count", 99)
        assert prof.values["Count"] == json.dumps(99)

    def test_simple_set_bool(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof._simple_set("Flag", True)
        assert prof.values["Flag"] == json.dumps(True)

    def test_simple_set_float(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof._simple_set("Ratio", 1.5)
        assert prof.values["Ratio"] == json.dumps(1.5)


class TestLocalWriteOnlyProfileColorSet:
    def test_color_set_none(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof._color_set("Color", None)
        assert prof.values["Color"] == "null"

    def test_color_set_valid(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 128, 64, 200)
        prof._color_set("Color", color)
        assert prof.values["Color"] == json.dumps(color.get_dict())


class TestLocalWriteOnlyProfileSetters:
    def test_set_title_components(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_title_components([
            iterm2.TitleComponents.SESSION_NAME,
            iterm2.TitleComponents.JOB,
        ])
        assert prof.values["Title Components"] == json.dumps((1 << 0) + (1 << 1))

    def test_set_title_components_custom(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_title_components([iterm2.TitleComponents.CUSTOM])
        assert prof.values["Title Components"] == json.dumps(1 << 4)

    def test_set_title_function(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_title_function("My Title", "com.example.title")
        assert prof.values["Title Function"] == json.dumps(["My Title", "com.example.title"])

    def test_set_use_separate_colors_for_light_and_dark_mode(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_separate_colors_for_light_and_dark_mode(True)
        assert prof.values["Use Separate Colors for Light and Dark Mode"] == json.dumps(True)

    def test_set_foreground_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(100, 150, 200)
        prof.set_foreground_color(color)
        assert prof.values["Foreground Color"] == json.dumps(color.get_dict())

    def test_set_foreground_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(50, 100, 150)
        prof.set_foreground_color_light(color)
        assert prof.values["Foreground Color (Light)"] == json.dumps(color.get_dict())

    def test_set_foreground_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(200, 100, 50)
        prof.set_foreground_color_dark(color)
        assert prof.values["Foreground Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_background_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 0, 0)
        prof.set_background_color(color)
        assert prof.values["Background Color"] == json.dumps(color.get_dict())

    def test_set_background_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 255, 255)
        prof.set_background_color_light(color)
        assert prof.values["Background Color (Light)"] == json.dumps(color.get_dict())

    def test_set_background_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(30, 30, 30)
        prof.set_background_color_dark(color)
        assert prof.values["Background Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_bold_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 255, 255)
        prof.set_bold_color(color)
        assert prof.values["Bold Color"] == json.dumps(color.get_dict())

    def test_set_bold_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(200, 200, 200)
        prof.set_bold_color_light(color)
        assert prof.values["Bold Color (Light)"] == json.dumps(color.get_dict())

    def test_set_bold_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(100, 100, 100)
        prof.set_bold_color_dark(color)
        assert prof.values["Bold Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_use_bright_bold(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bright_bold(True)
        assert prof.values["Use Bright Bold"] == json.dumps(True)

    def test_set_use_bright_bold_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bright_bold_light(False)
        assert prof.values["Use Bright Bold (Light)"] == json.dumps(False)

    def test_set_use_bright_bold_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bright_bold_dark(True)
        assert prof.values["Use Bright Bold (Dark)"] == json.dumps(True)

    def test_set_use_bold_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bold_color(True)
        assert prof.values["Use Bright Bold"] == json.dumps(True)

    def test_set_use_bold_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bold_color_light(False)
        assert prof.values["Use Bright Bold (Light)"] == json.dumps(False)

    def test_set_use_bold_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bold_color_dark(True)
        assert prof.values["Use Bright Bold (Dark)"] == json.dumps(True)

    def test_set_brighten_bold_text(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_brighten_bold_text(True)
        assert prof.values["Brighten Bold Text"] == json.dumps(True)

    def test_set_brighten_bold_text_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_brighten_bold_text_light(False)
        assert prof.values["Brighten Bold Text (Light)"] == json.dumps(False)

    def test_set_brighten_bold_text_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_brighten_bold_text_dark(True)
        assert prof.values["Brighten Bold Text (Dark)"] == json.dumps(True)

    def test_set_link_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 0, 255)
        prof.set_link_color(color)
        assert prof.values["Link Color"] == json.dumps(color.get_dict())

    def test_set_link_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 100, 255)
        prof.set_link_color_light(color)
        assert prof.values["Link Color (Light)"] == json.dumps(color.get_dict())

    def test_set_link_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 200, 255)
        prof.set_link_color_dark(color)
        assert prof.values["Link Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_selection_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(100, 100, 200)
        prof.set_selection_color(color)
        assert prof.values["Selection Color"] == json.dumps(color.get_dict())

    def test_set_selection_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(150, 150, 220)
        prof.set_selection_color_light(color)
        assert prof.values["Selection Color (Light)"] == json.dumps(color.get_dict())

    def test_set_selection_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(50, 50, 100)
        prof.set_selection_color_dark(color)
        assert prof.values["Selection Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_selected_text_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 255, 255)
        prof.set_selected_text_color(color)
        assert prof.values["Selected Text Color"] == json.dumps(color.get_dict())

    def test_set_selected_text_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 0, 0)
        prof.set_selected_text_color_light(color)
        assert prof.values["Selected Text Color (Light)"] == json.dumps(color.get_dict())

    def test_set_selected_text_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 255, 255)
        prof.set_selected_text_color_dark(color)
        assert prof.values["Selected Text Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_name(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_name("My Profile")
        assert prof.values["Name"] == json.dumps("My Profile")

    def test_set_badge_text(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_badge_text("badge")
        assert prof.values["Badge Text"] == json.dumps("badge")

    def test_set_subtitle(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_subtitle("sub")
        assert prof.values["Subtitle"] == json.dumps("sub")

    def test_set_answerback_string(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_answerback_string("VT100")
        assert prof.values["Answerback String"] == json.dumps("VT100")

    def test_set_blinking_cursor(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_blinking_cursor(True)
        assert prof.values["Blinking Cursor"] == json.dumps(True)

    def test_set_cursor_shadow(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_cursor_shadow(False)
        assert prof.values["Cursor Shadow"] == json.dumps(False)

    def test_set_use_bold_font(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_bold_font(True)
        assert prof.values["Use Bold Font"] == json.dumps(True)

    def test_set_ascii_ligatures(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_ascii_ligatures(True)
        assert prof.values["ASCII Ligatures"] == json.dumps(True)

    def test_set_non_ascii_ligatures(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_non_ascii_ligatures(False)
        assert prof.values["Non-ASCII Ligatures"] == json.dumps(False)

    def test_set_blink_allowed(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_blink_allowed(True)
        assert prof.values["Blink Allowed"] == json.dumps(True)

    def test_set_use_italic_font(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_italic_font(True)
        assert prof.values["Use Italic Font"] == json.dumps(True)

    def test_set_ambiguous_double_width(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_ambiguous_double_width(True)
        assert prof.values["Ambiguous Double Width"] == json.dumps(True)

    def test_set_horizontal_spacing(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_horizontal_spacing(1.2)
        assert prof.values["Horizontal Spacing"] == json.dumps(1.2)

    def test_set_vertical_spacing(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_vertical_spacing(1.5)
        assert prof.values["Vertical Spacing"] == json.dumps(1.5)

    def test_set_use_non_ascii_font(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_non_ascii_font(True)
        assert prof.values["Use Non-ASCII Font"] == json.dumps(True)

    def test_set_transparency(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_transparency(0.5)
        assert prof.values["Transparency"] == json.dumps(0.5)

    def test_set_cursor_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 0, 0)
        prof.set_cursor_color(color)
        assert prof.values["Cursor Color"] == json.dumps(color.get_dict())

    def test_set_cursor_text_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 255, 0)
        prof.set_cursor_text_color(color)
        assert prof.values["Cursor Text Color"] == json.dumps(color.get_dict())

    def test_set_cursor_type(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_cursor_type(iterm2.CursorType.CURSOR_TYPE_BOX)
        assert prof.values["Cursor Type"] == json.dumps(2)

    def test_set_allow_change_cursor_blink(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_allow_change_cursor_blink(True)
        assert prof.values["Allow Change Cursor Blink"] == json.dumps(True)

    def test_set_thin_strokes(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_thin_strokes(iterm2.ThinStrokes.THIN_STROKES_SETTING_ALWAYS)
        assert prof.values["Thin Strokes"] == json.dumps(3)

    def test_set_badge_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 0, 0)
        prof.set_badge_color(color)
        assert prof.values["Badge Color"] == json.dumps(color.get_dict())

    def test_set_use_cursor_guide(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_cursor_guide(True)
        assert prof.values["Use Cursor Guide"] == json.dumps(True)

    def test_set_cursor_guide_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 255, 0, 128)
        prof.set_cursor_guide_color(color)
        assert prof.values["Cursor Guide Color"] == json.dumps(color.get_dict())


class TestProfileConstants:
    def test_use_custom_command_enabled(self):
        assert iterm2.Profile.USE_CUSTOM_COMMAND_ENABLED == "Yes"

    def test_use_custom_command_disabled(self):
        assert iterm2.Profile.USE_CUSTOM_COMMAND_DISABLED == "No"


class TestProfileGetters:
    def test_guid(self):
        prof = _make_profile({"Guid": "test-guid-123"})
        assert prof.guid == "test-guid-123"

    def test_guid_none(self):
        prof = _make_profile({})
        assert prof.guid is None

    def test_original_guid(self):
        prof = _make_profile({"Original Guid": "orig-guid"})
        assert prof.original_guid == "orig-guid"

    def test_original_guid_none(self):
        prof = _make_profile({})
        assert prof.original_guid is None

    def test_dynamic_profile_parent_name(self):
        prof = _make_profile({"Dynamic Profile Parent Name": "ParentProfile"})
        assert prof.dynamic_profile_parent_name == "ParentProfile"

    def test_dynamic_profile_file_name(self):
        prof = _make_profile({"Dynamic Profile Filename": "/path/to/profile"})
        assert prof.dynamic_profile_file_name == "/path/to/profile"

    def test_all_properties(self):
        props = {"Guid": "g1", "Name": "Test", "Foo": "bar"}
        prof = _make_profile(props)
        all_props = prof.all_properties
        assert all_props["Guid"] == "g1"
        assert all_props["Name"] == "Test"
        assert all_props["Foo"] == "bar"
        assert all_props is not prof._Profile__props

    def test_use_separate_colors_for_light_and_dark_mode(self):
        prof = _make_profile({"Use Separate Colors for Light and Dark Mode": True})
        assert prof.use_separate_colors_for_light_and_dark_mode is True

    def test_use_separate_colors_for_light_and_dark_mode_false(self):
        prof = _make_profile({"Use Separate Colors for Light and Dark Mode": False})
        assert prof.use_separate_colors_for_light_and_dark_mode is False

    def test_use_separate_colors_for_light_and_dark_mode_none(self):
        prof = _make_profile({})
        assert prof.use_separate_colors_for_light_and_dark_mode is None


class TestProfileColorGetters:
    def test_foreground_color(self):
        color_dict = {
            "Red Component": 1.0,
            "Green Component": 0.5,
            "Blue Component": 0.25,
            "Alpha Component": 1.0,
            "Color Space": "Calibrated",
        }
        prof = _make_profile({"Foreground Color": color_dict})
        fg = prof.foreground_color
        assert fg is not None
        assert fg.red == 255
        assert fg.green == 127.5
        assert fg.blue == 63.75

    def test_foreground_color_none(self):
        prof = _make_profile({})
        assert prof.foreground_color is None

    def test_foreground_color_invalid(self):
        prof = _make_profile({"Foreground Color": "not a dict"})
        with pytest.raises(TypeError):
            _ = prof.foreground_color

    def test_background_color(self):
        color_dict = {
            "Red Component": 0.0,
            "Green Component": 0.0,
            "Blue Component": 0.0,
            "Alpha Component": 1.0,
        }
        prof = _make_profile({"Background Color": color_dict})
        bg = prof.background_color
        assert bg is not None
        assert bg.red == 0
        assert bg.blue == 0

    def test_bold_color(self):
        color_dict = {
            "Red Component": 0.5,
            "Green Component": 0.5,
            "Blue Component": 0.5,
        }
        prof = _make_profile({"Bold Color": color_dict})
        bold = prof.bold_color
        assert bold is not None
        assert bold.red == 127.5

    def test_link_color(self):
        color_dict = {
            "Red Component": 0.0,
            "Green Component": 0.0,
            "Blue Component": 1.0,
        }
        prof = _make_profile({"Link Color": color_dict})
        link = prof.link_color
        assert link is not None
        assert link.blue == 255

    def test_selection_color(self):
        color_dict = {
            "Red Component": 0.4,
            "Green Component": 0.4,
            "Blue Component": 0.8,
        }
        prof = _make_profile({"Selection Color": color_dict})
        sel = prof.selection_color
        assert sel is not None

    def test_selected_text_color(self):
        color_dict = {
            "Red Component": 1.0,
            "Green Component": 1.0,
            "Blue Component": 1.0,
        }
        prof = _make_profile({"Selected Text Color": color_dict})
        txt = prof.selected_text_color
        assert txt is not None
        assert txt.red == 255

    def test_foreground_color_light(self):
        color_dict = {"Red Component": 0.2, "Green Component": 0.2, "Blue Component": 0.2}
        prof = _make_profile({"Foreground Color (Light)": color_dict})
        assert prof.foreground_color_light is not None

    def test_foreground_color_dark(self):
        color_dict = {"Red Component": 0.8, "Green Component": 0.8, "Blue Component": 0.8}
        prof = _make_profile({"Foreground Color (Dark)": color_dict})
        assert prof.foreground_color_dark is not None

    def test_background_color_light(self):
        color_dict = {"Red Component": 1.0, "Green Component": 1.0, "Blue Component": 1.0}
        prof = _make_profile({"Background Color (Light)": color_dict})
        assert prof.background_color_light is not None

    def test_background_color_dark(self):
        color_dict = {"Red Component": 0.1, "Green Component": 0.1, "Blue Component": 0.1}
        prof = _make_profile({"Background Color (Dark)": color_dict})
        assert prof.background_color_dark is not None

    def test_bold_color_light(self):
        color_dict = {"Red Component": 0.9, "Green Component": 0.9, "Blue Component": 0.9}
        prof = _make_profile({"Bold Color (Light)": color_dict})
        assert prof.bold_color_light is not None

    def test_bold_color_dark(self):
        color_dict = {"Red Component": 0.3, "Green Component": 0.3, "Blue Component": 0.3}
        prof = _make_profile({"Bold Color (Dark)": color_dict})
        assert prof.bold_color_dark is not None

    def test_link_color_light(self):
        color_dict = {"Red Component": 0.0, "Green Component": 0.5, "Blue Component": 1.0}
        prof = _make_profile({"Link Color (Light)": color_dict})
        assert prof.link_color_light is not None

    def test_link_color_dark(self):
        color_dict = {"Red Component": 0.0, "Green Component": 0.0, "Blue Component": 0.5}
        prof = _make_profile({"Link Color (Dark)": color_dict})
        assert prof.link_color_dark is not None

    def test_selection_color_light(self):
        color_dict = {"Red Component": 0.5, "Green Component": 0.5, "Blue Component": 0.9}
        prof = _make_profile({"Selection Color (Light)": color_dict})
        assert prof.selection_color_light is not None

    def test_selection_color_dark(self):
        color_dict = {"Red Component": 0.2, "Green Component": 0.2, "Blue Component": 0.5}
        prof = _make_profile({"Selection Color (Dark)": color_dict})
        assert prof.selection_color_dark is not None

    def test_selected_text_color_light(self):
        color_dict = {"Red Component": 0.0, "Green Component": 0.0, "Blue Component": 0.0}
        prof = _make_profile({"Selected Text Color (Light)": color_dict})
        assert prof.selected_text_color_light is not None

    def test_selected_text_color_dark(self):
        color_dict = {"Red Component": 1.0, "Green Component": 1.0, "Blue Component": 1.0}
        prof = _make_profile({"Selected Text Color (Dark)": color_dict})
        assert prof.selected_text_color_dark is not None


class TestProfileBoolGetters:
    def test_use_bright_bold(self):
        prof = _make_profile({"Use Bright Bold": True})
        assert prof.use_bright_bold is True

    def test_use_bright_bold_none(self):
        prof = _make_profile({})
        assert prof.use_bright_bold is None

    def test_use_bright_bold_light(self):
        prof = _make_profile({"Use Bright Bold (Light)": True})
        assert prof.use_bright_bold_light is True

    def test_use_bright_bold_dark(self):
        prof = _make_profile({"Use Bright Bold (Dark)": False})
        assert prof.use_bright_bold_dark is False

    def test_use_bold_color(self):
        prof = _make_profile({"Use Bright Bold": True})
        assert prof.use_bold_color is True

    def test_use_bold_color_light(self):
        prof = _make_profile({"Use Bright Bold (Light)": False})
        assert prof.use_bold_color_light is False

    def test_use_bold_color_dark(self):
        prof = _make_profile({"Use Bright Bold (Dark)": True})
        assert prof.use_bold_color_dark is True

    def test_brighten_bold_text(self):
        prof = _make_profile({"Brighten Bold Text": True})
        assert prof.brighten_bold_text is True

    def test_brighten_bold_text_none(self):
        prof = _make_profile({})
        assert prof.brighten_bold_text is None

    def test_brighten_bold_text_light(self):
        prof = _make_profile({"Brighten Bold Text (Light)": True})
        assert prof.brighten_bold_text_light is True

    def test_brighten_bold_text_dark(self):
        prof = _make_profile({"Brighten Bold Text (Dark)": False})
        assert prof.brighten_bold_text_dark is False

    def test_blinking_cursor(self):
        prof = _make_profile({"Blinking Cursor": True})
        assert prof.blinking_cursor is True

    def test_cursor_shadow(self):
        prof = _make_profile({"Cursor Shadow": False})
        assert prof.cursor_shadow is False

    def test_use_bold_font(self):
        prof = _make_profile({"Use Bold Font": True})
        assert prof.use_bold_font is True

    def test_ascii_ligatures(self):
        prof = _make_profile({"ASCII Ligatures": True})
        assert prof.ascii_ligatures is True

    def test_non_ascii_ligatures(self):
        prof = _make_profile({"Non-ASCII Ligatures": False})
        assert prof.non_ascii_ligatures is False

    def test_blink_allowed(self):
        prof = _make_profile({"Blink Allowed": True})
        assert prof.blink_allowed is True

    def test_use_italic_font(self):
        prof = _make_profile({"Use Italic Font": True})
        assert prof.use_italic_font is True

    def test_ambiguous_double_width(self):
        prof = _make_profile({"Ambiguous Double Width": True})
        assert prof.ambiguous_double_width is True

    def test_use_non_ascii_font(self):
        prof = _make_profile({"Use Non-ASCII Font": False})
        assert prof.use_non_ascii_font is False

    def test_use_cursor_guide(self):
        prof = _make_profile({"Use Cursor Guide": True})
        assert prof.use_cursor_guide is True

    def test_use_cursor_guide_light(self):
        prof = _make_profile({"Use Cursor Guide (Light)": True})
        assert prof.use_cursor_guide_light is True

    def test_use_cursor_guide_dark(self):
        prof = _make_profile({"Use Cursor Guide (Dark)": False})
        assert prof.use_cursor_guide_dark is False


class TestProfileNumericGetters:
    def test_horizontal_spacing(self):
        prof = _make_profile({"Horizontal Spacing": 1.2})
        assert prof.horizontal_spacing == 1.2

    def test_vertical_spacing(self):
        prof = _make_profile({"Vertical Spacing": 1.5})
        assert prof.vertical_spacing == 1.5

    def test_transparency(self):
        prof = _make_profile({"Transparency": 0.75})
        assert prof.transparency == 0.75

    def test_allow_change_cursor_blink(self):
        prof = _make_profile({"Allow Change Cursor Blink": True})
        assert prof.allow_change_cursor_blink is True

    def test_cursor_type(self):
        prof = _make_profile({"Cursor Type": 2})
        assert prof.cursor_type == 2

    def test_cursor_type_none(self):
        prof = _make_profile({})
        assert prof.cursor_type is None

    def test_thin_strokes(self):
        prof = _make_profile({"Thin Strokes": 3})
        assert prof.thin_strokes == 3

    def test_thin_strokes_none(self):
        prof = _make_profile({})
        assert prof.thin_strokes is None


class TestProfileTitleComponents:
    def test_title_components_single(self):
        prof = _make_profile({"Title Components": 1})
        comps = prof.title_components
        assert comps is not None
        assert iterm2.TitleComponents.SESSION_NAME in comps

    def test_title_components_multiple(self):
        bitmask = (1 << 0) | (1 << 1) | (1 << 2)
        prof = _make_profile({"Title Components": bitmask})
        comps = prof.title_components
        assert iterm2.TitleComponents.SESSION_NAME in comps
        assert iterm2.TitleComponents.JOB in comps
        assert iterm2.TitleComponents.WORKING_DIRECTORY in comps

    def test_title_components_custom(self):
        prof = _make_profile({"Title Components": (1 << 4)})
        comps = prof.title_components
        assert iterm2.TitleComponents.CUSTOM in comps

    def test_title_components_zero(self):
        prof = _make_profile({"Title Components": 0})
        comps = prof.title_components
        assert comps == []

    def test_title_function(self):
        prof = _make_profile({"Title Function": ["Display Name", "com.example.id"]})
        result = prof.title_function
        assert result == ("Display Name", "com.example.id")

    def test_title_function_missing(self):
        prof = _make_profile({})
        with pytest.raises(TypeError):
            _ = prof.title_function


class TestProfileLocalWriteOnlyCopy:
    def test_local_write_only_copy(self):
        props = {"Guid": "g1", "Name": "Test", "Foo": "bar"}
        prof = _make_profile(props)
        copy = prof.local_write_only_copy
        assert isinstance(copy, iterm2.LocalWriteOnlyProfile)
        assert copy.values["Guid"] == json.dumps("g1")
        assert copy.values["Name"] == json.dumps("Test")
        assert copy.values["Foo"] == json.dumps("bar")


class TestTitleComponentsExtra:
    def test_host(self):
        assert iterm2.TitleComponents.HOST.value == (1 << 8)

    def test_command_line(self):
        assert iterm2.TitleComponents.COMMAND_LINE.value == (1 << 9)

    def test_size(self):
        assert iterm2.TitleComponents.SIZE.value == (1 << 10)

    def test_profile_name(self):
        assert iterm2.TitleComponents.PROFILE_NAME.value == (1 << 5)

    def test_profile_and_session_name(self):
        assert iterm2.TitleComponents.PROFILE_AND_SESSION_NAME.value == (1 << 6)

    def test_user(self):
        assert iterm2.TitleComponents.USER.value == (1 << 7)

    def test_toJSON_host(self):
        assert json.loads(iterm2.TitleComponents.HOST.toJSON()) == (1 << 8)

    def test_toJSON_command_line(self):
        assert json.loads(iterm2.TitleComponents.COMMAND_LINE.toJSON()) == (1 << 9)

    def test_toJSON_size(self):
        assert json.loads(iterm2.TitleComponents.SIZE.toJSON()) == (1 << 10)


class TestProfilePropertyProtobuf:
    def test_create_profile_property(self):
        prop = iterm2.api_pb2.ProfileProperty()
        prop.key = "TestKey"
        prop.json_value = json.dumps("test_value")
        assert prop.key == "TestKey"
        assert json.loads(prop.json_value) == "test_value"

    def test_profile_property_with_int(self):
        prop = iterm2.api_pb2.ProfileProperty()
        prop.key = "Count"
        prop.json_value = json.dumps(42)
        assert json.loads(prop.json_value) == 42

    def test_profile_property_with_dict(self):
        color_data = {"Red Component": 1.0, "Green Component": 0.5, "Blue Component": 0.0}
        prop = iterm2.api_pb2.ProfileProperty()
        prop.key = "Foreground Color"
        prop.json_value = json.dumps(color_data)
        parsed = json.loads(prop.json_value)
        assert parsed["Red Component"] == 1.0
        assert parsed["Green Component"] == 0.5

    def test_profile_property_with_bool(self):
        prop = iterm2.api_pb2.ProfileProperty()
        prop.key = "Enabled"
        prop.json_value = json.dumps(True)
        assert json.loads(prop.json_value) is True

    def test_profile_property_with_none(self):
        prop = iterm2.api_pb2.ProfileProperty()
        prop.key = "Optional"
        prop.json_value = json.dumps(None)
        assert json.loads(prop.json_value) is None

    def test_profile_property_with_list(self):
        prop = iterm2.api_pb2.ProfileProperty()
        prop.key = "Title Function"
        prop.json_value = json.dumps(["Name", "com.example"])
        parsed = json.loads(prop.json_value)
        assert parsed == ["Name", "com.example"]


class TestWriteOnlyProfile:
    def test_init_with_session_id(self):
        prof = iterm2.WriteOnlyProfile("session-1", None)
        assert prof.session_id == "session-1"

    def test_init_with_guid(self):
        prof = iterm2.WriteOnlyProfile(None, None, guid="profile-guid")
        assert prof.session_id is None
        assert prof._WriteOnlyProfile__guid == "profile-guid"

    def test_guids_for_set_with_session(self):
        prof = iterm2.WriteOnlyProfile("session-1", None)
        result = prof._guids_for_set()
        assert result == "session-1"

    def test_guids_for_set_with_guid(self):
        prof = iterm2.WriteOnlyProfile(None, None, guid="profile-guid")
        result = prof._guids_for_set()
        assert result == ["profile-guid"]

    def test_init_rejects_all(self):
        with pytest.raises(AssertionError):
            iterm2.WriteOnlyProfile("all", None)


class TestPartialProfile:
    def test_is_subclass_of_profile(self):
        assert issubclass(iterm2.PartialProfile, iterm2.Profile)


class TestColorRoundTrip:
    def test_color_get_set_roundtrip(self):
        color_dict = {
            "Red Component": 0.8,
            "Green Component": 0.4,
            "Blue Component": 0.2,
            "Alpha Component": 0.9,
            "Color Space": "sRGB",
        }
        prof = _make_profile({"Foreground Color": color_dict})
        fg = prof.foreground_color
        assert fg is not None
        assert fg.red == 204.0
        assert fg.green == 102.0
        assert fg.blue == 51.0
        assert fg.alpha == 229.5
        assert fg.color_space == iterm2.ColorSpace.SRGB

    def test_color_missing_alpha_defaults_to_255(self):
        color_dict = {
            "Red Component": 1.0,
            "Green Component": 0.0,
            "Blue Component": 0.0,
        }
        prof = _make_profile({"Foreground Color": color_dict})
        fg = prof.foreground_color
        assert fg is not None
        assert fg.alpha == 255

    def test_color_missing_colorspace_defaults_to_calibrated(self):
        color_dict = {
            "Red Component": 0.0,
            "Green Component": 1.0,
            "Blue Component": 0.0,
        }
        prof = _make_profile({"Foreground Color": color_dict})
        fg = prof.foreground_color
        assert fg is not None
        assert fg.color_space == iterm2.ColorSpace.CALIBRATED


class TestLocalWriteOnlyProfileAnsiColors:
    def test_set_ansi_4_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 0, 0)
        prof.set_ansi_4_color(color)
        assert prof.values["Ansi 4 Color"] == json.dumps(color.get_dict())

    def test_set_ansi_5_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 255, 0)
        prof.set_ansi_5_color(color)
        assert prof.values["Ansi 5 Color"] == json.dumps(color.get_dict())

    def test_set_ansi_12_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 0, 255)
        prof.set_ansi_12_color(color)
        assert prof.values["Ansi 12 Color"] == json.dumps(color.get_dict())

    def test_set_ansi_15_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(238, 238, 238)
        prof.set_ansi_15_color(color)
        assert prof.values["Ansi 15 Color"] == json.dumps(color.get_dict())


class TestLocalWriteOnlyProfileTabColors:
    def test_set_tab_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(100, 150, 200)
        prof.set_tab_color(color)
        assert prof.values["Tab Color"] == json.dumps(color.get_dict())

    def test_set_tab_color_none(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_tab_color(None)
        assert prof.values["Tab Color"] == "null"


class TestProfileTabColor:
    def test_tab_color(self):
        color_dict = {
            "Red Component": 0.5,
            "Green Component": 0.5,
            "Blue Component": 0.5,
        }
        prof = _make_profile({"Tab Color": color_dict})
        tc = prof.tab_color
        assert tc is not None
        assert tc.red == 127.5

    def test_tab_color_none(self):
        prof = _make_profile({})
        assert prof.tab_color is None


class TestLocalWriteOnlyProfileWorkspace:
    def test_set_custom_directory(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_custom_directory("/tmp")
        assert prof.values["Working Directory"] == json.dumps("/tmp")

    def test_set_custom_directory_home(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_custom_directory("/home/user")
        assert prof.values["Working Directory"] == json.dumps("/home/user")


class TestLocalWriteOnlyProfileCommand:
    def test_set_use_custom_command_enabled(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_custom_command("Yes")
        assert prof.values["Custom Command"] == json.dumps("Yes")

    def test_set_use_custom_command_disabled(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_use_custom_command("No")
        assert prof.values["Custom Command"] == json.dumps("No")

    def test_set_command(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_command("echo hello")
        assert prof.values["Command"] == json.dumps("echo hello")


class TestProfileStringGetters:
    def test_name(self):
        prof = _make_profile({"Name": "My Profile"})
        assert prof.name == "My Profile"

    def test_name_none(self):
        prof = _make_profile({})
        assert prof.name is None

    def test_badge_text(self):
        prof = _make_profile({"Badge Text": "custom badge"})
        assert prof.badge_text == "custom badge"

    def test_custom_directory(self):
        prof = _make_profile({"Working Directory": "/path/ws"})
        assert prof.custom_directory == "/path/ws"

    def test_use_custom_command(self):
        prof = _make_profile({"Custom Command": "Yes"})
        assert prof.use_custom_command == "Yes"

    def test_command(self):
        prof = _make_profile({"Command": "ls -la"})
        assert prof.command == "ls -la"


class TestLocalWriteOnlyProfilePreset:
    def test_set_name_as_preset(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_name("Solarized Dark")
        assert prof.values["Name"] == json.dumps("Solarized Dark")


class TestProfilePreset:
    def test_name_as_preset(self):
        prof = _make_profile({"Name": "Solarized Dark"})
        assert prof.name == "Solarized Dark"

    def test_name_none(self):
        prof = _make_profile({})
        assert prof.name is None


class TestProfileGetColorWithKey:
    def test_get_color_with_key_valid(self):
        color_dict = {
            "Red Component": 1.0,
            "Green Component": 0.0,
            "Blue Component": 0.0,
        }
        prof = _make_profile({"My Color": color_dict})
        c = prof.get_color_with_key("My Color")
        assert c is not None
        assert c.red == 255

    def test_get_color_with_key_missing(self):
        prof = _make_profile({})
        c = prof.get_color_with_key("Nonexistent")
        assert c is None

    def test_get_color_with_key_invalid_value(self):
        prof = _make_profile({"Bad Color": "not a dict"})
        with pytest.raises(TypeError):
            prof.get_color_with_key("Bad Color")


class TestProfileCursorColor:
    def test_cursor_color(self):
        color_dict = {"Red Component": 1.0, "Green Component": 0.0, "Blue Component": 0.0}
        prof = _make_profile({"Cursor Color": color_dict})
        assert prof.cursor_color is not None
        assert prof.cursor_color.red == 255

    def test_cursor_text_color(self):
        color_dict = {"Red Component": 0.0, "Green Component": 1.0, "Blue Component": 0.0}
        prof = _make_profile({"Cursor Text Color": color_dict})
        assert prof.cursor_text_color is not None
        assert prof.cursor_text_color.green == 255


class TestLocalWriteOnlyProfileCursorColor:
    def test_set_cursor_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 255, 255)
        prof.set_cursor_color(color)
        assert prof.values["Cursor Color"] == json.dumps(color.get_dict())

    def test_set_cursor_text_color(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 0, 0)
        prof.set_cursor_text_color(color)
        assert prof.values["Cursor Text Color"] == json.dumps(color.get_dict())

    def test_set_cursor_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(100, 100, 100)
        prof.set_cursor_color_light(color)
        assert prof.values["Cursor Color (Light)"] == json.dumps(color.get_dict())

    def test_set_cursor_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(200, 200, 200)
        prof.set_cursor_color_dark(color)
        assert prof.values["Cursor Color (Dark)"] == json.dumps(color.get_dict())

    def test_set_cursor_text_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(50, 50, 50)
        prof.set_cursor_text_color_light(color)
        assert prof.values["Cursor Text Color (Light)"] == json.dumps(color.get_dict())

    def test_set_cursor_text_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(250, 250, 250)
        prof.set_cursor_text_color_dark(color)
        assert prof.values["Cursor Text Color (Dark)"] == json.dumps(color.get_dict())


class TestProfileCursorColorVariants:
    def test_cursor_color_light(self):
        color_dict = {"Red Component": 0.5, "Green Component": 0.5, "Blue Component": 0.5}
        prof = _make_profile({"Cursor Color (Light)": color_dict})
        assert prof.cursor_color_light is not None

    def test_cursor_color_dark(self):
        color_dict = {"Red Component": 0.8, "Green Component": 0.8, "Blue Component": 0.8}
        prof = _make_profile({"Cursor Color (Dark)": color_dict})
        assert prof.cursor_color_dark is not None

    def test_cursor_text_color_light(self):
        color_dict = {"Red Component": 0.1, "Green Component": 0.1, "Blue Component": 0.1}
        prof = _make_profile({"Cursor Text Color (Light)": color_dict})
        assert prof.cursor_text_color_light is not None

    def test_cursor_text_color_dark(self):
        color_dict = {"Red Component": 0.9, "Green Component": 0.9, "Blue Component": 0.9}
        prof = _make_profile({"Cursor Text Color (Dark)": color_dict})
        assert prof.cursor_text_color_dark is not None


class TestLocalWriteOnlyProfileBadgeColorVariants:
    def test_set_badge_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(255, 0, 0)
        prof.set_badge_color_light(color)
        assert prof.values["Badge Color (Light)"] == json.dumps(color.get_dict())

    def test_set_badge_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(0, 0, 255)
        prof.set_badge_color_dark(color)
        assert prof.values["Badge Color (Dark)"] == json.dumps(color.get_dict())


class TestProfileBadgeColor:
    def test_badge_color(self):
        color_dict = {"Red Component": 1.0, "Green Component": 0.0, "Blue Component": 0.0}
        prof = _make_profile({"Badge Color": color_dict})
        assert prof.badge_color is not None
        assert prof.badge_color.red == 255

    def test_badge_color_light(self):
        color_dict = {"Red Component": 0.5, "Green Component": 0.5, "Blue Component": 0.5}
        prof = _make_profile({"Badge Color (Light)": color_dict})
        assert prof.badge_color_light is not None

    def test_badge_color_dark(self):
        color_dict = {"Red Component": 0.2, "Green Component": 0.2, "Blue Component": 0.2}
        prof = _make_profile({"Badge Color (Dark)": color_dict})
        assert prof.badge_color_dark is not None


class TestLocalWriteOnlyProfileCursorGuideColor:
    def test_set_cursor_guide_color_light(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(200, 200, 200, 100)
        prof.set_cursor_guide_color_light(color)
        assert prof.values["Cursor Guide Color (Light)"] == json.dumps(color.get_dict())

    def test_set_cursor_guide_color_dark(self):
        prof = iterm2.LocalWriteOnlyProfile()
        color = iterm2.Color(50, 50, 50, 200)
        prof.set_cursor_guide_color_dark(color)
        assert prof.values["Cursor Guide Color (Dark)"] == json.dumps(color.get_dict())


class TestProfileCursorGuideColor:
    def test_cursor_guide_color(self):
        color_dict = {"Red Component": 0.5, "Green Component": 0.5, "Blue Component": 0.5}
        prof = _make_profile({"Cursor Guide Color": color_dict})
        assert prof.cursor_guide_color is not None

    def test_cursor_guide_color_light(self):
        color_dict = {"Red Component": 0.8, "Green Component": 0.8, "Blue Component": 0.8}
        prof = _make_profile({"Cursor Guide Color (Light)": color_dict})
        assert prof.cursor_guide_color_light is not None

    def test_cursor_guide_color_dark(self):
        color_dict = {"Red Component": 0.2, "Green Component": 0.2, "Blue Component": 0.2}
        prof = _make_profile({"Cursor Guide Color (Dark)": color_dict})
        assert prof.cursor_guide_color_dark is not None


class TestLocalWriteOnlyProfileFont:
    def test_set_normal_font(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_normal_font("Monaco:12")
        assert prof.values["Normal Font"] == json.dumps("Monaco:12")

    def test_set_non_ascii_font(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_non_ascii_font("Helvetica:14")
        assert prof.values["Non Ascii Font"] == json.dumps("Helvetica:14")


class TestProfileFont:
    def test_normal_font(self):
        prof = _make_profile({"Normal Font": "Monaco:12"})
        assert prof.normal_font == "Monaco:12"

    def test_non_ascii_font(self):
        prof = _make_profile({"Non Ascii Font": "Helvetica:14"})
        assert prof.non_ascii_font == "Helvetica:14"


class TestLocalWriteOnlyProfileBackgroundImage:
    def test_set_background_image_location(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_background_image_location("/path/to/image.png")
        assert prof.values["Background Image Location"] == json.dumps("/path/to/image.png")

    def test_set_background_image_mode(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_background_image_mode(iterm2.BackgroundImageMode.ASPECT_FILL)
        assert prof.values["Background Image Mode"] == json.dumps(2)


class TestProfileBackgroundImage:
    def test_background_image_location(self):
        prof = _make_profile({"Background Image Location": "/path/img.png"})
        assert prof.background_image_location == "/path/img.png"

    def test_background_image_mode(self):
        prof = _make_profile({"Background Image Mode": 2})
        assert prof.background_image_mode == iterm2.BackgroundImageMode.ASPECT_FILL


class TestLocalWriteOnlyProfileTermination:
    def test_set_command(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_command("echo start")
        assert prof.values["Command"] == json.dumps("echo start")


class TestProfileTermination:
    def test_command(self):
        prof = _make_profile({"Command": "echo hi"})
        assert prof.command == "echo hi"


class TestLocalWriteOnlyProfileMouseReporting:
    def test_set_mouse_reporting(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_mouse_reporting(2)
        assert prof.values["Mouse Reporting"] == json.dumps(2)


class TestProfileMouseReporting:
    def test_mouse_reporting(self):
        prof = _make_profile({"Mouse Reporting": 2})
        assert prof.mouse_reporting == 2


class TestLocalWriteOnlyProfileScrollback:
    def test_set_unlimited_scrollback(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_unlimited_scrollback(True)
        assert prof.values["Unlimited Scrollback"] == json.dumps(True)

    def test_set_scrollback_in_alternate_screen(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_scrollback_in_alternate_screen(True)
        assert prof.values["Scrollback in Alternate Screen"] == json.dumps(True)

    def test_set_scrollback_lines(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_scrollback_lines(10000)
        assert prof.values["Scrollback Lines"] == json.dumps(10000)


class TestProfileScrollback:
    def test_unlimited_scrollback(self):
        prof = _make_profile({"Unlimited Scrollback": True})
        assert prof.unlimited_scrollback is True

    def test_scrollback_in_alternate_screen(self):
        prof = _make_profile({"Scrollback in Alternate Screen": False})
        assert prof.scrollback_in_alternate_screen is False

    def test_scrollback_lines(self):
        prof = _make_profile({"Scrollback Lines": 5000})
        assert prof.scrollback_lines == 5000


class TestLocalWriteOnlyProfileUnicode:
    def test_set_unicode_version(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_unicode_version(9)
        assert prof.values["Unicode Version"] == json.dumps(9)

    def test_set_unicode_normalization(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_unicode_normalization(iterm2.UnicodeNormalization.UNICODE_NORMALIZATION_NFC)
        assert prof.values["Unicode Normalization"] == json.dumps(1)

    def test_set_character_encoding(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_character_encoding(iterm2.CharacterEncoding.CHARACTER_ENCODING_UTF_8)
        assert prof.values["Character Encoding"] == json.dumps(4)


class TestProfileUnicode:
    def test_unicode_version(self):
        prof = _make_profile({"Unicode Version": 9})
        assert prof.unicode_version == 9

    def test_unicode_normalization(self):
        prof = _make_profile({"Unicode Normalization": 1})
        assert prof.unicode_normalization == 1

    def test_character_encoding(self):
        prof = _make_profile({"Character Encoding": 4})
        assert prof.character_encoding == 4


class TestLocalWriteOnlyProfileOptionKey:
    def test_set_left_option_key_sends(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_left_option_key_sends(iterm2.OptionKeySends.OPTION_KEY_ESC)
        assert prof.values["Option Key Sends"] == json.dumps(2)


class TestProfileOptionKey:
    def test_left_option_key_sends(self):
        prof = _make_profile({"Option Key Sends": 2})
        assert prof.left_option_key_sends == 2


class TestLocalWriteOnlyProfileWorkingDirectory:
    def test_set_initial_directory_mode(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_initial_directory_mode(iterm2.InitialWorkingDirectory.INITIAL_WORKING_DIRECTORY_CUSTOM)
        assert prof.values["Custom Directory"] == json.dumps("Yes")

    def test_set_custom_directory(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_custom_directory("/custom/path")
        assert prof.values["Working Directory"] == json.dumps("/custom/path")


class TestProfileWorkingDirectory:
    def test_initial_directory_mode(self):
        prof = _make_profile({"Custom Directory": "Yes"})
        assert prof.initial_directory_mode == "Yes"

    def test_custom_directory(self):
        prof = _make_profile({"Working Directory": "/custom/path"})
        assert prof.custom_directory == "/custom/path"


class TestLocalWriteOnlyProfileIcon:
    def test_set_icon_mode(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_icon_mode(iterm2.IconMode.CUSTOM)
        assert prof.values["Icon"] == json.dumps(2)

    def test_set_custom_icon_path(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_custom_icon_path("/path/to/icon.png")
        assert prof.values["Custom Icon Path"] == json.dumps("/path/to/icon.png")


class TestProfileIcon:
    def test_icon_mode(self):
        prof = _make_profile({"Icon": 2})
        assert prof.icon_mode == 2

    def test_custom_icon_path(self):
        prof = _make_profile({"Custom Icon Path": "/path/icon.png"})
        assert prof.custom_icon_path == "/path/icon.png"


class TestLocalWriteOnlyProfileSilenceBell:
    def test_set_silence_bell(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_silence_bell(True)
        assert prof.values["Silence Bell"] == json.dumps(True)


class TestProfileSilenceBell:
    def test_silence_bell(self):
        prof = _make_profile({"Silence Bell": True})
        assert prof.silence_bell is True


class TestLocalWriteOnlyProfileVisualBell:
    def test_set_visual_bell(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_visual_bell(True)
        assert prof.values["Visual Bell"] == json.dumps(True)


class TestProfileVisualBell:
    def test_visual_bell(self):
        prof = _make_profile({"Visual Bell": True})
        assert prof.visual_bell is True


class TestLocalWriteOnlyProfileTriggers:
    def test_set_triggers(self):
        prof = iterm2.LocalWriteOnlyProfile()
        triggers = [{"regex": "test", "action": "Notify"}]
        prof.set_triggers(triggers)
        assert prof.values["Triggers"] == json.dumps(triggers)


class TestProfileTriggers:
    def test_triggers(self):
        triggers = [{"regex": "test", "action": "Notify"}]
        prof = _make_profile({"Triggers": triggers})
        assert prof.triggers == triggers


class TestLocalWriteOnlyProfileProfileName:
    def test_set_name(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_name("My Profile")
        assert prof.values["Name"] == json.dumps("My Profile")


class TestLocalWriteOnlyProfileSession:
    def test_set_initial_directory_mode_home(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_initial_directory_mode(iterm2.InitialWorkingDirectory.INITIAL_WORKING_DIRECTORY_HOME)
        assert prof.values["Custom Directory"] == json.dumps("No")


class TestLocalWriteOnlyProfileAutoHideCursor:
    def test_set_blinking_cursor(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_blinking_cursor(True)
        assert prof.values["Blinking Cursor"] == json.dumps(True)


class TestProfileAutoHideCursor:
    def test_blinking_cursor(self):
        prof = _make_profile({"Blinking Cursor": True})
        assert prof.blinking_cursor is True


class TestLocalWriteOnlyProfileCloseSession:
    def test_set_close_sessions_on_end(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_close_sessions_on_end(True)
        assert prof.values["Close Sessions On End"] == json.dumps(True)


class TestProfileCloseSession:
    def test_close_sessions_on_end(self):
        prof = _make_profile({"Close Sessions On End": True})
        assert prof.close_sessions_on_end is True


class TestLocalWriteOnlyProfilePasswordManager:
    def test_set_open_password_manager_automatically(self):
        prof = iterm2.LocalWriteOnlyProfile()
        prof.set_open_password_manager_automatically(True)
        assert prof.values["Open Password Manager Automatically"] == json.dumps(True)


class TestProfilePasswordManager:
    def test_open_password_manager_automatically(self):
        prof = _make_profile({"Open Password Manager Automatically": True})
        assert prof.open_password_manager_automatically is True


class TestColorSpace:
    def test_srgb(self):
        assert iterm2.ColorSpace.SRGB.value == "sRGB"

    def test_calibrated(self):
        assert iterm2.ColorSpace.CALIBRATED.value == "Calibrated"

    def test_p3(self):
        assert iterm2.ColorSpace.P3.value == "P3"


class TestColor:
    def test_constructor_defaults(self):
        c = iterm2.Color()
        assert c.red == 0
        assert c.green == 0
        assert c.blue == 0
        assert c.alpha == 255
        assert c.color_space == iterm2.ColorSpace.SRGB

    def test_constructor_values(self):
        c = iterm2.Color(100, 150, 200, 200, iterm2.ColorSpace.P3)
        assert c.red == 100
        assert c.green == 150
        assert c.blue == 200
        assert c.alpha == 200
        assert c.color_space == iterm2.ColorSpace.P3

    def test_get_dict(self):
        c = iterm2.Color(255, 128, 64, 255)
        d = c.get_dict()
        assert d["Red Component"] == 1.0
        assert d["Green Component"] == 128 / 255.0
        assert d["Blue Component"] == 64 / 255.0
        assert d["Alpha Component"] == 1.0
        assert d["Color Space"] == "sRGB"

    def test_from_dict(self):
        c = iterm2.Color()
        c.from_dict({
            "Red Component": 1.0,
            "Green Component": 0.5,
            "Blue Component": 0.25,
            "Alpha Component": 0.8,
            "Color Space": "sRGB",
        })
        assert c.red == 255
        assert c.green == 127.5
        assert c.blue == 63.75
        assert c.alpha == 204.0
        assert c.color_space == iterm2.ColorSpace.SRGB

    def test_json_property(self):
        c = iterm2.Color(255, 0, 0)
        j = c.json
        parsed = json.loads(j)
        assert parsed["Red Component"] == 1.0

    def test_hex_property(self):
        c = iterm2.Color(255, 170, 85)
        assert c.hex == "#ffaa55"

    def test_hex_p3(self):
        c = iterm2.Color(255, 170, 85, 255, iterm2.ColorSpace.P3)
        assert c.hex == "p3#ffaa55"

    def test_repr(self):
        c = iterm2.Color(100, 150, 200, 255, iterm2.ColorSpace.SRGB)
        r = repr(c)
        assert "100" in r
        assert "150" in r
        assert "200" in r

    def test_from_hex_6digit(self):
        c = iterm2.Color.from_hex("#aabbcc")
        assert c is not None
        assert c.red == 170
        assert c.green == 187
        assert c.blue == 204

    def test_from_hex_12digit(self):
        c = iterm2.Color.from_hex("#aabb00cc0011")
        assert c is not None
        assert c.red == 170
        assert c.green == 0
        assert c.blue == 0

    def test_from_hex_p3(self):
        c = iterm2.Color.from_hex("p3#aabbcc")
        assert c is not None
        assert c.color_space == iterm2.ColorSpace.P3

    def test_from_hex_invalid(self):
        assert iterm2.Color.from_hex("invalid") is None
        assert iterm2.Color.from_hex("#abc") is None

    def test_color_setters(self):
        c = iterm2.Color()
        c.red = 100
        c.green = 150
        c.blue = 200
        c.alpha = 200
        c.color_space = iterm2.ColorSpace.P3
        assert c.red == 100
        assert c.green == 150
        assert c.blue == 200
        assert c.alpha == 200
        assert c.color_space == iterm2.ColorSpace.P3
