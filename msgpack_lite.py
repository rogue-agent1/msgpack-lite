#!/usr/bin/env python3
"""MessagePack encoder/decoder (subset). Zero dependencies."""
import struct, sys

def encode(obj):
    if obj is None: return b"\xc0"
    if isinstance(obj, bool): return b"\xc3" if obj else b"\xc2"
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
    if isinstance(obj, str):
        b = obj.encode("utf-8")
        if len(b) <= 31: return bytes([0xa0 | len(b)]) + b
        if len(b) <= 0xFF: return b"\xd9" + struct.pack("B", len(b)) + b
        return b"\xda" + struct.pack(">H", len(b)) + b
    if isinstance(obj, bytes):
        if len(obj) <= 0xFF: return b"\xc4" + struct.pack("B", len(obj)) + obj
        return b"\xc5" + struct.pack(">H", len(obj)) + obj
    if isinstance(obj, (list, tuple)):
        if len(obj) <= 15: header = bytes([0x90 | len(obj)])
        else: header = b"\xdc" + struct.pack(">H", len(obj))
        return header + b"".join(encode(item) for item in obj)
    if isinstance(obj, dict):
        if len(obj) <= 15: header = bytes([0x80 | len(obj)])
        else: header = b"\xde" + struct.pack(">H", len(obj))
        return header + b"".join(encode(k) + encode(v) for k, v in obj.items())
    raise TypeError(f"Cannot encode {type(obj)}")

def decode(data, offset=0):
    b = data[offset]
    if b == 0xc0: return None, offset+1
    if b == 0xc2: return False, offset+1
    if b == 0xc3: return True, offset+1
    if b <= 0x7f: return b, offset+1
    if b >= 0xe0: return struct.unpack_from("b", data, offset)[0], offset+1
    if b == 0xcc: return data[offset+1], offset+2
    if b == 0xcd: return struct.unpack_from(">H", data, offset+1)[0], offset+3
    if b == 0xce: return struct.unpack_from(">I", data, offset+1)[0], offset+5
    if b == 0xd0: return struct.unpack_from("b", data, offset+1)[0], offset+2
    if b == 0xd1: return struct.unpack_from(">h", data, offset+1)[0], offset+3
    if b == 0xd2: return struct.unpack_from(">i", data, offset+1)[0], offset+5
    if b == 0xd3: return struct.unpack_from(">q", data, offset+1)[0], offset+9
    if b == 0xcb: return struct.unpack_from(">d", data, offset+1)[0], offset+9
    if 0xa0 <= b <= 0xbf:
        n = b & 0x1f; return data[offset+1:offset+1+n].decode(), offset+1+n
    if b == 0xd9:
        n = data[offset+1]; return data[offset+2:offset+2+n].decode(), offset+2+n
    if b == 0xda:
        n = struct.unpack_from(">H", data, offset+1)[0]; return data[offset+3:offset+3+n].decode(), offset+3+n
    if b == 0xc4:
        n = data[offset+1]; return data[offset+2:offset+2+n], offset+2+n
    if b == 0xc5:
        n = struct.unpack_from(">H", data, offset+1)[0]; return data[offset+3:offset+3+n], offset+3+n
    if 0x90 <= b <= 0x9f:
        n = b & 0x0f; off = offset+1; items = []
        for _ in range(n): v, off = decode(data, off); items.append(v)
        return items, off
    if b == 0xdc:
        n = struct.unpack_from(">H", data, offset+1)[0]; off = offset+3; items = []
        for _ in range(n): v, off = decode(data, off); items.append(v)
        return items, off
    if 0x80 <= b <= 0x8f:
        n = b & 0x0f; off = offset+1; d = {}
        for _ in range(n): k, off = decode(data, off); v, off = decode(data, off); d[k] = v
        return d, off
    if b == 0xde:
        n = struct.unpack_from(">H", data, offset+1)[0]; off = offset+3; d = {}
        for _ in range(n): k, off = decode(data, off); v, off = decode(data, off); d[k] = v
        return d, off
    raise ValueError(f"Unknown byte 0x{b:02x}")

def loads(data): return decode(data, 0)[0]
def dumps(obj): return encode(obj)

if __name__ == "__main__":
    obj = {"name": "test", "values": [1, 2, 3], "flag": True}
    packed = dumps(obj)
    print(f"Packed: {len(packed)} bytes")
    unpacked = loads(packed)
    print(f"Unpacked: {unpacked}")
