import pytest
import iterm2.filepanel
import iterm2


class TestOpenPanelOptions:
    def test_all_options_exist(self):
        assert iterm2.filepanel.OpenPanel.Options.CAN_CREATE_DIRECTORIES.value == (1 << 0)
        assert iterm2.filepanel.OpenPanel.Options.TREATS_FILE_PACKAGES_AS_DIRECTORIES.value == (1 << 1)
        assert iterm2.filepanel.OpenPanel.Options.SHOWS_HIDDEN_FILES.value == (1 << 2)
        assert iterm2.filepanel.OpenPanel.Options.RESOLVES_ALIASES.value == (1 << 32)
        assert iterm2.filepanel.OpenPanel.Options.CAN_CHOOSE_DIRECTORIES.value == (1 << 33)
        assert iterm2.filepanel.OpenPanel.Options.ALLOWS_MULTIPLE_SELECTION.value == (1 << 34)
        assert iterm2.filepanel.OpenPanel.Options.CAN_CHOOSE_FILES.value == (1 << 35)


class TestOpenPanelResult:
    def test_files(self):
        result = iterm2.filepanel.OpenPanel.Result(["/a.txt", "/b.txt"])
        assert result.files == ["/a.txt", "/b.txt"]


class TestOpenPanel:
    def test_init_defaults(self):
        panel = iterm2.filepanel.OpenPanel()
        assert panel.path is None
        assert len(panel.options) == 1
        assert panel.options[0] == iterm2.filepanel.OpenPanel.Options(iterm2.filepanel.OpenPanel.Options.CAN_CHOOSE_FILES)
        assert panel.extensions is None
        assert panel.prompt is None
        assert panel.message is None

    def test_set_path(self):
        panel = iterm2.filepanel.OpenPanel()
        panel.path = "/tmp"
        assert panel.path == "/tmp"

    def test_set_options(self):
        panel = iterm2.filepanel.OpenPanel()
        panel.options = [iterm2.filepanel.OpenPanel.Options.CAN_CHOOSE_DIRECTORIES]
        assert panel.options == [iterm2.filepanel.OpenPanel.Options.CAN_CHOOSE_DIRECTORIES]

    def test_set_extensions(self):
        panel = iterm2.filepanel.OpenPanel()
        panel.extensions = ["txt", "md"]
        assert panel.extensions == ["txt", "md"]

    def test_set_prompt(self):
        panel = iterm2.filepanel.OpenPanel()
        panel.prompt = "Open"
        assert panel.prompt == "Open"

    def test_set_message(self):
        panel = iterm2.filepanel.OpenPanel()
        panel.message = "Select a file"
        assert panel.message == "Select a file"


class TestSavePanelOptions:
    def test_all_options_exist(self):
        assert iterm2.filepanel.SavePanel.Options.CAN_CREATE_DIRECTORIES.value == (1 << 0)
        assert iterm2.filepanel.SavePanel.Options.TREATS_FILE_PACKAGES_AS_DIRECTORIES.value == (1 << 1)
        assert iterm2.filepanel.SavePanel.Options.SHOWS_HIDDEN_FILES.value == (1 << 2)
        assert iterm2.filepanel.SavePanel.Options.ALLOWS_OTHER_FILE_TYPES.value == (1 << 3)
        assert iterm2.filepanel.SavePanel.Options.CAN_SELECT_HIDDEN_EXTENSION.value == (1 << 4)
        assert iterm2.filepanel.SavePanel.Options.EXTENSION_HIDDEN.value == (1 << 5)


class TestSavePanelResult:
    def test_file(self):
        result = iterm2.filepanel.SavePanel.Result("/path/to/file.txt")
        assert result.file == "/path/to/file.txt"


class TestSavePanel:
    def test_init_defaults(self):
        panel = iterm2.filepanel.SavePanel()
        assert panel.path is None
        assert panel.options == []
        assert panel.extensions is None
        assert panel.prompt is None
        assert panel.title is None
        assert panel.message is None
        assert panel.name_field_label is None
        assert panel.default_filename is None

    def test_setters(self):
        panel = iterm2.filepanel.SavePanel()
        panel.path = "/tmp"
        panel.options = [iterm2.filepanel.SavePanel.Options.CAN_CREATE_DIRECTORIES]
        panel.extensions = ["py"]
        panel.prompt = "Save"
        panel.title = "Save File"
        panel.message = "Subtitle"
        panel.name_field_label = "Name:"
        panel.default_filename = "default.py"
        assert panel.path == "/tmp"
        assert panel.options == [iterm2.filepanel.SavePanel.Options.CAN_CREATE_DIRECTORIES]
        assert panel.extensions == ["py"]
        assert panel.prompt == "Save"
        assert panel.title == "Save File"
        assert panel.message == "Subtitle"
        assert panel.name_field_label == "Name:"
        assert panel.default_filename == "default.py"
