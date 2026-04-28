import pytest
import iterm2.auth


class TestAuthenticationException:
    def test_exception_message(self):
        exc = iterm2.auth.AuthenticationException("auth failed")
        assert str(exc) == "auth failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.auth.AuthenticationException, Exception)


class TestGetScriptName:
    def test_returns_path_or_string(self):
        name = iterm2.auth.get_script_name()
        assert len(str(name)) > 0

    def test_returns_unknown_when_no_file(self):
        import __main__
        original_file = getattr(__main__, "__file__", None)
        if hasattr(__main__, "__file__"):
            delattr(__main__, "__file__")
        import sys
        original_argv = sys.argv
        try:
            sys.argv = []
            name = iterm2.auth.get_script_name()
            assert name == "Unknown"
        finally:
            sys.argv = original_argv
            if original_file is not None:
                __main__.__file__ = original_file


class TestApplescriptAuthDisabled:
    def test_returns_false_when_file_not_exists(self):
        result = iterm2.auth.applescript_auth_disabled()
        assert result is False


class TestCommandLineApplescriptRunner:
    def test_init(self):
        runner = iterm2.auth.CommandLineApplescriptRunner('return "hello"')
        assert runner._script == b'return "hello"'
