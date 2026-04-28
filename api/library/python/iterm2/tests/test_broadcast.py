import pytest
from unittest.mock import MagicMock
import iterm2.broadcast
import iterm2


class TestBroadcastDomain:
    def test_init_empty(self):
        domain = iterm2.broadcast.BroadcastDomain()
        assert domain.sessions == []

    def test_add_session(self):
        domain = iterm2.broadcast.BroadcastDomain()
        session = MagicMock()
        session.session_id = "sess1"
        domain.add_session(session)
        assert len(domain.sessions) == 1
        assert domain.sessions[0] == session

    def test_add_multiple_sessions(self):
        domain = iterm2.broadcast.BroadcastDomain()
        s1 = MagicMock()
        s2 = MagicMock()
        domain.add_session(s1)
        domain.add_session(s2)
        assert len(domain.sessions) == 2

    def test_add_unresolved(self):
        domain = iterm2.broadcast.BroadcastDomain()
        ref = MagicMock()
        domain.add_unresolved(ref)

    def test_sessions_filters_none(self):
        domain = iterm2.broadcast.BroadcastDomain()
        session = MagicMock()
        domain.add_session(session)
        unresolved = MagicMock()
        unresolved.return_value = None
        domain.add_unresolved(unresolved)
        sessions = domain.sessions
        assert None not in sessions
        assert session in sessions

    def test_sessions_includes_unresolved_results(self):
        domain = iterm2.broadcast.BroadcastDomain()
        s1 = MagicMock()
        domain.add_session(s1)
        unresolved = MagicMock()
        s2 = MagicMock()
        unresolved.return_value = s2
        domain.add_unresolved(unresolved)
        sessions = domain.sessions
        assert s1 in sessions
        assert s2 in sessions
