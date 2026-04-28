import pytest
import iterm2.registration
import iterm2


class TestReference:
    def test_init(self):
        ref = iterm2.registration.Reference("myVar")
        assert ref.name == "myVar"

    def test_repr(self):
        ref = iterm2.registration.Reference("myVar")
        assert repr(ref) == "myVar"

    def test_multiple_references(self):
        ref1 = iterm2.registration.Reference("id")
        ref2 = iterm2.registration.Reference("title")
        assert ref1.name == "id"
        assert ref2.name == "title"
        assert repr(ref1) == "id"
        assert repr(ref2) == "title"

    def test_reference_with_special_chars(self):
        ref = iterm2.registration.Reference("autoName?")
        assert ref.name == "autoName?"
        assert repr(ref) == "autoName?"


class TestRPCDecorator:
    def test_decorator_adds_async_register(self):
        @iterm2.registration.RPC
        async def my_func(x):
            return x

        assert hasattr(my_func, 'async_register')

    def test_decorator_preserves_function(self):
        @iterm2.registration.RPC
        async def my_func(x):
            return x * 2

        assert my_func.__name__ == "my_func"

    def test_decorator_with_no_args(self):
        @iterm2.registration.RPC
        async def no_args_func():
            return "ok"

        assert hasattr(no_args_func, 'async_register')
        assert no_args_func.__name__ == "no_args_func"

    def test_decorator_with_reference_default(self):
        @iterm2.registration.RPC
        async def with_ref(session_id=iterm2.Reference("id")):
            return session_id

        assert hasattr(with_ref, 'async_register')
        assert with_ref.__name__ == "with_ref"


class TestContextMenuProviderRPCDecorator:
    def test_decorator_adds_async_register(self):
        @iterm2.registration.ContextMenuProviderRPC
        async def my_context_menu(x):
            return x

        assert hasattr(my_context_menu, 'async_register')

    def test_decorator_preserves_function(self):
        @iterm2.registration.ContextMenuProviderRPC
        async def my_context_menu(x):
            return x

        assert my_context_menu.__name__ == "my_context_menu"


class TestTitleProviderRPCDecorator:
    def test_decorator_adds_async_register(self):
        @iterm2.registration.TitleProviderRPC
        async def my_title(x):
            return x

        assert hasattr(my_title, 'async_register')

    def test_decorator_preserves_function(self):
        @iterm2.registration.TitleProviderRPC
        async def my_title(x):
            return x

        assert my_title.__name__ == "my_title"


class TestStatusBarRPCDecorator:
    def test_decorator_adds_async_register(self):
        @iterm2.registration.StatusBarRPC
        async def my_status_bar(knobs):
            return "test"

        assert hasattr(my_status_bar, 'async_register')

    def test_decorator_preserves_function(self):
        @iterm2.registration.StatusBarRPC
        async def my_status_bar(knobs):
            return "test"

        assert my_status_bar.__name__ == "my_status_bar"


class TestGenericHandleRPC:
    def test_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.registration.generic_handle_rpc)
