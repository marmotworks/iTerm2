import pytest
import iterm2.profile
import iterm2
import json


class TestBackgroundImageMode:
    def test_enum_values(self):
        assert iterm2.profile.BackgroundImageMode.STRETCH.value == 0
        assert iterm2.profile.BackgroundImageMode.TILE.value == 1
        assert iterm2.profile.BackgroundImageMode.ASPECT_FILL.value == 2
        assert iterm2.profile.BackgroundImageMode.ASPECT_FIT.value == 3

    def test_toJSON(self):
        for mode in iterm2.profile.BackgroundImageMode:
            result = mode.toJSON()
            assert json.loads(result) == mode.value


class TestBadGUIDException:
    def test_exception_message(self):
        exc = iterm2.profile.BadGUIDException("bad guid")
        assert str(exc) == "bad guid"

    def test_is_base_exception(self):
        assert issubclass(iterm2.profile.BadGUIDException, Exception)


class TestCursorType:
    def test_enum_values(self):
        assert iterm2.profile.CursorType.CURSOR_TYPE_UNDERLINE.value == 0
        assert iterm2.profile.CursorType.CURSOR_TYPE_VERTICAL.value == 1
        assert iterm2.profile.CursorType.CURSOR_TYPE_BOX.value == 2

    def test_toJSON(self):
        for ct in iterm2.profile.CursorType:
            result = ct.toJSON()
            assert json.loads(result) == ct.value


class TestThinStrokes:
    def test_enum_values(self):
        assert iterm2.profile.ThinStrokes.THIN_STROKES_SETTING_NEVER.value == 0
        assert iterm2.profile.ThinStrokes.THIN_STROKES_SETTING_RETINA_DARK_BACKGROUNDS_ONLY.value == 1
        assert iterm2.profile.ThinStrokes.THIN_STROKES_SETTING_DARK_BACKGROUNDS_ONLY.value == 2
        assert iterm2.profile.ThinStrokes.THIN_STROKES_SETTING_ALWAYS.value == 3
        assert iterm2.profile.ThinStrokes.THIN_STROKES_SETTING_RETINA_ONLY.value == 4

    def test_toJSON(self):
        for ts in iterm2.profile.ThinStrokes:
            result = ts.toJSON()
            assert json.loads(result) == ts.value


class TestUnicodeNormalization:
    def test_enum_values(self):
        assert iterm2.profile.UnicodeNormalization.UNICODE_NORMALIZATION_NONE.value == 0
        assert iterm2.profile.UnicodeNormalization.UNICODE_NORMALIZATION_NFC.value == 1
        assert iterm2.profile.UnicodeNormalization.UNICODE_NORMALIZATION_NFD.value == 2
        assert iterm2.profile.UnicodeNormalization.UNICODE_NORMALIZATION_HFSPLUS.value == 3

    def test_toJSON(self):
        for un in iterm2.profile.UnicodeNormalization:
            result = un.toJSON()
            assert json.loads(result) == un.value


class TestCharacterEncoding:
    def test_enum_values(self):
        assert iterm2.profile.CharacterEncoding.CHARACTER_ENCODING_UTF_8.value == 4

    def test_toJSON(self):
        for ce in iterm2.profile.CharacterEncoding:
            result = ce.toJSON()
            assert json.loads(result) == ce.value


class TestOptionKeySends:
    def test_enum_values(self):
        assert iterm2.profile.OptionKeySends.OPTION_KEY_NORMAL.value == 0
        assert iterm2.profile.OptionKeySends.OPTION_KEY_META.value == 1
        assert iterm2.profile.OptionKeySends.OPTION_KEY_ESC.value == 2

    def test_toJSON(self):
        for oks in iterm2.profile.OptionKeySends:
            result = oks.toJSON()
            assert json.loads(result) == oks.value


class TestInitialWorkingDirectory:
    def test_enum_values(self):
        assert iterm2.profile.InitialWorkingDirectory.INITIAL_WORKING_DIRECTORY_CUSTOM.value == "Yes"
        assert iterm2.profile.InitialWorkingDirectory.INITIAL_WORKING_DIRECTORY_HOME.value == "No"
        assert iterm2.profile.InitialWorkingDirectory.INITIAL_WORKING_DIRECTORY_RECYCLE.value == "Recycle"
        assert iterm2.profile.InitialWorkingDirectory.INITIAL_WORKING_DIRECTORY_ADVANCED.value == "Advanced"

    def test_toJSON(self):
        for iwd in iterm2.profile.InitialWorkingDirectory:
            result = iwd.toJSON()
            assert json.loads(result) == iwd.value


class TestIconMode:
    def test_enum_values(self):
        assert iterm2.profile.IconMode.NONE.value == 0
        assert iterm2.profile.IconMode.AUTOMATIC.value == 1
        assert iterm2.profile.IconMode.CUSTOM.value == 2

    def test_toJSON(self):
        for im in iterm2.profile.IconMode:
            result = im.toJSON()
            assert json.loads(result) == im.value


class TestTitleComponents:
    def test_enum_values(self):
        assert iterm2.profile.TitleComponents.SESSION_NAME.value == (1 << 0)
        assert iterm2.profile.TitleComponents.JOB.value == (1 << 1)
        assert iterm2.profile.TitleComponents.WORKING_DIRECTORY.value == (1 << 2)
        assert iterm2.profile.TitleComponents.TTY.value == (1 << 3)
        assert iterm2.profile.TitleComponents.CUSTOM.value == (1 << 4)
        assert iterm2.profile.TitleComponents.PROFILE_NAME.value == (1 << 5)
        assert iterm2.profile.TitleComponents.PROFILE_AND_SESSION_NAME.value == (1 << 6)
        assert iterm2.profile.TitleComponents.USER.value == (1 << 7)

    def test_toJSON(self):
        for tc in iterm2.profile.TitleComponents:
            result = tc.toJSON()
            assert json.loads(result) == tc.value
