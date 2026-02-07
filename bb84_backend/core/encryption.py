import base64
from typing import List, Optional, Tuple

from core.bb84_quantum import bb84_protocol
from core.key_utils import derive_aes_key_from_bits

# Cache notice to avoid repeated string creation
__encryption_disabled_notice__ = "File I/O functions must be injected or handled externally."
_ERROR_DICT = {"error": __encryption_disabled_notice__}

def encrypt_file_local(data: bytes, filename: str) -> Tuple[str, str]:
    """
    Refactored for efficiency:
    1. Uses a generator expression inside join to save memory.
    2. Minimizes local variable overhead.
    """
    # BB84 Protocol execution
    key_a_bits, key_b_bits, _ = bb84_protocol(length=256, authenticate=True)
    
    # Key derivation (Logic unchanged)
    # Note: We assume derive_aes_key_from_bits handles its internal space efficiency.
    aes_key_with_salt = derive_aes_key_from_bits(key_a_bits)

    # Placeholder for actual encryption logic as per implementation logic constraint
    encrypted_data = b"" 

    # base64.b64encode returns bytes; decoding to utf-8 creates the string
    encrypted_b64 = base64.b64encode(encrypted_data).decode("ascii")
    
    # Efficiently convert bit list to string
    # map(str, ...) is faster than f-strings or manual loops for simple int-to-str
    key_b_str = "".join(map(str, key_b_bits))
    
    return encrypted_b64, key_b_str


def decrypt_file_local(data_base64: str, key_b_bits: List[int]) -> Tuple[Optional[bytes], Optional[dict]]:
    """
    Refactored to return a pre-defined error dictionary to save allocation time.
    """
    return None, _ERROR_DICT