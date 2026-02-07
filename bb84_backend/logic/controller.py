import os
import sys
import base64
import hashlib
import time
import json
from datetime import datetime
from math import log2
from typing import Tuple, Optional, List

import os
import sys
import base64
import hashlib
import time
import json
from datetime import datetime
from math import log2
from typing import Tuple, Optional, List, Dict

# Add core modules path for relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.bb84_quantum import bb84_protocol
from secure_io.secure_packager import save_encrypted_file, load_and_decrypt_bytes

class BB84MetricsCollector:
    def __init__(self):
        self.metrics = {}
        self.start_time = 0.0

    def start_timer(self):
        self.start_time = time.perf_counter()

    def stop_timer(self, label="Encryption Time (s)"):
        if self.start_time:
            self.metrics[label] = round(time.perf_counter() - self.start_time, 4)

    def add_timestamp(self):
        self.metrics["Timestamp"] = datetime.utcnow().isoformat()

    def add_key_metrics(self, key_a_bits: List[int], key_b_bits: List[int]):
        len_a = len(key_a_bits)
        len_b = len(key_b_bits)
        
        # Single pass optimization
        ones_b = 0
        matches = 0
        for a, b in zip(key_a_bits, key_b_bits):
            if b == 1: ones_b += 1
            if a == b: matches += 1

        self.metrics.update({
            "Key A Length": len_a,
            "Key B Length": len_b,
            "Key B - Count of 1s": ones_b,
            "Key B - Count of 0s": len_b - ones_b,
            "A/B Bit Match Percentage": round(100 * matches / len_b, 2) if len_b else 0
        })

        # Fast Shannon Entropy for Binary (Key A)
        ones_a = sum(key_a_bits)
        zeros_a = len_a - ones_a
        if len_a > 0:
            p1 = ones_a / len_a
            p0 = zeros_a / len_a
            entropy = 0.0
            if p1 > 0: entropy -= p1 * log2(p1)
            if p0 > 0: entropy -= p0 * log2(p0)
            self.metrics["Estimated Shannon Entropy"] = round(entropy, 4)

    def add_file_size_metric(self, label: str, data: bytes):
        self.metrics[label] = len(data)

    def add_sha256_hash(self, label: str, data: bytes):
        self.metrics[label] = hashlib.sha256(data).hexdigest()

    def add_hmac_verification(self, valid: bool):
        self.metrics["HMAC Integrity Check"] = "Passed" if valid else "Failed"

    def add_quantum_signature_status(self, enabled: bool):
        self.metrics["Post-Quantum Signature"] = "Enabled" if enabled else "Disabled"

    def export_to_json(self, output_path="bb84_metrics.json"):
        with open(output_path, "w") as f:
            json.dump(self.metrics, f, indent=2)

def encrypt_file_local(data: bytes, filename: str) -> Tuple[str, str, List[Dict]]:
    """
    Encrypts a file using BB84 keys and returns the payload + UI visualization data.
    """
    metrics = BB84MetricsCollector()
    metrics.start_timer()
    metrics.add_timestamp()
    metrics.add_file_size_metric("Original File Size (bytes)", data)

    # 1. BB84 Logic
    # UPDATED: Now captures 'qubit_log' from the protocol return values
    key_a_bits, key_b_bits, qubit_log = bb84_protocol(length=256, authenticate=True)

    # 2. Secure Packaging
    package_bytes = save_encrypted_file(
        plaintext=data,
        key_a_bits=key_a_bits,
        key_b_bits=key_b_bits,
        original_filename=filename
    )

    # 3. Metrics Recording
    metrics.stop_timer("Encryption Time (s)")
    metrics.add_key_metrics(key_a_bits, key_b_bits)
    metrics.add_file_size_metric("Encrypted File Size (bytes)", package_bytes)
    metrics.add_sha256_hash("SHA-256 Hash of Encrypted File", package_bytes)
    metrics.add_quantum_signature_status(True)
    metrics.export_to_json()

    # Returns: Encrypted Package (B64), Bob's Key (Str), and the Qubit Log (List[Dict])
    return (
        base64.b64encode(package_bytes).decode("ascii"), 
        "".join(map(str, key_b_bits)), 
        qubit_log
    )

def decrypt_file_local(data_base64: str, key_b_bits: List[int]) -> Tuple[Optional[bytes], Optional[dict]]:
    try:
        metrics = BB84MetricsCollector()
        metrics.start_timer()
        metrics.add_timestamp()

        encrypted_bytes = base64.b64decode(data_base64)
        data, metadata, integrity_ok = load_and_decrypt_bytes(encrypted_bytes, key_b_bits)

        metrics.stop_timer("Decryption Time (s)")
        metrics.add_hmac_verification(integrity_ok)
        metrics.add_sha256_hash("SHA-256 Hash of Encrypted File", encrypted_bytes)

        if data:
            metrics.add_file_size_metric("Decrypted File Size (bytes)", data)
            metrics.add_sha256_hash("SHA-256 Hash of Decrypted File", data)

        metrics.export_to_json()

        if not integrity_ok:
            return None, {"error": "Key B mismatch. Integrity verification failed."}

        return data, metadata
    except Exception as e:
        return None, {"error": str(e)}