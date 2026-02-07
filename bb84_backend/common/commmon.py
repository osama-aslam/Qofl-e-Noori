import hashlib
import base64
from typing import List

def encode_key(bits: List[int]) -> str:
    """
    Packs a list of bits into bytes (8 bits per byte) and returns a base64 string.
    Significantly more space-efficient (approx 8x smaller).
    """
    if not bits:
        return ""

    # 1. Initialize with a 'sentinel' 1 to preserve leading zeros.
    #    Example: [0, 1] -> 101 (binary) -> 5 (decimal)
    num = 1
    for b in bits:
        num = (num << 1) | b

    # 2. Convert the integer to the minimum number of bytes needed.
    #    (num.bit_length() + 7) // 8 calculates the exact byte count.
    num_bytes = (num.bit_length() + 7) // 8
    data = num.to_bytes(num_bytes, byteorder='big')

    return base64.urlsafe_b64encode(data).decode('ascii')

def decode_key(encoded: str) -> List[int]:
    """
    Decodes a base64 string back into a list of bits, handling the bit-packing.
    """
    if not encoded:
        return []

    data = base64.urlsafe_b64decode(encoded)
    
    # 1. Convert bytes back to a large integer
    num = int.from_bytes(data, byteorder='big')

    # 2. Convert to binary string, strip '0b', and remove the leading sentinel '1'.
    #    bin(5) is '0b101', slicing [3:] gives '01'
    return [int(b) for b in bin(num)[3:]]

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()