import pytest
import iterm2.rpc
import iterm2


class TestRPCException:
    def test_exception_message(self):
        exc = iterm2.rpc.RPCException("rpc failed")
        assert str(exc) == "rpc failed"

    def test_is_base_exception(self):
        assert issubclass(iterm2.rpc.RPCException, Exception)


class TestConstants:
    def test_activate_raise_all_windows(self):
        assert iterm2.rpc.ACTIVATE_RAISE_ALL_WINDOWS == 1

    def test_activate_ignoring_other_apps(self):
        assert iterm2.rpc.ACTIVATE_IGNORING_OTHER_APPS == 2


class TestAllocId:
    def test_returns_increasing_ids(self):
        id1 = iterm2.rpc._alloc_id()
        id2 = iterm2.rpc._alloc_id()
        assert id2 == id1 + 1

    def test_returns_non_negative(self):
        val = iterm2.rpc._alloc_id()
        assert val >= 0


class TestAllocRequest:
    def test_returns_message(self):
        req = iterm2.rpc._alloc_request()
        assert req is not None

    def test_has_id(self):
        req = iterm2.rpc._alloc_request()
        assert req.id >= 0

    def test_ids_are_unique(self):
        req1 = iterm2.rpc._alloc_request()
        req2 = iterm2.rpc._alloc_request()
        assert req1.id != req2.id


class TestAssertNotInTransaction:
    def test_passes_outside_transaction(self):
        iterm2.rpc._assert_not_in_transaction()


class TestProfilePropertiesFromDict:
    def test_empty_dict(self):
        result = iterm2.rpc._profile_properties_from_dict({})
        assert result == []

    def test_single_property(self):
        result = iterm2.rpc._profile_properties_from_dict({"key1": "val1"})
        assert len(result) == 1
        assert result[0].key == "key1"
        assert result[0].json_value == "val1"

    def test_multiple_properties(self):
        result = iterm2.rpc._profile_properties_from_dict({"k1": "v1", "k2": "v2"})
        assert len(result) == 2
        props = {(p.key, p.json_value) for p in result}
        assert ("k1", "v1") in props
        assert ("k2", "v2") in props

    def test_json_value_preserved(self):
        result = iterm2.rpc._profile_properties_from_dict({"cfg": '{"a":1}'})
        assert len(result) == 1
        assert result[0].json_value == '{"a":1}'

    def test_returns_profile_property_objects(self):
        result = iterm2.rpc._profile_properties_from_dict({"k": "v"})
        assert isinstance(result[0], iterm2.api_pb2.ProfileProperty)
