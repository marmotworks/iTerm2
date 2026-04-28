import pytest
import iterm2.transaction
import iterm2


class TestTransaction:
    def test_current_none_initially(self):
        iterm2.transaction.CURRENT_TRANSACTION = None
        assert iterm2.transaction.Transaction.current() is None

    def test_current_returns_transaction(self):
        iterm2.transaction.CURRENT_TRANSACTION = None
        conn = None
        txn = iterm2.transaction.Transaction(conn)
        old = iterm2.transaction.CURRENT_TRANSACTION
        iterm2.transaction.CURRENT_TRANSACTION = txn
        try:
            assert iterm2.transaction.Transaction.current() == txn
        finally:
            iterm2.transaction.CURRENT_TRANSACTION = old

    def test_connection_property(self):
        conn = object()
        txn = iterm2.transaction.Transaction(conn)
        assert txn.connection == conn
