#!/usr/bin/env python3
"""msgpack_lite: Minimal MessagePack encoder/decoder."""
import struct, sys

def pack(obj):
    if obj is None: return b"\xc0"
    if obj is False: return b"\xc2"
    if obj is True: return b"\xc3"
    if isinstance(obj, int):
        if 0 <= obj <= 127: return struct.pack("B", obj)
        if -32 <= obj < 0: return struct.pack("b", obj)
        if 0 <= obj <= 0xFF: return b"\xcc" + struct.pack("B", obj)
        if 0 <= obj <= 0xFFFF: return b"\xcd" + struct.pack(">H", obj)
        if 0 <= obj <= 0xFFFFFFFF: return b"\xce" + struct.pack(">I", obj)
        if -128 <= obj < 0: return b"\xd0" + struct.pack("b", obj)
        if -32768 <= obj < 0: return b"\xd1" + struct.pack(">h", obj)
        if -2147483648 <= obj < 0: return b"\xd2" + struct.pack(">i", obj)
        return b"\xd3" + struct.pack(">q", obj)
    if isinstance(obj, float): return b"\xcb" + struct.pack(">d", obj)
    if isinstance(obj, str): obj = obj.encode()
    if isinstance(obj, bytes):
        n = len(obj)
        if n <= 31: return bytes([0xa0 | n]) + obj
        if n <= 0xFF: return b"\xd9" + struct.pack("B", n) + obj
        if n <= 0xFFFF: return b"\xda" + struct.pack(">H", n) + obj
        return b"\xdb" + struct.pack(">I", n) + obj
    if isinstance(obj, (list, tuple)):
        n = len(obj)
        if n <= 15: header = bytes([0x90 | n])
        elif n <= 0xFFFF: header = b"\xdc" + struct.pack(">H", n)
        else: header = b"\xdd" + struct.pack(">I", n)
        return header + b"".join(pack(i) for i in obj)
    if isinstance(obj, dict):
        n = len(obj)
        if n <= 15: header = bytes([0x80 | n])
        elif n <= 0xFFFF: header = b"\xde" + struct.pack(">H", n)
        else: header = b"\xdf" + struct.pack(">I", n)
        return header + b"".join(pack(k) + pack(v) for k, v in obj.items())
    raise TypeError(f"Cannot pack {type(obj)}")

def unpack(data, offset=0):
    b = data[offset]
    if b == 0xc0: return None, offset+1
    if b == 0xc2: return False, offset+1
    if b == 0xc3: return True, offset+1
    if b <= 0x7f: return b, offset+1
    if b >= 0xe0: return struct.unpack("b", bytes([b]))[0], offset+1
    if b == 0xcc: return data[offset+1], offset+2
    if b == 0xcd: return struct.unpack(">H", data[offset+1:offset+3])[0], offset+3
    if b == 0xce: return struct.unpack(">I", data[offset+1:offset+5])[0], offset+5
    if b == 0xd0: return struct.unpack("b", data[offset+1:offset+2])[0], offset+2
    if b == 0xd1: return struct.unpack(">h", data[offset+1:offset+3])[0], offset+3
    if b == 0xd2: return struct.unpack(">i", data[offset+1:offset+5])[0], offset+5
    if b == 0xd3: return struct.unpack(">q", data[offset+1:offset+9])[0], offset+9
    if b == 0xcb: return struct.unpack(">d", data[offset+1:offset+9])[0], offset+9
    if 0xa0 <= b <= 0xbf:
        n = b & 0x1f; return data[offset+1:offset+1+n], offset+1+n
    if b == 0xd9:
        n = data[offset+1]; return data[offset+2:offset+2+n], offset+2+n
    if b == 0xda:
        n = struct.unpack(">H", data[offset+1:offset+3])[0]; return data[offset+3:offset+3+n], offset+3+n
    if 0x90 <= b <= 0x9f:
        n = b & 0x0f; result = []; off = offset+1
        for _ in range(n): v, off = unpack(data, off); result.append(v)
        return result, off
    if 0xdc == b:
        n = struct.unpack(">H", data[offset+1:offset+3])[0]; result = []; off = offset+3
        for _ in range(n): v, off = unpack(data, off); result.append(v)
        return result, off
    if 0x80 <= b <= 0x8f:
        n = b & 0x0f; result = {}; off = offset+1
        for _ in range(n):
            k, off = unpack(data, off); v, off = unpack(data, off); result[k] = v
        return result, off
    raise ValueError(f"Unknown type byte: 0x{b:02x}")

def test():
    for val in [None, True, False, 0, 1, 127, 128, 255, 256, 65535, -1, -32, -33, -128, -129]:
        packed = pack(val)
        unpacked, _ = unpack(packed)
        assert unpacked == val, f"{val} -> {unpacked}"
    assert abs(unpack(pack(3.14))[0] - 3.14) < 1e-9
    # Strings/bytes
    v, _ = unpack(pack("hello"))
    assert v == b"hello"
    # Arrays
    v, _ = unpack(pack([1, 2, 3]))
    assert v == [1, 2, 3]
    # Maps
    v, _ = unpack(pack({"a": 1}))
    assert v == {b"a": 1}
    # Nested
    obj = {"list": [1, "two", None], "num": 42}
    v, _ = unpack(pack(obj))
    assert v[b"num"] == 42
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Usage: msgpack_lite.py test")
