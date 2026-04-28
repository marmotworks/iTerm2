import pytest
import json
import base64
import iterm2.statusbar
import iterm2.color


class TestBaseKnob:
    def test_to_proto(self):
        knob_type = iterm2.api_pb2.RPCRegistrationRequest.StatusBarComponentAttributes.Knob.Checkbox
        knob = iterm2.statusbar.BaseKnob(
            knob_type=knob_type,
            name="Test Knob",
            placeholder="Enter value",
            json_default_value=json.dumps("default"),
            key="test_key"
        )
        proto = knob.to_proto()
        assert proto.name == "Test Knob"
        assert proto.type == knob_type
        assert proto.placeholder == "Enter value"
        assert proto.json_default_value == json.dumps("default")
        assert proto.key == "test_key"


class TestKnob:
    def test_to_proto(self):
        knob = iterm2.statusbar.Knob(
            knob_type=1,
            name="Knob",
            placeholder="ph",
            json_default_value=json.dumps(42),
            key="k1"
        )
        proto = knob.to_proto()
        assert proto.name == "Knob"
        assert proto.key == "k1"


class TestCheckboxKnob:
    def test_init_true(self):
        knob = iterm2.statusbar.CheckboxKnob("Enable", True, "chk1")
        proto = knob.to_proto()
        assert proto.name == "Enable"
        assert proto.key == "chk1"
        assert json.loads(proto.json_default_value) is True

    def test_init_false(self):
        knob = iterm2.statusbar.CheckboxKnob("Disable", False, "chk2")
        proto = knob.to_proto()
        assert json.loads(proto.json_default_value) is False


class TestStringKnob:
    def test_init(self):
        knob = iterm2.statusbar.StringKnob("Label", "Placeholder", "default", "str1")
        proto = knob.to_proto()
        assert proto.name == "Label"
        assert proto.placeholder == "Placeholder"
        assert proto.key == "str1"
        assert json.loads(proto.json_default_value) == "default"


class TestPositiveFloatingPointKnob:
    def test_init(self):
        knob = iterm2.statusbar.PositiveFloatingPointKnob("Value", 3.14, "fp1")
        proto = knob.to_proto()
        assert proto.name == "Value"
        assert proto.key == "fp1"
        assert json.loads(proto.json_default_value) == 3.14


class TestColorKnob:
    def test_init(self):
        color = iterm2.color.Color(255, 0, 0, 255, iterm2.color.ColorSpace.SRGB)
        knob = iterm2.statusbar.ColorKnob("Color Picker", color, "clr1")
        proto = knob.to_proto()
        assert proto.name == "Color Picker"
        assert proto.key == "clr1"
        parsed = json.loads(proto.json_default_value)
        assert parsed["Red Component"] == 1.0
        assert parsed["Green Component"] == 0.0
        assert parsed["Blue Component"] == 0.0


class TestStatusBarComponentFormat:
    def test_format_values(self):
        assert iterm2.statusbar.StatusBarComponent.Format.PLAIN_TEXT.value is not None
        assert iterm2.statusbar.StatusBarComponent.Format.HTML.value is not None

    def test_all_formats_present(self):
        members = [m.name for m in iterm2.statusbar.StatusBarComponent.Format]
        assert "PLAIN_TEXT" in members
        assert "HTML" in members


class TestStatusBarComponentIcon:
    def test_init(self, capsys):
        png_data = b"\x89PNG\r\n\x1a\n"
        b64 = base64.b64encode(png_data).decode()
        icon = iterm2.statusbar.StatusBarComponent.Icon(2.0, b64)
        proto = icon.to_status_bar_icon()
        assert proto.scale == 2.0
        assert proto.data == png_data


class TestStatusBarComponent:
    def test_init_defaults(self):
        comp = iterm2.statusbar.StatusBarComponent(
            short_description="Short",
            detailed_description="Detailed",
            knobs=[],
            exemplar="Example",
            update_cadence=None,
            identifier="com.test.comp"
        )
        proto = iterm2.api_pb2.RPCRegistrationRequest.StatusBarComponentAttributes()
        comp.set_fields_in_proto(proto)
        assert proto.short_description == "Short"
        assert proto.detailed_description == "Detailed"
        assert proto.exemplar == "Example"
        assert proto.unique_identifier == "com.test.comp"
        assert proto.format == iterm2.statusbar.StatusBarComponent.Format.PLAIN_TEXT.value

    def test_init_with_update_cadence(self):
        comp = iterm2.statusbar.StatusBarComponent(
            short_description="S",
            detailed_description="D",
            knobs=[],
            exemplar="E",
            update_cadence=5.0,
            identifier="com.test.comp2"
        )
        proto = iterm2.api_pb2.RPCRegistrationRequest.StatusBarComponentAttributes()
        comp.set_fields_in_proto(proto)
        assert proto.update_cadence == 5.0

    def test_init_with_html_format(self):
        comp = iterm2.statusbar.StatusBarComponent(
            short_description="S",
            detailed_description="D",
            knobs=[],
            exemplar="E",
            update_cadence=None,
            identifier="com.test.comp3",
            format=iterm2.statusbar.StatusBarComponent.Format.HTML
        )
        proto = iterm2.api_pb2.RPCRegistrationRequest.StatusBarComponentAttributes()
        comp.set_fields_in_proto(proto)
        assert proto.format == iterm2.statusbar.StatusBarComponent.Format.HTML.value

    def test_init_with_knobs(self):
        knob = iterm2.statusbar.CheckboxKnob("Toggle", True, "k1")
        comp = iterm2.statusbar.StatusBarComponent(
            short_description="S",
            detailed_description="D",
            knobs=[knob],
            exemplar="E",
            update_cadence=None,
            identifier="com.test.comp4"
        )
        proto = iterm2.api_pb2.RPCRegistrationRequest.StatusBarComponentAttributes()
        comp.set_fields_in_proto(proto)
        assert len(proto.knobs) == 1
        assert proto.knobs[0].key == "k1"

    def test_init_with_icons(self):
        png_data = b"\x89PNG\r\n\x1a\n"
        b64 = base64.b64encode(png_data).decode()
        icon = iterm2.statusbar.StatusBarComponent.Icon(1.0, b64)
        comp = iterm2.statusbar.StatusBarComponent(
            short_description="S",
            detailed_description="D",
            knobs=[],
            exemplar="E",
            update_cadence=None,
            identifier="com.test.comp5",
            icons=[icon]
        )
        proto = iterm2.api_pb2.RPCRegistrationRequest.StatusBarComponentAttributes()
        comp.set_fields_in_proto(proto)
        assert len(proto.icons) == 1
        assert proto.icons[0].scale == 1.0
