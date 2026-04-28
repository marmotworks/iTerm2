import pytest
import iterm2.arrangement


class TestSavedArrangementException:
    def test_exception_message(self):
        exc = iterm2.arrangement.SavedArrangementException("error details")
        assert str(exc) == "error details"

    def test_exception_is_base_exception(self):
        assert issubclass(iterm2.arrangement.SavedArrangementException, Exception)


class TestArrangement:
    def test_class_exists(self):
        assert iterm2.arrangement.Arrangement is not None

    def test_async_save_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.arrangement.Arrangement.async_save)

    def test_async_restore_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.arrangement.Arrangement.async_restore)

    def test_async_list_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.arrangement.Arrangement.async_list)
