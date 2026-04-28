import pytest
from unittest.mock import MagicMock, PropertyMock
import iterm2.screen
import iterm2
from iterm2.api_pb2 import CellStyle as ProtoCellStyle, RGBColor as ProtoRGBColor, URL as ProtoURL, AlternateColor as ProtoAlternateColor, ImagePlaceholderType as ProtoImagePlaceholderType


class TestCellStyleRGBColor:
    def test_rgb_components(self):
        proto = ProtoRGBColor()
        proto.red = 255
        proto.green = 128
        proto.blue = 64
        color = iterm2.screen.CellStyle.RGBColor(proto)
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 64


class TestCellStyleURL:
    def test_url_string(self):
        proto = ProtoURL()
        proto.url = "https://example.com"
        url = iterm2.screen.CellStyle.URL(proto)
        assert url.url == "https://example.com"

    def test_url_identifier_present(self):
        proto = ProtoURL()
        proto.url = "https://example.com"
        proto.identifier = "id123"
        url = iterm2.screen.CellStyle.URL(proto)
        assert url.identifier == "id123"

    def test_url_identifier_none(self):
        proto = ProtoURL()
        proto.url = "https://example.com"
        url = iterm2.screen.CellStyle.URL(proto)
        assert url.identifier is None


class TestCellStyleAlternateColor:
    def test_enum_values(self):
        assert iterm2.screen.CellStyle.AlternateColor.DEFAULT.value == ProtoAlternateColor.DEFAULT
        assert iterm2.screen.CellStyle.AlternateColor.REVERSED_DEFAULT.value == ProtoAlternateColor.REVERSED_DEFAULT
        assert iterm2.screen.CellStyle.AlternateColor.SYSTEM_MESSAGE.value == ProtoAlternateColor.SYSTEM_MESSAGE


class TestCellStyleColor:
    def test_standard_color(self):
        color = iterm2.screen.CellStyle.Color(standard=255)
        assert color.is_standard is True
        assert color.is_alternate is False
        assert color.is_rgb is False
        assert color.standard == 255

    def test_alternate_color(self):
        color = iterm2.screen.CellStyle.Color(alternate=iterm2.screen.CellStyle.AlternateColor.DEFAULT)
        assert color.is_alternate is True
        assert color.is_standard is False
        assert color.alternate == iterm2.screen.CellStyle.AlternateColor.DEFAULT

    def test_rgb_color(self):
        proto = ProtoRGBColor()
        proto.red = 100
        proto.green = 150
        proto.blue = 200
        rgb = iterm2.screen.CellStyle.RGBColor(proto)
        color = iterm2.screen.CellStyle.Color(rgb=rgb)
        assert color.is_rgb is True
        assert color.is_standard is False
        assert color.rgb == rgb
        assert color.rgb.red == 100

    def test_placement_color(self):
        color = iterm2.screen.CellStyle.Color(placement=42)
        assert color.placement == 42
        assert color.is_standard is False
        assert color.is_alternate is False
        assert color.is_rgb is False

    def test_standard_raises_when_not_standard(self):
        color = iterm2.screen.CellStyle.Color(alternate=iterm2.screen.CellStyle.AlternateColor.DEFAULT)
        with pytest.raises(ValueError, match="Not a standard color"):
            _ = color.standard

    def test_alternate_raises_when_not_alternate(self):
        color = iterm2.screen.CellStyle.Color(standard=10)
        with pytest.raises(ValueError, match="Not an alternate color"):
            _ = color.alternate

    def test_rgb_raises_when_not_rgb(self):
        color = iterm2.screen.CellStyle.Color(standard=10)
        with pytest.raises(ValueError, match="Not an RGB color"):
            _ = color.rgb

    def test_placement_raises_when_not_placement(self):
        color = iterm2.screen.CellStyle.Color(standard=10)
        with pytest.raises(ValueError, match="Not an alternate placement"):
            _ = color.placement


class TestCellStyleImagePlaceholderType:
    def test_enum_values(self):
        assert iterm2.screen.CellStyle.ImagePlaceholderType.NONE.value == ProtoImagePlaceholderType.NONE
        assert iterm2.screen.CellStyle.ImagePlaceholderType.ITERM2.value == ProtoImagePlaceholderType.ITERM2
        assert iterm2.screen.CellStyle.ImagePlaceholderType.KITTY.value == ProtoImagePlaceholderType.KITTY


class TestCellStyle:
    def _make_proto(self, **kwargs):
        proto = ProtoCellStyle()
        for k, v in kwargs.items():
            setattr(proto, k, v)
        return proto

    def test_repeats(self):
        proto = self._make_proto(repeats=5)
        style = iterm2.screen.CellStyle(proto)
        assert style.repeats == 5

    def test_fg_standard(self):
        proto = self._make_proto(fgStandard=255)
        style = iterm2.screen.CellStyle(proto)
        assert style.fg_color is not None
        assert style.fg_color.is_standard is True
        assert style.fg_color.standard == 255

    def test_fg_alternate(self):
        proto = self._make_proto(fgAlternate=ProtoAlternateColor.DEFAULT)
        style = iterm2.screen.CellStyle(proto)
        assert style.fg_color is not None
        assert style.fg_color.is_alternate is True

    def test_fg_rgb(self):
        proto = self._make_proto()
        proto.fgRgb.red = 100
        proto.fgRgb.green = 150
        proto.fgRgb.blue = 200
        style = iterm2.screen.CellStyle(proto)
        assert style.fg_color is not None
        assert style.fg_color.is_rgb is True

    def test_bg_standard(self):
        proto = self._make_proto(bgStandard=100)
        style = iterm2.screen.CellStyle(proto)
        assert style.bg_color is not None
        assert style.bg_color.is_standard is True

    def test_text_properties(self):
        proto = self._make_proto(
            bold=True, faint=True, italic=True, blink=True,
            underline=True, strikethrough=True, invisible=True,
            inverse=True, guarded=True)
        style = iterm2.screen.CellStyle(proto)
        assert style.bold is True
        assert style.faint is True
        assert style.italic is True
        assert style.blink is True
        assert style.underline is True
        assert style.strikethrough is True
        assert style.invisible is True
        assert style.inverse is True
        assert style.guarded is True

    def test_text_properties_default_false(self):
        proto = self._make_proto()
        style = iterm2.screen.CellStyle(proto)
        assert style.bold is False
        assert style.faint is False
        assert style.italic is False
        assert style.blink is False
        assert style.underline is False
        assert style.strikethrough is False
        assert style.invisible is False
        assert style.inverse is False
        assert style.guarded is False

    def test_image_none(self):
        proto = self._make_proto()
        style = iterm2.screen.CellStyle(proto)
        assert style.image is None

    def test_image_iterm2(self):
        proto = self._make_proto()
        proto.image = ProtoImagePlaceholderType.ITERM2
        style = iterm2.screen.CellStyle(proto)
        assert style.image == iterm2.screen.CellStyle.ImagePlaceholderType.ITERM2

    def test_url_none(self):
        proto = self._make_proto()
        style = iterm2.screen.CellStyle(proto)
        assert style.url is None

    def test_url_present(self):
        proto = self._make_proto()
        proto.url.url = "https://example.com"
        style = iterm2.screen.CellStyle(proto)
        assert style.url is not None
        assert style.url.url == "https://example.com"

    def test_block_id_none(self):
        proto = self._make_proto()
        style = iterm2.screen.CellStyle(proto)
        assert style.block_id is None

    def test_block_id_present(self):
        proto = self._make_proto()
        proto.blockID = "block123"
        style = iterm2.screen.CellStyle(proto)
        assert style.block_id == "block123"

    def test_underline_color_none(self):
        proto = self._make_proto()
        style = iterm2.screen.CellStyle(proto)
        assert style.underline_color is None

    def test_underline_color_present(self):
        proto = self._make_proto()
        proto.underlineColor.red = 255
        proto.underlineColor.green = 0
        proto.underlineColor.blue = 0
        style = iterm2.screen.CellStyle(proto)
        assert style.underline_color is not None
        assert style.underline_color.red == 255


class TestLineContents:
    def _make_proto(self, text="", **kwargs):
        proto = iterm2.api_pb2.LineContents()
        proto.text = text
        proto.continuation = iterm2.api_pb2.LineContents.Continuation.Value("CONTINUATION_HARD_EOL")
        for k, v in kwargs.items():
            setattr(proto, k, v)
        return proto

    def test_string(self):
        proto = self._make_proto(text="hello world")
        line = iterm2.screen.LineContents(proto)
        assert line.string == "hello world"

    def test_hard_eol_true(self):
        proto = self._make_proto()
        proto.continuation = iterm2.api_pb2.LineContents.Continuation.Value("CONTINUATION_HARD_EOL")
        line = iterm2.screen.LineContents(proto)
        assert line.hard_eol is True

    def test_hard_eol_false(self):
        proto = self._make_proto()
        proto.continuation = iterm2.api_pb2.LineContents.Continuation.Value("CONTINUATION_SOFT_EOL")
        line = iterm2.screen.LineContents(proto)
        assert line.hard_eol is False

    def test_string_at(self):
        proto = self._make_proto(text="hello")
        cppc = proto.code_points_per_cell.add()
        cppc.num_code_points = 1
        cppc.repeats = 5
        line = iterm2.screen.LineContents(proto)
        assert line.string_at(0) == "h"
        assert line.string_at(4) == "o"

    def test_style_at_out_of_range(self):
        proto = self._make_proto(text="hello")
        cppc = proto.code_points_per_cell.add()
        cppc.num_code_points = 1
        cppc.repeats = 5
        line = iterm2.screen.LineContents(proto)
        assert line.style_at(100) is None
        assert line.style_at(-1) is None


class TestScreenContents:
    def _make_proto(self):
        proto = iterm2.api_pb2.GetBufferResponse()
        proto.status = iterm2.api_pb2.GetBufferResponse.Status.Value("OK")
        proto.windowed_coord_range.coord_range.start.x = 0
        proto.windowed_coord_range.coord_range.start.y = 0
        proto.windowed_coord_range.coord_range.end.x = 79
        proto.windowed_coord_range.coord_range.end.y = 23
        proto.windowed_coord_range.columns.location = 0
        proto.windowed_coord_range.columns.length = 80
        proto.cursor.x = 10
        proto.cursor.y = 5
        proto.num_lines_above_screen = 100
        return proto

    def test_number_of_lines(self):
        proto = self._make_proto()
        proto.contents.add()
        proto.contents.add()
        contents = iterm2.screen.ScreenContents(proto)
        assert contents.number_of_lines == 2

    def test_cursor_coord(self):
        proto = self._make_proto()
        contents = iterm2.screen.ScreenContents(proto)
        assert contents.cursor_coord.x == 10
        assert contents.cursor_coord.y == 5

    def test_number_of_lines_above_screen(self):
        proto = self._make_proto()
        contents = iterm2.screen.ScreenContents(proto)
        assert contents.number_of_lines_above_screen == 100

    def test_windowed_coord_range(self):
        proto = self._make_proto()
        contents = iterm2.screen.ScreenContents(proto)
        wcr = contents.windowed_coord_range
        assert wcr.coordRange.start.x == 0
        assert wcr.coordRange.start.y == 0
        assert wcr.columnRange.location == 0
        assert wcr.columnRange.length == 80

    def test_line(self):
        proto = self._make_proto()
        line_proto = proto.contents.add()
        line_proto.text = "test line"
        cppc = line_proto.code_points_per_cell.add()
        cppc.num_code_points = 1
        cppc.repeats = 9
        contents = iterm2.screen.ScreenContents(proto)
        line = contents.line(0)
        assert line.string == "test line"
