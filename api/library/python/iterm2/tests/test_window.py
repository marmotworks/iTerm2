import pytest
import iterm2.window
import iterm2


class TestCreateTabException:
    def test_exception_message(self):
        exc = iterm2.window.CreateTabException("tab failed")
        assert str(exc) == "tab failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.window.CreateTabException, Exception)


class TestCreateWindowException:
    def test_exception_message(self):
        exc = iterm2.window.CreateWindowException("window failed")
        assert str(exc) == "window failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.window.CreateWindowException, Exception)


class TestSetPropertyException:
    def test_exception_message(self):
        exc = iterm2.window.SetPropertyException("property failed")
        assert str(exc) == "property failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.window.SetPropertyException, Exception)


class TestGetPropertyException:
    def test_exception_message(self):
        exc = iterm2.window.GetPropertyException("get failed")
        assert str(exc) == "get failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.window.GetPropertyException, Exception)
