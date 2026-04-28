import pytest
from unittest.mock import MagicMock, patch
import iterm2.alert
import iterm2


class TestAlert:
    def test_init_default_window(self):
        alert = iterm2.alert.Alert("Title", "Subtitle")
        assert alert.title == "Title"
        assert alert.subtitle == "Subtitle"
        assert alert.window_id is None

    def test_init_with_window(self):
        alert = iterm2.alert.Alert("Title", "Subtitle", "win123")
        assert alert.window_id == "win123"

    def test_add_button(self):
        alert = iterm2.alert.Alert("Title", "Subtitle")
        alert.add_button("OK")
        alert.add_button("Cancel")

    def test_properties_immutable(self):
        alert = iterm2.alert.Alert("Title", "Subtitle")
        assert alert.title == "Title"
        assert alert.subtitle == "Subtitle"


class TestTextInputAlert:
    def test_init_default_window(self):
        alert = iterm2.alert.TextInputAlert(
            "Title", "Subtitle", "Placeholder", "Default")
        assert alert.title == "Title"
        assert alert.subtitle == "Subtitle"
        assert alert.placeholder == "Placeholder"
        assert alert.default_value == "Default"
        assert alert.defaultValue == "Default"
        assert alert.window_id is None

    def test_init_with_window(self):
        alert = iterm2.alert.TextInputAlert(
            "Title", "Subtitle", "Placeholder", "Default", "win123")
        assert alert.window_id == "win123"


class TestPolyModalResult:
    def test_default(self):
        result = iterm2.alert.PolyModalResult()
        assert result.button is None
        assert result.tf_text is None
        assert result.combo is None
        assert result.checks is None

    def test_with_values(self):
        result = iterm2.alert.PolyModalResult(
            button="OK", tf_text="hello", combo="opt1", checks=["c1", "c2"])
        assert result.button == "OK"
        assert result.tf_text == "hello"
        assert result.combo == "opt1"
        assert result.checks == ["c1", "c2"]

    def test_from_dict(self):
        result = iterm2.alert.PolyModalResult(**{"button": "OK", "checks": ["a"]})
        assert result.button == "OK"
        assert result.checks == ["a"]


class TestPolyModalAlert:
    def test_init_default(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        assert alert.title == "Title"
        assert alert.subtitle == "Subtitle"
        assert alert.window_id is None
        assert alert.width == 300
        assert alert.checkboxes == []
        assert alert.checkbox_defaults == []
        assert alert.combobox_items == []
        assert alert.combobox_default == ""
        assert alert.text_field == []

    def test_init_with_window(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle", "win123")
        assert alert.window_id == "win123"

    def test_add_button(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_button("OK")
        alert.add_button("Cancel")

    def test_add_checkbox_item(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_checkbox_item("Option 1", 1)
        alert.add_checkbox_item("Option 2", 0)
        assert alert.checkboxes == ["Option 1", "Option 2"]
        assert alert.checkbox_defaults == [1, 0]

    def test_add_checkboxes(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_checkboxes(["A", "B", "C"], [1, 0, 1])
        assert alert.checkboxes == ["A", "B", "C"]
        assert alert.checkbox_defaults == [1, 0, 1]

    def test_add_checkboxes_mismatch_raises(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        with pytest.raises(AssertionError):
            alert.add_checkboxes(["A", "B"], [1])

    def test_add_combobox(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_combobox(["A", "B", "C"], "B")
        assert alert.combobox_items == ["A", "B", "C"]
        assert alert.combobox_default == "B"

    def test_add_combobox_no_default(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_combobox(["A", "B", "C"])
        assert alert.combobox_items == ["A", "B", "C"]
        assert alert.combobox_default == ""

    def test_add_combobox_invalid_default_raises(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        with pytest.raises(AssertionError):
            alert.add_combobox(["A", "B"], "C")

    def test_set_combobox_items(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.set_combobox_items(["A", "B", "C"], 1)
        assert alert.combobox_items == ["A", "B", "C"]
        assert alert.combobox_default == "B"

    def test_set_combobox_items_out_of_range_raises(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        with pytest.raises(AssertionError):
            alert.set_combobox_items(["A", "B"], 5)

    def test_add_combobox_item(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_combobox_item("A")
        alert.add_combobox_item("B", is_default=True)
        alert.add_combobox_item("C")
        assert alert.combobox_items == ["A", "B", "C"]
        assert alert.combobox_default == "B"

    def test_add_text_field(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        alert.add_text_field("Enter name", "John")
        assert alert.text_field == ["Enter name", "John"]

    def test_width_setter(self):
        alert = iterm2.alert.PolyModalAlert("Title", "Subtitle")
        assert alert.width == 300
        alert.width = 500
        assert alert.width == 500
