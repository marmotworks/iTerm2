import pytest
import iterm2.colorpresets
import iterm2.color


class TestExceptions:
    def test_list_presets_exception(self):
        exc = iterm2.colorpresets.ListPresetsException("msg")
        assert str(exc) == "msg"

    def test_get_preset_exception(self):
        exc = iterm2.colorpresets.GetPresetException("msg")
        assert str(exc) == "msg"


class TestColorPresetColor:
    def test_init_and_properties(self):
        color = iterm2.colorpresets.ColorPreset.Color(
            255, 128, 64, 255,
            iterm2.color.ColorSpace.SRGB,
            "foreground"
        )
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 64
        assert color.alpha == 255
        assert color.color_space == iterm2.color.ColorSpace.SRGB
        assert color.key == "foreground"

    def test_repr(self):
        color = iterm2.colorpresets.ColorPreset.Color(
            255, 128, 64, 255,
            iterm2.color.ColorSpace.SRGB,
            "fg"
        )
        r = repr(color)
        assert "fg" in r
        assert "255" in r
        assert "128" in r
        assert "64" in r
        assert "SRGB" in r


class TestColorPreset:
    def test_init_with_proto(self):
        proto = []
        preset = iterm2.colorpresets.ColorPreset(proto)
        assert preset.values == []

    def test_init_populates_values(self):
        setting = _make_color_setting(1.0, 0.5, 0.0, 1.0, "sRGB", "foreground")
        preset = iterm2.colorpresets.ColorPreset([setting])
        colors = preset.values
        assert len(colors) == 1
        assert colors[0].red == 255
        assert colors[0].green == 0.5 * 255
        assert colors[0].blue == 0
        assert colors[0].key == "foreground"

    def test_values_returns_list(self):
        settings = [
            _make_color_setting(1.0, 0.0, 0.0, 1.0, "sRGB", "fg"),
            _make_color_setting(0.0, 1.0, 0.0, 1.0, "sRGB", "bg"),
        ]
        preset = iterm2.colorpresets.ColorPreset(settings)
        assert len(preset.values) == 2


def _make_color_setting(r, g, b, a, cs, key):
    import iterm2.api_pb2 as pb
    resp = pb.ColorPresetResponse()
    resp.status = pb.ColorPresetResponse.Status.Value("OK")
    s = resp.get_preset.color_settings.add()
    s.red = r
    s.green = g
    s.blue = b
    s.alpha = a
    s.color_space = cs
    s.key = key
    return s
