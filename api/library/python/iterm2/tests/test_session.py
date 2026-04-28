import pytest
import iterm2.session
import iterm2.util


class TestSplitPaneException:
    def test_exception_message(self):
        exc = iterm2.session.SplitPaneException("split failed")
        assert str(exc) == "split failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.session.SplitPaneException, Exception)


class TestInvalidSessionId:
    def test_exception_message(self):
        exc = iterm2.session.InvalidSessionId("bad id")
        assert str(exc) == "bad id"

    def test_is_base_exception(self):
        assert issubclass(iterm2.session.InvalidSessionId, Exception)


class TestSplitter:
    def test_init_horizontal(self):
        s = iterm2.session.Splitter()
        assert s.vertical is False
        assert s.children == []
        assert s.sessions == []

    def test_init_vertical(self):
        s = iterm2.session.Splitter(vertical=True)
        assert s.vertical is True

    def test_add_child(self):
        s = iterm2.session.Splitter()
        child = iterm2.session.Splitter(vertical=True)
        s.add_child(child)
        assert len(s.children) == 1
        assert s.children[0] is child

    def test_sessions_empty(self):
        s = iterm2.session.Splitter()
        assert s.sessions == []

    def test_sessions_nested(self):
        root = iterm2.session.Splitter(vertical=False)
        inner = iterm2.session.Splitter(vertical=True)
        root.add_child(inner)
        assert root.sessions == []
        assert inner.sessions == []

    def test_pretty_str_vertical(self):
        s = iterm2.session.Splitter(vertical=True)
        result = s.pretty_str("")
        assert "|" in result

    def test_pretty_str_horizontal(self):
        s = iterm2.session.Splitter(vertical=False)
        result = s.pretty_str("")
        assert "-" in result

    def test_update_session_not_found(self):
        s = iterm2.session.Splitter()
        result = s.update_session(None)
        assert result is False

    def test_to_protobuf(self):
        s = iterm2.session.Splitter(vertical=True)
        proto = s.to_protobuf()
        assert proto.vertical is True
        assert len(proto.links) == 0


class TestSessionLineInfo:
    def test_all_properties(self):
        info = iterm2.session.SessionLineInfo([24, 1000, 50, 10])
        assert info.mutable_area_height == 24
        assert info.scrollback_buffer_height == 1000
        assert info.overflow == 50
        assert info.first_visible_line_number == 10

    def test_zero_values(self):
        info = iterm2.session.SessionLineInfo([0, 0, 0, 0])
        assert info.mutable_area_height == 0
        assert info.scrollback_buffer_height == 0
        assert info.overflow == 0
        assert info.first_visible_line_number == 0


# ProxySession requires a live Connection, tested via integration tests.
