import pytest
from unittest.mock import MagicMock
import iterm2.capabilities


class TestGe:
    def test_major_greater(self):
        assert iterm2.capabilities.ge((2, 0), (1, 5)) is True

    def test_major_less(self):
        assert iterm2.capabilities.ge((1, 0), (2, 0)) is False

    def test_major_equal_minor_greater(self):
        assert iterm2.capabilities.ge((1, 5), (1, 3)) is True

    def test_major_equal_minor_less(self):
        assert iterm2.capabilities.ge((1, 3), (1, 5)) is False

    def test_equal(self):
        assert iterm2.capabilities.ge((1, 5), (1, 5)) is True

    def test_zero_version(self):
        assert iterm2.capabilities.ge((0, 69), (0, 68)) is True
        assert iterm2.capabilities.ge((0, 68), (0, 69)) is False


def _make_connection(version):
    conn = MagicMock()
    conn.iterm2_protocol_version = version
    return conn


class TestSupportsFunctions:
    def test_supports_multiple_set_profile_properties(self):
        assert iterm2.capabilities.supports_multiple_set_profile_properties(
            _make_connection((0, 69))) is True
        assert iterm2.capabilities.supports_multiple_set_profile_properties(
            _make_connection((0, 68))) is False

    def test_supports_select_pane_in_direction(self):
        assert iterm2.capabilities.supports_select_pane_in_direction(
            _make_connection((1, 0))) is True
        assert iterm2.capabilities.supports_select_pane_in_direction(
            _make_connection((0, 99))) is False

    def test_supports_prompt_monitor_modes(self):
        assert iterm2.capabilities.supports_prompt_monitor_modes(
            _make_connection((1, 1))) is True
        assert iterm2.capabilities.supports_prompt_monitor_modes(
            _make_connection((1, 0))) is False

    def test_supports_status_bar_unread_count(self):
        assert iterm2.capabilities.supports_status_bar_unread_count(
            _make_connection((1, 2))) is True
        assert iterm2.capabilities.supports_status_bar_unread_count(
            _make_connection((1, 1))) is False

    def test_supports_coprocesses(self):
        assert iterm2.capabilities.supports_coprocesses(
            _make_connection((1, 3))) is True
        assert iterm2.capabilities.supports_coprocesses(
            _make_connection((1, 2))) is False

    def test_supports_get_default_profile(self):
        assert iterm2.capabilities.supports_get_default_profile(
            _make_connection((1, 4))) is True
        assert iterm2.capabilities.supports_get_default_profile(
            _make_connection((1, 3))) is False

    def test_supports_prompt_id(self):
        assert iterm2.capabilities.supports_prompt_id(
            _make_connection((1, 5))) is True
        assert iterm2.capabilities.supports_prompt_id(
            _make_connection((1, 4))) is False

    def test_supports_list_saved_arrangements(self):
        assert iterm2.capabilities.supports_list_saved_arrangements(
            _make_connection((1, 6))) is True
        assert iterm2.capabilities.supports_list_saved_arrangements(
            _make_connection((1, 5))) is False

    def test_supports_context_menu_providers(self):
        assert iterm2.capabilities.supports_context_menu_providers(
            _make_connection((1, 7))) is True
        assert iterm2.capabilities.supports_context_menu_providers(
            _make_connection((1, 6))) is False

    def test_supports_add_annotation(self):
        assert iterm2.capabilities.supports_add_annotation(
            _make_connection((1, 8))) is True
        assert iterm2.capabilities.supports_add_annotation(
            _make_connection((1, 7))) is False

    def test_supports_advanced_key_notifications(self):
        assert iterm2.capabilities.supports_advanced_key_notifications(
            _make_connection((1, 9))) is True
        assert iterm2.capabilities.supports_advanced_key_notifications(
            _make_connection((1, 8))) is False

    def test_supports_file_panels(self):
        assert iterm2.capabilities.supports_file_panels(
            _make_connection((1, 10))) is True
        assert iterm2.capabilities.supports_file_panels(
            _make_connection((1, 9))) is False

    def test_supports_move_session(self):
        assert iterm2.capabilities.supports_move_session(
            _make_connection((1, 11))) is True
        assert iterm2.capabilities.supports_move_session(
            _make_connection((1, 10))) is False

    def test_supports_load_url(self):
        assert iterm2.capabilities.supports_load_url(
            _make_connection((1, 12))) is True
        assert iterm2.capabilities.supports_load_url(
            _make_connection((1, 11))) is False

    def test_supports_move_session_to_tab_or_window(self):
        assert iterm2.capabilities.supports_move_session_to_tab_or_window(
            _make_connection((1, 13))) is True
        assert iterm2.capabilities.supports_move_session_to_tab_or_window(
            _make_connection((1, 12))) is False


class TestCheckSupportsFunctions:
    def test_check_supports_coprocesses_ok(self):
        iterm2.capabilities.check_supports_coprocesses(
            _make_connection((1, 3)))

    def test_check_supports_coprocesses_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_coprocesses(
                _make_connection((1, 2)))

    def test_check_supports_get_default_profile_ok(self):
        iterm2.capabilities.check_supports_get_default_profile(
            _make_connection((1, 4)))

    def test_check_supports_get_default_profile_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_get_default_profile(
                _make_connection((1, 3)))

    def test_check_supports_prompt_id_ok(self):
        iterm2.capabilities.check_supports_prompt_id(
            _make_connection((1, 5)))

    def test_check_supports_prompt_id_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_prompt_id(
                _make_connection((1, 4)))

    def test_check_supports_list_saved_arrangements_ok(self):
        iterm2.capabilities.check_supports_list_saved_arrangements(
            _make_connection((1, 6)))

    def test_check_supports_list_saved_arrangements_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_list_saved_arrangements(
                _make_connection((1, 5)))

    def test_check_supports_context_menu_provider_ok(self):
        iterm2.capabilities.check_supports_context_menu_provider(
            _make_connection((1, 7)))

    def test_check_supports_context_menu_provider_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_context_menu_provider(
                _make_connection((1, 6)))

    def test_check_supports_add_annotation_ok(self):
        iterm2.capabilities.check_supports_add_annotation(
            _make_connection((1, 8)))

    def test_check_supports_add_annotation_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_add_annotation(
                _make_connection((1, 7)))

    def test_check_supports_advanced_key_notifications_ok(self):
        iterm2.capabilities.check_supports_advanced_key_notifications(
            _make_connection((1, 9)))

    def test_check_supports_advanced_key_notifications_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_advanced_key_notifications(
                _make_connection((1, 8)))

    def test_check_supports_file_panels_ok(self):
        iterm2.capabilities.check_supports_file_panels(
            _make_connection((1, 10)))

    def test_check_supports_file_panels_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_file_panels(
                _make_connection((1, 9)))

    def test_check_supports_move_session_ok(self):
        iterm2.capabilities.check_supports_move_session(
            _make_connection((1, 11)))

    def test_check_supports_move_session_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_move_session(
                _make_connection((1, 10)))

    def test_check_supports_load_url_ok(self):
        iterm2.capabilities.check_supports_load_url(
            _make_connection((1, 12)))

    def test_check_supports_load_url_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_load_url(
                _make_connection((1, 11)))

    def test_check_supports_move_session_to_tab_or_window_ok(self):
        iterm2.capabilities.check_supports_move_session_to_tab_or_window(
            _make_connection((1, 13)))

    def test_check_supports_move_session_to_tab_or_window_raises(self):
        with pytest.raises(iterm2.capabilities.AppVersionTooOld):
            iterm2.capabilities.check_supports_move_session_to_tab_or_window(
                _make_connection((1, 12)))
