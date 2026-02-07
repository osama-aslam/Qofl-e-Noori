import json
import base64
import os
from typing import List, Tuple, Dict

# Core AES encryption and key utilities
from bb84_backend.core.aes_engine import aes_encrypt, aes_decrypt
from bb84_backend.core.key_utils import (
    derive_aes_key_from_bits,
    verify_key_integrity,
    bits_to_bytes
)

# Post-quantum logic remains as provided
try:
    from dilithium import Dilithium, DEFAULT_PARAMETERS
    ps = DEFAULT_PARAMETERS.get("dilithium5") or next(iter(DEFAULT_PARAMETERS.values()))
    dilithium_obj = Dilithium(parameter_set=ps)
    PQCRYPTO_AVAILABLE = True
except Exception as e:
    PQCRYPTO_AVAILABLE = False
    dilithium_obj = None

def _dilithium_keypair_pk_sk(dil) -> Tuple[bytes, bytes]:
    # Streamlined keypair generation
    seed = os.urandom(64)
    pk, sk = dil.keygen(seed)
    return bytes(pk), bytes(sk)

def save_encrypted_file(
    plaintext: bytes,
    key_a_bits: List[int],
    key_b_bits: List[int],
    original_filename: str = "file"
) -> bytes:
    # 1) Derive AES key
    key_with_salt = derive_aes_key_from_bits(key_a_bits)

    # 2) Build INTERNAL payload
    # Efficiently encode bits to bytes once
    key_a_bytes = bits_to_bytes(key_a_bits)
    
    internal_payload = {
        "file_bytes_b64": base64.b64encode(plaintext).decode("ascii"),
        "key_a_encoded": base64.b64encode(key_a_bytes).decode("ascii"),
        "original_filename": original_filename,
    }
    
    # 3) Encrypt INTERNAL payload
    internal_bytes = json.dumps(internal_payload, separators=(',', ':')).encode("utf-8")
    encrypted = aes_encrypt(internal_bytes, key_with_salt)

    # 4) Build OUTER package (Prepare for signing)
    package = {
        "ciphertext": base64.b64encode(encrypted).decode("ascii"),
        "salt": base64.b64encode(key_with_salt[32:]).decode("ascii"),
    }

    if not PQCRYPTO_AVAILABLE:
        raise RuntimeError("Dilithium module not available — cannot sign the package.")

    # 5) Post-quantum signing
    pk_bytes, sk_bytes = _dilithium_keypair_pk_sk(dilithium_obj)
    
    # Serialize exactly once for the signature
    unsigned_bytes = json.dumps(package, separators=(',', ':')).encode("utf-8")
    signature = dilithium_obj.sign_with_input(sk_bytes, unsigned_bytes)

    # 6) Final Assembly
    package["pq_signature"] = base64.b64encode(signature).decode("ascii")
    package["pq_public_key"] = base64.b64encode(pk_bytes).decode("ascii")

    return json.dumps(package, separators=(',', ':')).encode("utf-8")

def load_and_decrypt_bytes(
    package_bytes: bytes,
    key_b_bits: List[int]
) -> Tuple[bytes, Dict[str, str], bool]:
    # Parse OUTER package
    try:
        package = json.loads(package_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return b"", {}, False

    # 1) Verify post-quantum signature
    if PQCRYPTO_AVAILABLE and "pq_signature" in package:
        pq_sig = base64.b64decode(package["pq_signature"])
        pq_pk = base64.b64decode(package["pq_public_key"])

        # Reconstruct exactly as signed (removing signature keys)
        unsigned_package = package.copy()
        unsigned_package.pop("pq_signature", None)
        unsigned_package.pop("pq_public_key", None)
        unsigned_bytes = json.dumps(unsigned_package, separators=(',', ':')).encode("utf-8")

        if not dilithium_obj.verify(pq_pk, unsigned_bytes, pq_sig):
            return b"", {}, False
    else:
        return b"", {}, False

    # 2) Decrypt internal payload
    salt = base64.b64decode(package["salt"])
    candidate_key = derive_aes_key_from_bits(key_b_bits, salt)
    
    try:
        internal_bytes = aes_decrypt(base64.b64decode(package["ciphertext"]), candidate_key)
        internal = json.loads(internal_bytes)
        
        plaintext = base64.b64decode(internal["file_bytes_b64"])
        encoded_key_a = base64.b64decode(internal["key_a_encoded"])
    except Exception:
        return b"", {}, False

    # 3) Optimized bit reconstruction (Bit-shifting instead of f-string)
    # This is O(N) where N is bits; significantly faster for key verification.
    stored_key_a_bits = []
    for byte in encoded_key_a:
        for i in range(7, -1, -1):
            stored_key_a_bits.append((byte >> i) & 1)

    # 4) Final checks
    integrity_ok = verify_key_integrity(candidate_key, stored_key_a_bits)
    if not integrity_ok:
        return b"", {}, False

    metadata = {
        "original_filename": internal.get("original_filename", "decrypted_file"),
        "extension": internal.get("extension", "bin"),
    }

    return plaintext, metadata, True