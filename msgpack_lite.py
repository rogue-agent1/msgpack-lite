#!/usr/bin/env python3
"""msgpack_lite - Minimal MessagePack encoder/decoder (subset)."""
import sys, struct

def pack(val):
    if val is None: return b"\xc0"
    if val is True: return b"\xc3"
    if val is False: return b"\xc2"
    if isinstance(val, int):
        if 0 <= val < 128: return struct.pack("B", val)
        if -32 <= val < 0: return struct.pack("b", val)
        if 0 <= val < 256: return b"\xcc" + struct.pack("B", val)
        if 0 <= val < 65536: return b"\xcd" + struct.pack(">H", val)
        if 0 <= val < 2**32: return b"\xce" + struct.pack(">I", val)
        if -128 <= val < 0: return b"\xd0" + struct.pack("b", val)
        if -32768 <= val < 0: return b"\xd1" + struct.pack(">h", val)
        return b"\xd2" + struct.pack(">i", val)
    if isinstance(val, str):
        b = val.encode("utf-8")
        if len(b) < 32: return bytes([0xa0 | len(b)]) + b
        return b"\xd9" + struct.pack("B", len(b)) + b
    if isinstance(val, list):
        if len(val) < 16: header = bytes([0x90 | len(val)])
        else: header = b"\xdc" + struct.pack(">H", len(val))
        return header + b"".join(pack(v) for v in val)
    if isinstance(val, dict):
        if len(val) < 16: header = bytes([0x80 | len(val)])
        else: header = b"\xde" + struct.pack(">H", len(val))
        return header + b"".join(pack(k) + pack(v) for k, v in val.items())
    raise TypeError(f"Cannot pack {type(val)}")

def unpack(data):
    val, _ = _unpack(data, 0)
    return val

def _unpack(data, i):
    b = data[i]
    if b == 0xc0: return None, i+1
    if b == 0xc2: return False, i+1
    if b == 0xc3: return True, i+1
    if b < 0x80: return b, i+1
    if b >= 0xe0: return struct.unpack("b", bytes([b]))[0], i+1
    if b == 0xcc: return data[i+1], i+2
    if b == 0xcd: return struct.unpack(">H", data[i+1:i+3])[0], i+3
    if b == 0xce: return struct.unpack(">I", data[i+1:i+5])[0], i+5
    if b == 0xd0: return struct.unpack("b", data[i+1:i+2])[0], i+2
    if b == 0xd1: return struct.unpack(">h", data[i+1:i+3])[0], i+3
    if b == 0xd2: return struct.unpack(">i", data[i+1:i+5])[0], i+5
    if 0xa0 <= b <= 0xbf:
        n = b & 0x1f
        return data[i+1:i+1+n].decode("utf-8"), i+1+n
    if b == 0xd9:
        n = data[i+1]
        return data[i+2:i+2+n].decode("utf-8"), i+2+n
    if 0x90 <= b <= 0x9f:
        n = b & 0x0f; lst = []; j = i+1
        for _ in range(n): v, j = _unpack(data, j); lst.append(v)
        return lst, j
    if b == 0xdc:
        n = struct.unpack(">H", data[i+1:i+3])[0]; lst = []; j = i+3
        for _ in range(n): v, j = _unpack(data, j); lst.append(v)
        return lst, j
    if 0x80 <= b <= 0x8f:
        n = b & 0x0f; d = {}; j = i+1
        for _ in range(n): k, j = _unpack(data, j); v, j = _unpack(data, j); d[k] = v
        return d, j
    raise ValueError(f"Unknown tag: 0x{b:02x}")

def test():
    for val in [None, True, False, 0, 42, -10, 1000, 65000, "hi", "hello world",
                [1, 2, 3], {"a": 1, "b": [True, None]}]:
        assert unpack(pack(val)) == val, f"Failed for {val}"
    assert len(pack(5)) == 1  # fixint
    assert len(pack("hi")) == 3  # fixstr
    print("msgpack_lite: all tests passed")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("Usage: msgpack_lite.py --test")
