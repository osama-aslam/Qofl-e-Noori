from typing import List
from hashlib import pbkdf2_hmac
import hmac
import os

def check_key_entropy(bits: List[int]) -> bool:
    """
    Optimized entropy check using native sum and length.
    """
    n = len(bits)
    if n == 0: return False
    # abs(ones - n/2) / n  =>  abs(2*ones - n) / (2*n)
    balance_ratio = abs(2 * sum(bits) - n) / (2 * n)
    return balance_ratio < 0.4

def bits_to_bytes(bits: List[int]) -> bytes:
    """
    Refactored to use bit-shifting instead of string joining.
    Eliminates O(N) string allocations.
    """
    n = len(bits)
    # Use bitwise math to calculate bytes needed
    byte_count = (n + 7) // 8
    result = bytearray(byte_count)
    
    for i, bit in enumerate(bits):
        if bit:
            # Set the bit in the correct byte using bitwise OR
            result[i // 8] |= (1 << (7 - (i % 8)))
            
    return bytes(result)

def bytes_to_bits(data: bytes) -> List[int]:
    """
    Refactored to use bit-masking instead of f-string formatting.
    """
    bits = [0] * (len(data) * 8)
    for i, byte in enumerate(data):
        for j in range(8):
            # Extract the j-th bit from the left
            bits[i * 8 + j] = (byte >> (7 - j)) & 1
    return bits

def derive_aes_key_from_bits(bits: List[int], salt: bytes = None, iterations: int = 100_000) -> bytes:
    """
    Derives 48-byte key + salt using PBKDF2.
    """
    # bits_to_bytes refactored above makes this much faster
    raw_material = bits_to_bytes(bits)
    salt = salt or os.urandom(16)
    key = pbkdf2_hmac('sha256', raw_material, salt, iterations, dklen=32)
    return key + salt

def verify_key_integrity(key_with_salt: bytes, bits: List[int], iterations: int = 100_000) -> bool:
    """
    Verifies key integrity using constant-time comparison.
    """
    if len(key_with_salt) < 48:
        return False
        
    salt = key_with_salt[32:48]
    # Recompute using the optimized bits_to_bytes
    expected_key = pbkdf2_hmac('sha256', bits_to_bytes(bits), salt, iterations, dklen=32)
    
    # hmac.compare_digest prevents timing attacks
    return hmac.compare_digest(key_with_salt[:32], expected_key)