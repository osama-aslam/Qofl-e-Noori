import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

__all__ = ["aes_encrypt", "aes_decrypt"]

def aes_encrypt(data: bytes, key_with_salt: bytes) -> bytes:
    """
    Refactored AES-256 CBC encryption.
    """
    # Slice once, avoid repeated salt indexing
    key = key_with_salt[:32]
    iv = os.urandom(16)

    # Use built-in PKCS7 for speed and side-channel resistance
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    
    # Return using a single join/concatenation to save memory overhead
    return iv + encryptor.update(padded_data) + encryptor.finalize()

def aes_decrypt(encrypted: bytes, key_with_salt: bytes) -> bytes:
    """
    Refactored AES-256 CBC decryption.
    """
    key = key_with_salt[:32]
    iv = encrypted[:16]
    ciphertext = encrypted[16:]

    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Efficient unpadding
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()