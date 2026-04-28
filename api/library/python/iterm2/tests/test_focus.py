import pytest
import iterm2.focus
import iterm2


class TestFocusUpdateApplicationActive:
    def test_active_true(self):
        update = iterm2.focus.FocusUpdateApplicationActive(True)
        assert update.application_active is True

    def test_active_false(self):
        update = iterm2.focus.FocusUpdateApplicationActive(False)
        assert update.application_active is False


class TestFocusUpdateWindowChanged:
    def test_reason_enum(self):
        assert iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_BECAME_KEY.value == 0
        assert iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_IS_CURRENT.value == 1
        assert iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_RESIGNED_KEY.value == 2

    def test_properties(self):
        update = iterm2.focus.FocusUpdateWindowChanged(
            "win123",
            iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_BECAME_KEY)
        assert update.window_id == "win123"
        assert update.event == iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_BECAME_KEY

    def test_repr(self):
        update = iterm2.focus.FocusUpdateWindowChanged(
            "win123",
            iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_BECAME_KEY)
        assert "win123" in repr(update)
        assert "TERMINAL_WINDOW_BECAME_KEY" in repr(update)


class TestFocusUpdateSelectedTabChanged:
    def test_properties(self):
        update = iterm2.focus.FocusUpdateSelectedTabChanged("tab456")
        assert update.tab_id == "tab456"

    def test_repr(self):
        update = iterm2.focus.FocusUpdateSelectedTabChanged("tab456")
        assert "tab456" in repr(update)


class TestFocusUpdateActiveSessionChanged:
    def test_properties(self):
        update = iterm2.focus.FocusUpdateActiveSessionChanged("sess789")
        assert update.session_id == "sess789"

    def test_repr(self):
        update = iterm2.focus.FocusUpdateActiveSessionChanged("sess789")
        assert "sess789" in repr(update)


class TestFocusUpdate:
    def test_application_active(self):
        app_update = iterm2.focus.FocusUpdateApplicationActive(True)
        update = iterm2.focus.FocusUpdate(application_active=app_update)
        assert update.application_active == app_update
        assert update.window_changed is None
        assert update.selected_tab_changed is None
        assert update.active_session_changed is None

    def test_window_changed(self):
        reason = iterm2.focus.FocusUpdateWindowChanged.Reason.TERMINAL_WINDOW_BECAME_KEY
        win_update = iterm2.focus.FocusUpdateWindowChanged("win1", reason)
        update = iterm2.focus.FocusUpdate(window_changed=win_update)
        assert update.window_changed == win_update
        assert update.application_active is None

    def test_selected_tab_changed(self):
        tab_update = iterm2.focus.FocusUpdateSelectedTabChanged("tab1")
        update = iterm2.focus.FocusUpdate(selected_tab_changed=tab_update)
        assert update.selected_tab_changed == tab_update

    def test_active_session_changed(self):
        sess_update = iterm2.focus.FocusUpdateActiveSessionChanged("sess1")
        update = iterm2.focus.FocusUpdate(active_session_changed=sess_update)
        assert update.active_session_changed == sess_update

    def test_all_none(self):
        update = iterm2.focus.FocusUpdate()
        assert update.application_active is None
        assert update.window_changed is None
        assert update.selected_tab_changed is None
        assert update.active_session_changed is None

    def test_repr_application_active(self):
        app_update = iterm2.focus.FocusUpdateApplicationActive(True)
        update = iterm2.focus.FocusUpdate(application_active=app_update)
        assert "No Event" not in repr(update)

    def test_repr_no_event(self):
        update = iterm2.focus.FocusUpdate()
        assert repr(update) == "No Event"
