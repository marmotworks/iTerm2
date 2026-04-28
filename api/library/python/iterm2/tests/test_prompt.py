import pytest
import iterm2.prompt
import iterm2.util


class TestPromptState:
    def test_enum_values(self):
        assert iterm2.prompt.PromptState.UNKNOWN.value == -1
        assert iterm2.prompt.PromptState.EDITING.value == 0
        assert iterm2.prompt.PromptState.RUNNING.value == 1
        assert iterm2.prompt.PromptState.FINISHED.value == 3

    def test_all_members_present(self):
        members = [m.name for m in iterm2.prompt.PromptState]
        assert "UNKNOWN" in members
        assert "EDITING" in members
        assert "RUNNING" in members
        assert "FINISHED" in members


class TestPrompt:
    def _make_proto(self, **kwargs):
        from iterm2.api_pb2 import GetPromptResponse
        proto = GetPromptResponse()
        proto.status = iterm2.api_pb2.GetPromptResponse.Status.Value("OK")
        proto.working_directory = "/tmp"
        proto.command = "ls -la"
        proto.prompt_state = iterm2.prompt.PromptState.RUNNING.value
        proto.unique_prompt_id = "prompt-123"
        proto.prompt_range.start.x = 0
        proto.prompt_range.start.y = 0
        proto.prompt_range.end.x = 10
        proto.prompt_range.end.y = 0
        proto.command_range.start.x = 11
        proto.command_range.start.y = 0
        proto.command_range.end.x = 20
        proto.command_range.end.y = 0
        proto.output_range.start.x = 0
        proto.output_range.start.y = 1
        proto.output_range.end.x = 79
        proto.output_range.end.y = 5
        for k, v in kwargs.items():
            setattr(proto, k, v)
        return proto

    def test_prompt_range(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.prompt_range
        assert isinstance(rng, iterm2.util.CoordRange)
        assert rng.start.x == 0
        assert rng.start.y == 0
        assert rng.end.x == 10
        assert rng.end.y == 0

    def test_command_range(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.command_range
        assert rng.start.x == 11
        assert rng.end.x == 20

    def test_output_range(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        rng = prompt.output_range
        assert rng.start.y == 1
        assert rng.end.y == 5

    def test_working_directory(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.working_directory == "/tmp"

    def test_command(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.command == "ls -la"

    def test_state(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.state == iterm2.prompt.PromptState.RUNNING

    def test_state_unknown_when_not_set(self):
        proto = self._make_proto()
        proto.ClearField("prompt_state")
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.state == iterm2.prompt.PromptState.UNKNOWN

    def test_unique_id(self):
        proto = self._make_proto()
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.unique_id == "prompt-123"

    def test_unique_id_none_when_not_set(self):
        proto = self._make_proto()
        proto.ClearField("unique_prompt_id")
        prompt = iterm2.prompt.Prompt(proto)
        assert prompt.unique_id is None


class TestPromptMonitorMode:
    def test_mode_values(self):
        assert iterm2.prompt.PromptMonitor.Mode.PROMPT.value is not None
        assert iterm2.prompt.PromptMonitor.Mode.COMMAND_START.value is not None
        assert iterm2.prompt.PromptMonitor.Mode.COMMAND_END.value is not None

    def test_all_modes_present(self):
        members = [m.name for m in iterm2.prompt.PromptMonitor.Mode]
        assert "PROMPT" in members
        assert "COMMAND_START" in members
        assert "COMMAND_END" in members
