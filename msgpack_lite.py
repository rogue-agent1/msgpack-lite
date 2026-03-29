#!/usr/bin/env python3
"""Minimal MessagePack encoder/decoder."""
import struct

def pack(obj) -> bytes:
    if obj is None: return b"\xc0"
    if obj is False: return b"\xc2"
    if obj is True: return b"\xc3"
    if isinstance(obj, int):
        if 0 <= obj <= 127: return struct.pack("B", obj)
        if -32 <= obj < 0: return struct.pack("b", obj)
        if 0 <= obj <= 0xff: return b"\xcc" + struct.pack("B", obj)
        if 0 <= obj <= 0xffff: return b"\xcd" + struct.pack(">H", obj)
        if 0 <= obj <= 0xffffffff: return b"\xce" + struct.pack(">I", obj)
        if -128 <= obj < 0: return b"\xd0" + struct.pack("b", obj)
        if -32768 <= obj < 0: return b"\xd1" + struct.pack(">h", obj)
        return b"\xd2" + struct.pack(">i", obj)
    if isinstance(obj, float):
        return b"\xcb" + struct.pack(">d", obj)
    if isinstance(obj, str):
        b = obj.encode()
        if len(b) <= 31: return struct.pack("B", 0xa0 | len(b)) + b
        return b"\xd9" + struct.pack("B", len(b)) + b
    if isinstance(obj, bytes):
        if len(obj) <= 0xff: return b"\xc4" + struct.pack("B", len(obj)) + obj
        return b"\xc5" + struct.pack(">H", len(obj)) + obj
    if isinstance(obj, (list, tuple)):
        if len(obj) <= 15: header = struct.pack("B", 0x90 | len(obj))
        else: header = b"\xdc" + struct.pack(">H", len(obj))
        return header + b"".join(pack(i) for i in obj)
    if isinstance(obj, dict):
        if len(obj) <= 15: header = struct.pack("B", 0x80 | len(obj))
        else: header = b"\xde" + struct.pack(">H", len(obj))
        return header + b"".join(pack(k) + pack(v) for k, v in obj.items())
    raise TypeError(f"Cannot pack {type(obj)}")

def unpack(data: bytes):
    val, _ = _unpack(data, 0)
    return val

def _unpack(data, pos):
    b = data[pos]
    if b == 0xc0: return None, pos+1
    if b == 0xc2: return False, pos+1
    if b == 0xc3: return True, pos+1
    if b <= 0x7f: return b, pos+1
    if b >= 0xe0: return struct.unpack("b", bytes([b]))[0], pos+1
    if b == 0xcc: return data[pos+1], pos+2
    if b == 0xcd: return struct.unpack(">H", data[pos+1:pos+3])[0], pos+3
    if b == 0xce: return struct.unpack(">I", data[pos+1:pos+5])[0], pos+5
    if b == 0xd0: return struct.unpack("b", data[pos+1:pos+2])[0], pos+2
    if b == 0xd1: return struct.unpack(">h", data[pos+1:pos+3])[0], pos+3
    if b == 0xd2: return struct.unpack(">i", data[pos+1:pos+5])[0], pos+5
    if b == 0xcb: return struct.unpack(">d", data[pos+1:pos+9])[0], pos+9
    if 0xa0 <= b <= 0xbf:
        n = b & 0x1f; return data[pos+1:pos+1+n].decode(), pos+1+n
    if b == 0xd9:
        n = data[pos+1]; return data[pos+2:pos+2+n].decode(), pos+2+n
    if b == 0xc4:
        n = data[pos+1]; return data[pos+2:pos+2+n], pos+2+n
    if b == 0xc5:
        n = struct.unpack(">H", data[pos+1:pos+3])[0]; return data[pos+3:pos+3+n], pos+3+n
    if 0x90 <= b <= 0x9f:
        n = b & 0x0f; pos += 1; items = []
        for _ in range(n): v, pos = _unpack(data, pos); items.append(v)
        return items, pos
    if b == 0xdc:
        n = struct.unpack(">H", data[pos+1:pos+3])[0]; pos += 3; items = []
        for _ in range(n): v, pos = _unpack(data, pos); items.append(v)
        return items, pos
    if 0x80 <= b <= 0x8f:
        n = b & 0x0f; pos += 1; d = {}
        for _ in range(n): k, pos = _unpack(data, pos); v, pos = _unpack(data, pos); d[k] = v
        return d, pos
    if b == 0xde:
        n = struct.unpack(">H", data[pos+1:pos+3])[0]; pos += 3; d = {}
        for _ in range(n): k, pos = _unpack(data, pos); v, pos = _unpack(data, pos); d[k] = v
        return d, pos
    raise ValueError(f"Unknown msgpack byte: 0x{b:02x}")

if __name__ == "__main__":
    obj = {"name": "test", "values": [1, 2.5, True, None]}
    packed = pack(obj)
    print(f"Packed ({len(packed)} bytes): {packed.hex()}")
    print(f"Unpacked: {unpack(packed)}")

def test():
    for obj in [None, True, False, 0, 1, 127, 128, 255, 256, 65535, -1, -32, -33, -128, -129,
                3.14, "", "hello", "x"*31, b"bytes", [], [1,2,3], {}, {"a": 1, "b": [2,3]}]:
        assert unpack(pack(obj)) == obj, f"Round-trip failed for {obj!r}"
    print("  msgpack_lite: ALL TESTS PASSED")
