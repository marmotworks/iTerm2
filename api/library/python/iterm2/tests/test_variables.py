import pytest
import iterm2.variables
import iterm2


class TestVariableScopes:
    def test_session(self):
        assert iterm2.variables.VariableScopes.SESSION.value == iterm2.api_pb2.VariableScope.Value("SESSION")

    def test_tab(self):
        assert iterm2.variables.VariableScopes.TAB.value == iterm2.api_pb2.VariableScope.Value("TAB")

    def test_window(self):
        assert iterm2.variables.VariableScopes.WINDOW.value == iterm2.api_pb2.VariableScope.Value("WINDOW")

    def test_app(self):
        assert iterm2.variables.VariableScopes.APP.value == iterm2.api_pb2.VariableScope.Value("APP")

    def test_all_scopes_exist(self):
        scopes = list(iterm2.variables.VariableScopes)
        assert len(scopes) == 4
        names = {s.name for s in scopes}
        assert names == {"SESSION", "TAB", "WINDOW", "APP"}


class TestVariableMonitor:
    def test_class_exists(self):
        assert iterm2.variables.VariableMonitor is not None

    def test_async_get_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(iterm2.variables.VariableMonitor.async_get)
