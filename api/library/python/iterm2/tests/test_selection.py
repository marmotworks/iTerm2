import pytest
import iterm2.selection
import iterm2


class TestSelectionMode:
    def test_enum_values(self):
        assert iterm2.selection.SelectionMode.CHARACTER.value == 0
        assert iterm2.selection.SelectionMode.WORD.value == 1
        assert iterm2.selection.SelectionMode.LINE.value == 2
        assert iterm2.selection.SelectionMode.SMART.value == 3
        assert iterm2.selection.SelectionMode.BOX.value == 4
        assert iterm2.selection.SelectionMode.WHOLE_LINE.value == 5

    def test_from_proto_value(self):
        for mode in iterm2.selection.SelectionMode:
            proto_val = iterm2.selection.SelectionMode.to_proto_value(mode)
            result = iterm2.selection.SelectionMode.from_proto_value(proto_val)
            assert result == mode

    def test_to_proto_value(self):
        for mode in iterm2.selection.SelectionMode:
            proto_val = iterm2.selection.SelectionMode.to_proto_value(mode)
            assert isinstance(proto_val, int)


class TestSubSelection:
    def test_properties(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, True)
        assert ss.windowed_coord_range == wcr
        assert ss.mode == iterm2.selection.SelectionMode.CHARACTER
        assert ss.connected is True
        assert ss.windowedCoordRange == wcr

    def test_not_connected(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.WORD, False)
        assert ss.connected is False


class TestSelection:
    def test_empty(self):
        sel = iterm2.selection.Selection([])
        assert sel.sub_selections == []
        assert sel.subSelections == []

    def test_with_subselections(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss])
        assert len(sel.sub_selections) == 1
        assert sel.sub_selections[0] == ss

    def test_multiple_subselections(self):
        wcr1 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        wcr2 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 1), iterm2.util.Point(3, 1)))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, False)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.WORD, True)
        sel = iterm2.selection.Selection([ss1, ss2])
        assert len(sel.sub_selections) == 2


class TestSubSelectionProto:
    def test_proto_creation(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, True)
        proto = ss.proto
        assert proto.selection_mode == iterm2.selection.SelectionMode.to_proto_value(
            iterm2.selection.SelectionMode.CHARACTER)


class TestSubSelectionEnumerateRanges:
    def test_enumerate_single_line(self):
        ranges = []
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        ss.enumerate_ranges(lambda *args: ranges.append(args[0]))
        assert len(ranges) == 1

    def test_enumerate_windowed(self):
        ranges = []
        coord_range = iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 2))
        wcr = iterm2.util.WindowedCoordRange(coord_range, iterm2.util.Range(0, 80))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        ss.enumerate_ranges(lambda *args: ranges.append(args[0]))
        assert len(ranges) > 0
