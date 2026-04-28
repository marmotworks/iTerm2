import asyncio
import unittest.mock as mock

import pytest
import iterm2
import iterm2.selection
import iterm2.util
import iterm2.rpc


class TestSelectionModeInvalidProtoValue:
    def test_from_proto_value_invalid_raises_key_error(self):
        with pytest.raises(KeyError):
            iterm2.selection.SelectionMode.from_proto_value(999)

    def test_from_proto_value_negative_raises_key_error(self):
        with pytest.raises(KeyError):
            iterm2.selection.SelectionMode.from_proto_value(-1)


class TestSelectionModeMapCompleteness:
    def test_mode_map_has_all_modes(self):
        mode_map = iterm2.selection.MODE_MAP
        assert len(mode_map) == len(iterm2.selection.SelectionMode)

    def test_mode_map_values_are_selection_modes(self):
        mode_map = iterm2.selection.MODE_MAP
        for val in mode_map.values():
            assert isinstance(val, iterm2.selection.SelectionMode)

    def test_inverse_mode_map_has_all_modes(self):
        inverse = iterm2.selection.INVERSE_MODE_MAP
        assert len(inverse) == len(iterm2.selection.SelectionMode)

    def test_inverse_mode_map_keys_are_selection_modes(self):
        inverse = iterm2.selection.INVERSE_MODE_MAP
        for key in inverse.keys():
            assert isinstance(key, iterm2.selection.SelectionMode)

    def test_mode_map_and_inverse_are_consistent(self):
        mode_map = iterm2.selection.MODE_MAP
        inverse = iterm2.selection.INVERSE_MODE_MAP
        for proto_val, sel_mode in mode_map.items():
            assert inverse[sel_mode] == proto_val

    def test_mode_map_keys_are_proto_values(self):
        mode_map = iterm2.selection.MODE_MAP
        for key in mode_map.keys():
            assert isinstance(key, int)

    def test_character_in_mode_map(self):
        proto_char = iterm2.api_pb2.SelectionMode.Value("CHARACTER")
        assert proto_char in iterm2.selection.MODE_MAP
        assert iterm2.selection.MODE_MAP[proto_char] == iterm2.selection.SelectionMode.CHARACTER

    def test_word_in_mode_map(self):
        proto_word = iterm2.api_pb2.SelectionMode.Value("WORD")
        assert proto_word in iterm2.selection.MODE_MAP
        assert iterm2.selection.MODE_MAP[proto_word] == iterm2.selection.SelectionMode.WORD

    def test_line_in_mode_map(self):
        proto_line = iterm2.api_pb2.SelectionMode.Value("LINE")
        assert proto_line in iterm2.selection.MODE_MAP
        assert iterm2.selection.MODE_MAP[proto_line] == iterm2.selection.SelectionMode.LINE

    def test_smart_in_mode_map(self):
        proto_smart = iterm2.api_pb2.SelectionMode.Value("SMART")
        assert proto_smart in iterm2.selection.MODE_MAP
        assert iterm2.selection.MODE_MAP[proto_smart] == iterm2.selection.SelectionMode.SMART

    def test_box_in_mode_map(self):
        proto_box = iterm2.api_pb2.SelectionMode.Value("BOX")
        assert proto_box in iterm2.selection.MODE_MAP
        assert iterm2.selection.MODE_MAP[proto_box] == iterm2.selection.SelectionMode.BOX

    def test_whole_line_in_mode_map(self):
        proto_wl = iterm2.api_pb2.SelectionMode.Value("WHOLE_LINE")
        assert proto_wl in iterm2.selection.MODE_MAP
        assert iterm2.selection.MODE_MAP[proto_wl] == iterm2.selection.SelectionMode.WHOLE_LINE


class TestSubSelectionProtoRoundTrip:
    def test_proto_contains_windowed_coord_range(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(2, 3), iterm2.util.Point(7, 3)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.WORD, True)
        proto = ss.proto
        assert proto.windowed_coord_range.coord_range.start.x == 2
        assert proto.windowed_coord_range.coord_range.start.y == 3
        assert proto.windowed_coord_range.coord_range.end.x == 7
        assert proto.windowed_coord_range.coord_range.end.y == 3

    def test_proto_contains_selection_mode(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.BOX, False)
        proto = ss.proto
        assert proto.selection_mode == iterm2.selection.SelectionMode.to_proto_value(
            iterm2.selection.SelectionMode.BOX)

    def test_proto_with_windowed_range(self):
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0), iterm2.util.Point(10, 2))
        column_range = iterm2.util.Range(2, 8)
        wcr = iterm2.util.WindowedCoordRange(coord_range, column_range)
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.LINE, True)
        proto = ss.proto
        assert proto.windowed_coord_range.columns.location == 2
        assert proto.windowed_coord_range.columns.length == 8

    def test_proto_is_subselection_type(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        proto = ss.proto
        assert proto.DESCRIPTOR.name == "SubSelection"


class TestSubSelectionEnumerateRangesWindowed:
    def test_enumerate_multi_line_windowed(self):
        ranges = []
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(2, 0), iterm2.util.Point(5, 3))
        column_range = iterm2.util.Range(0, 80)
        wcr = iterm2.util.WindowedCoordRange(coord_range, column_range)
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        ss.enumerate_ranges(lambda *args: ranges.append(args[0]))

        assert len(ranges) == 4
        assert ranges[0].start.x == 2
        assert ranges[0].start.y == 0
        assert ranges[0].end.x == 80
        assert ranges[0].end.y == 0
        assert ranges[1].start.x == 0
        assert ranges[1].start.y == 1
        assert ranges[1].end.x == 80
        assert ranges[1].end.y == 1
        assert ranges[2].start.x == 0
        assert ranges[2].start.y == 2
        assert ranges[2].end.x == 80
        assert ranges[2].end.y == 2
        assert ranges[3].start.x == 0
        assert ranges[3].start.y == 3
        assert ranges[3].end.x == 5
        assert ranges[3].end.y == 3

    def test_enumerate_single_line_windowed(self):
        ranges = []
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(3, 5), iterm2.util.Point(10, 5))
        column_range = iterm2.util.Range(0, 80)
        wcr = iterm2.util.WindowedCoordRange(coord_range, column_range)
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        ss.enumerate_ranges(lambda *args: ranges.append(args[0]))

        assert len(ranges) == 1
        assert ranges[0].start.x == 3
        assert ranges[0].start.y == 5
        assert ranges[0].end.x == 10
        assert ranges[0].end.y == 5

    def test_enumerate_windowed_two_lines(self):
        ranges = []
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(5, 10), iterm2.util.Point(15, 11))
        column_range = iterm2.util.Range(0, 40)
        wcr = iterm2.util.WindowedCoordRange(coord_range, column_range)
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.WORD, True)
        ss.enumerate_ranges(lambda *args: ranges.append(args[0]))

        assert len(ranges) == 2
        assert ranges[0].start.x == 5
        assert ranges[0].start.y == 10
        assert ranges[0].end.x == 40
        assert ranges[0].end.y == 10
        assert ranges[1].start.x == 0
        assert ranges[1].start.y == 11
        assert ranges[1].end.x == 15
        assert ranges[1].end.y == 11


class TestSubSelectionEnumerateRangesUnwindowed:
    def test_enumerate_unwindowed_passes_self(self):
        received_self = []
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)

        def capture(*args):
            received_self.append(args)

        ss.enumerate_ranges(capture)
        assert len(received_self) == 1
        assert len(received_self[0]) == 2
        assert received_self[0][1] is ss

    def test_enumerate_unwindowed_coord_range(self):
        ranges = []
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(10, 3), iterm2.util.Point(20, 5)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.LINE, True)
        ss.enumerate_ranges(lambda *args: ranges.append(args[0]))

        assert len(ranges) == 1
        assert ranges[0].start.x == 10
        assert ranges[0].start.y == 3
        assert ranges[0].end.x == 20
        assert ranges[0].end.y == 5


class TestSubSelectionModes:
    def test_subselection_with_all_modes(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        for mode in iterm2.selection.SelectionMode:
            ss = iterm2.selection.SubSelection(wcr, mode, False)
            assert ss.mode == mode


class TestSelectionConnectedSubselections:
    def test_selection_with_connected_subselections(self):
        wcr1 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(10, 0)))
        wcr2 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(10, 0), iterm2.util.Point(20, 0)))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, True)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss1, ss2])
        assert sel.sub_selections[0].connected is True
        assert sel.sub_selections[1].connected is False

    def test_selection_all_connected(self):
        wcr1 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        wcr2 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(5, 0), iterm2.util.Point(10, 0)))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, True)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.CHARACTER, True)
        sel = iterm2.selection.Selection([ss1, ss2])
        assert all(ss.connected for ss in sel.sub_selections)

    def test_selection_all_disconnected(self):
        wcr1 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        wcr2 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 1), iterm2.util.Point(5, 1)))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, False)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss1, ss2])
        assert all(not ss.connected for ss in sel.sub_selections)


@pytest.mark.asyncio
class TestSelectionAsyncEnumerateRanges:
    async def test_empty_selection_no_callback(self):
        sel = iterm2.selection.Selection([])
        callback = mock.AsyncMock()
        await sel.async_enumerate_ranges(80, callback)
        callback.assert_not_called()

    async def test_single_subselection_windowed_callback_called(self):
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0), iterm2.util.Point(5, 0))
        wcr = iterm2.util.WindowedCoordRange(coord_range, iterm2.util.Range(0, 80))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss])
        callback = mock.AsyncMock(return_value=None)
        await sel.async_enumerate_ranges(80, callback)
        assert callback.call_count >= 1

    async def test_callback_receives_windowed_coord_range_and_bool(self):
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0), iterm2.util.Point(5, 0))
        wcr = iterm2.util.WindowedCoordRange(coord_range, iterm2.util.Range(0, 80))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss])

        received_args = []
        async def capture(wcr_arg, eol):
            received_args.append((wcr_arg, eol))
            return None

        await sel.async_enumerate_ranges(80, capture)
        assert len(received_args) >= 1
        for wcr_arg, eol in received_args:
            assert isinstance(wcr_arg, iterm2.util.WindowedCoordRange)
            assert isinstance(eol, bool)

    async def test_callback_returning_true_stops_enumeration(self):
        coord_range1 = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0), iterm2.util.Point(5, 0))
        coord_range2 = iterm2.util.CoordRange(
            iterm2.util.Point(0, 1), iterm2.util.Point(5, 1))
        wcr1 = iterm2.util.WindowedCoordRange(coord_range1, iterm2.util.Range(0, 80))
        wcr2 = iterm2.util.WindowedCoordRange(coord_range2, iterm2.util.Range(0, 80))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, False)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss1, ss2])

        call_count = 0
        async def stop_after_one(wcr_arg, eol):
            nonlocal call_count
            call_count += 1
            return True

        await sel.async_enumerate_ranges(80, stop_after_one)
        assert call_count == 1

    async def test_multiple_subselections_enumerated(self):
        coord_range1 = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0), iterm2.util.Point(5, 0))
        coord_range2 = iterm2.util.CoordRange(
            iterm2.util.Point(0, 1), iterm2.util.Point(5, 1))
        coord_range3 = iterm2.util.CoordRange(
            iterm2.util.Point(0, 2), iterm2.util.Point(5, 2))
        wcr1 = iterm2.util.WindowedCoordRange(coord_range1, iterm2.util.Range(0, 80))
        wcr2 = iterm2.util.WindowedCoordRange(coord_range2, iterm2.util.Range(0, 80))
        wcr3 = iterm2.util.WindowedCoordRange(coord_range3, iterm2.util.Range(0, 80))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, False)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.CHARACTER, False)
        ss3 = iterm2.selection.SubSelection(wcr3, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss1, ss2, ss3])

        ranges_collected = []
        async def collect(wcr_arg, eol):
            ranges_collected.append(wcr_arg.coordRange)
            return None

        await sel.async_enumerate_ranges(80, collect)
        assert len(ranges_collected) >= 1


@pytest.mark.asyncio
class TestSelectionAsyncGetString:
    async def test_single_subselection_delegates(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss])

        mock_ss_get = mock.AsyncMock(return_value="hello")
        with mock.patch.object(
            iterm2.selection.SubSelection,
            'async_get_string',
            mock_ss_get,
        ):
            result = await sel.async_get_string(mock.Mock(), "sess-1", 80)

        assert result == "hello"
        mock_ss_get.assert_called_once_with(mock.ANY, "sess-1")

    async def test_multiple_subselections_uses_enumerate(self):
        wcr1 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        wcr2 = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 1), iterm2.util.Point(5, 1)))
        ss1 = iterm2.selection.SubSelection(wcr1, iterm2.selection.SelectionMode.CHARACTER, False)
        ss2 = iterm2.selection.SubSelection(wcr2, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss1, ss2])

        mock_enumerate = mock.AsyncMock()
        with mock.patch.object(
            iterm2.selection.Selection,
            'async_enumerate_ranges',
            mock_enumerate,
        ):
            await sel.async_get_string(mock.Mock(), "sess-1", 80)

        mock_enumerate.assert_called_once()


@pytest.mark.asyncio
class TestSubSelectionAsyncGetString:
    async def test_ok_status_returns_string(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)

        from iterm2.api_pb2 import GetBufferResponse, ServerOriginatedMessage
        msg = ServerOriginatedMessage()
        msg.get_buffer_response.status = iterm2.api_pb2.GetBufferResponse.Status.Value("OK")

        mock_rpc = mock.AsyncMock(return_value=msg)
        with mock.patch.object(iterm2.rpc, 'async_get_screen_contents', mock_rpc):
            result = await ss.async_get_string(mock.Mock(), "sess-1")

        mock_rpc.assert_called_once()
        assert result == ""

    async def test_error_status_raises_rpc_exception(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)

        from iterm2.api_pb2 import GetBufferResponse, ServerOriginatedMessage
        msg = ServerOriginatedMessage()
        msg.get_buffer_response.status = iterm2.api_pb2.GetBufferResponse.Status.Value(
            "SESSION_NOT_FOUND")

        mock_rpc = mock.AsyncMock(return_value=msg)
        with mock.patch.object(iterm2.rpc, 'async_get_screen_contents', mock_rpc):
            with pytest.raises(iterm2.rpc.RPCException):
                await ss.async_get_string(mock.Mock(), "sess-1")


class TestSubSelectionDeprecatedAlias:
    def test_windowedCoordRange_alias(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        assert ss.windowedCoordRange is ss.windowed_coord_range


class TestSelectionDeprecatedAlias:
    def test_subSelections_alias(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        ss = iterm2.selection.SubSelection(
            wcr, iterm2.selection.SelectionMode.CHARACTER, False)
        sel = iterm2.selection.Selection([ss])
        assert sel.subSelections is sel.sub_selections


class TestRangeToSet:
    def test_range_to_set_deprecated_alias(self):
        r = iterm2.util.Range(0, 5)
        assert r.toSet == r.to_set

    def test_range_to_set_values(self):
        r = iterm2.util.Range(2, 3)
        assert r.to_set == {2, 3, 4}


class TestWindowedCoordRangeHasWindow:
    def test_has_window_deprecated_alias(self):
        coord_range = iterm2.util.CoordRange(
            iterm2.util.Point(0, 0), iterm2.util.Point(5, 0))
        column_range = iterm2.util.Range(0, 80)
        wcr = iterm2.util.WindowedCoordRange(coord_range, column_range)
        assert wcr.hasWindow == wcr.has_window

    def test_has_window_false_without_column_range(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)))
        assert wcr.has_window is False

    def test_has_window_true_with_column_range(self):
        wcr = iterm2.util.WindowedCoordRange(
            iterm2.util.CoordRange(iterm2.util.Point(0, 0), iterm2.util.Point(5, 0)),
            iterm2.util.Range(0, 80))
        assert wcr.has_window is True
