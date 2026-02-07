import os
import sys
import time
import re
import json  # Added for reading metrics

# ----------------------------------------------------------------------------
# PATH CONFIGURATION
# ----------------------------------------------------------------------------
# Ensure we can import the backend modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from bb84_backend.logic.controller import encrypt_file_local, decrypt_file_local
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Critical Error: Backend modules not found. {e}")
    print("Ensure you are running this from the project root directory.")
    sys.exit(1)

# ----------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------------------------------
def print_slow(text, speed=0.01):
    """Prints text with a retro typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    print()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_file_content(prompt_text):
    """Safe file reading utility."""
    while True:
        path = input(f"Input {prompt_text}: ").strip().strip('"')
        if not path: return None, None
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return f.read(), path
            except Exception as e:
                print(f"Error: Could not read file: {e}")
        else:
            print(f"Warning: File not found. Try again.")

# ----------------------------------------------------------------------------
# MAIN WORKFLOWS
# ----------------------------------------------------------------------------
def run_encryption():
    print(f"\n--- ENCRYPTION MODE ---")
    file_bytes, file_path = get_file_content("Enter path to file to encrypt")
    if not file_bytes: return

    filename = os.path.basename(file_path)
    
    print(f"\n[*] Initializing Qofl-e-Noori Protocol...")
    print_slow("    > Generating random bitstreams...", 0.02)
    print_slow("    > Transmitting qubits via quantum channel...", 0.02)
    print_slow("    > Sifting bases and distilling key...", 0.02)

    try:
        # Call backend
        # Note: controller.py returns (encrypted_b64, key_b_str, qubit_log)
        result = encrypt_file_local(file_bytes, filename)
        
        # Handle unpacking based on your controller version
        if len(result) == 3:
            enc_data, key_b, _ = result
        else:
            enc_data, key_b = result

        # Stats
        print(f"\n[SUCCESS] Encryption Complete!")
        print(f"    - Total Qubits Used: 256")
        print(f"    - Final Key Length:  {len(key_b)} bits")
        
        # Save Outputs
        out_name = filename + ".qofl"
        with open(out_name, "w") as f:
            f.write(enc_data)
        
        key_name = filename + "_key.txt"
        with open(key_name, "w") as f:
            f.write(key_b)

        print(f"\nOutput Saved Encrypted File: {out_name}")
        print(f"Output Saved Secret Key:     {key_name}")
        print(f"Important: Keep the key file safe! You need it to decrypt.")

    except Exception as e:
        print(f"[ERROR] Encryption failed: {e}")

def run_decryption():
    print(f"\n--- DECRYPTION MODE ---")
    
    # 1. Get Encrypted File
    enc_bytes, enc_path = get_file_content("Enter path to .qofl encrypted file")
    if not enc_bytes: return

    # 2. Get Key
    print(f"\nInput How will you provide the key?")
    print("    1. Paste key string")
    print("    2. Load from file")
    choice = input("    Selection [1/2]: ").strip()

    key_b_str = ""
    if choice == "2":
        k_bytes, _ = get_file_content("Enter path to key file")
        if k_bytes:
            key_b_str = k_bytes.decode("utf-8").strip()
    else:
        key_b_str = input(f"    Input Paste Key B: ").strip()

    # Validate Key
    if not re.fullmatch(r"[01]+", key_b_str):
        print(f"[ERROR] Invalid Key Format. Must be binary (0s and 1s).")
        return

    print(f"\n[*] Verifying Integrity & Decrypting...")

    try:
        # Backend expects list of ints
        key_bits = [int(k) for k in key_b_str]
        
        # Decode bytes to string for backend if needed (controller expects string base64)
        enc_string = enc_bytes.decode("utf-8")
        
        data, metadata = decrypt_file_local(enc_string, key_bits)

        if data is None:
            print(f"[FAILED] Decryption Error: {metadata.get('error')}")
        else:
            orig_name = metadata.get("original_filename", "decrypted_file")
            
            # Auto-rename if file exists to prevent overwrite
            if os.path.exists(orig_name):
                base, ext = os.path.splitext(orig_name)
                orig_name = f"{base}_restored{ext}"

            with open(orig_name, "wb") as f:
                f.write(data)

            print(f"\n[SUCCESS] File Restored Successfully!")
            print(f"Output Saved as: {orig_name}")
            
            # --- METRICS DISPLAY ADDED HERE ---
            print(f"\n--- Decryption Report ---")
            metrics_file = "bb84_metrics.json"
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, "r") as f:
                        m = json.load(f)
                        print(f"Timestamp:            {m.get('Timestamp', 'N/A')}")
                        print(f"Decryption Time:      {m.get('Decryption Time (s)', 'N/A')} s")
                        print(f"HMAC Integrity Check: {m.get('HMAC Integrity Check', 'N/A')}")
                        print(f"Decrypted File Size:  {m.get('Decrypted File Size (bytes)', 'N/A')} bytes")
                except Exception as e:
                    print(f"Warning: Could not read metrics file: {e}")
            else:
                print("Metrics file not found.")
            # ----------------------------------

    except Exception as e:
        print(f"[ERROR] Critical failure: {e}")

# ----------------------------------------------------------------------------
# MAIN MENU
# ----------------------------------------------------------------------------
def main():
    clear_screen()
    print(f"  ============================================")
    print("     QOFL-E-NOORI | CLI v1.0                ")
    print("     Secure Information by Quantum Encryption ")
    print("  ============================================")

    while True:
        print("\nSelect Operation:")
        print("  1. Encrypt a File")
        print("  2. Decrypt a File")
        print("  3. Exit")
        
        choice = input(f"\n[root@qofl]~# ")

        if choice == "1":
            run_encryption()
        elif choice == "2":
            run_decryption()
        elif choice == "3":
            print("\nExiting secure session...")
            sys.exit(0)
        else:
            print(f"Invalid command.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nForce Quit detected. Goodbye.")
        sys.exit(0)