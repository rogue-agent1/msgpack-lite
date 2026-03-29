from msgpack_lite import dumps, loads
for obj in [None, True, False, 0, 42, -10, 300, 3.14, "hello", b"\x01\x02", [1,2,3], {"a":1}]:
    assert loads(dumps(obj)) == obj, f"Failed for {obj}"
nested = {"key": [1, "two", {"three": 3}]}
assert loads(dumps(nested)) == nested
print("MsgPack tests passed")