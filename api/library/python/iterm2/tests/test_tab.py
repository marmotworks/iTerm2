import pytest
import iterm2.tab
import iterm2


class TestNavigationDirection:
    def test_enum_values(self):
        assert iterm2.tab.NavigationDirection.LEFT.value == "left"
        assert iterm2.tab.NavigationDirection.RIGHT.value == "right"
        assert iterm2.tab.NavigationDirection.ABOVE.value == "above"
        assert iterm2.tab.NavigationDirection.BELOW.value == "below"
