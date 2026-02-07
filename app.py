import streamlit as st
import sys
import os
import time
import json
import base64
import re
from fpdf import FPDF

# ----------------------------------------------------------------------------
# PATH CONFIGURATION
# ----------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try importing backend
try:
    from bb84_backend.logic.controller import encrypt_file_local, decrypt_file_local
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

# ----------------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------------

def generate_pdf_report(metrics_path="bb84_metrics.json"):
    """Generates a PDF byte string from the metrics JSON."""
    if not os.path.exists(metrics_path):
        return None
    try:
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Qofl-e-Noori Metrics Report", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        for key, value in metrics.items():
            safe_val = str(value).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, f"{key}: {safe_val}", ln=True)
            
        return bytes(pdf.output(dest="S")) 
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def check_key_strength(key_b):
    """Returns a status string and color based on key bit balance."""
    ones = key_b.count('1')
    zeros = key_b.count('0')
    total = len(key_b)
    if total == 0: return "Empty", "red"
    balance = abs(ones - zeros)
    is_strong = balance < (total * 0.4)
    status = f"Strong (Balance: {balance})" if is_strong else f"Weak (Balance: {balance})"
    color = "green" if is_strong else "red"
    return f"1s: {ones} | 0s: {zeros} | Status: {status}", color

# ----------------------------------------------------------------------------
# STREAMLIT UI SETUP & AESTHETIC THEME
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="Qofl-e-Noori | PakQubit",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AESTHETIC GREEN THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #f4fcf6; }
    h1 { color: #1b5e20; }
    div.stButton > button {
        background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%);
        color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Qofl-e-Noori (قفلِ نوری)")
    st.title("Lock of Light")
    st.markdown("### 🌿 Secure Information by Quantum Encryption")
with col2:
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHerTw_y5Z8sM_g8GNJnmP6Qb1arhGJjKS1g&s", width=64)
    st.metric(label="Team Code", value="E")
    st.caption("Powered by **PakQubit**")

if not BACKEND_AVAILABLE:
    st.error("⚠️ Backend modules not found. Ensure 'bb84_backend' is in the python path.")

# --- TABS LAYOUT ---
tab_work, tab_team = st.tabs(["🔒 Main Work", "👥 About Team"])

# ==========================================
# TAB 1: MAIN WORK (Encryption/Decryption)
# ==========================================
with tab_work:
    mode = st.radio("Select Operation:", ["Encrypt File", "Decrypt File"], horizontal=True)
    st.divider()

    # --- ENCRYPTION LOGIC ---
    if mode == "Encrypt File":
        st.subheader("Quantum Encryption")
        uploaded_file = st.file_uploader("Upload a file to encrypt", type=None)
        
        if uploaded_file and BACKEND_AVAILABLE:
            if st.button("Start Qofl-e-Noori Protocol", type="primary"):
                
                # Visual Simulation
                progress_text = "Establishing Secure Quantum Channel..."
                my_bar = st.progress(0, text=progress_text)
                steps = [
                    "Initializing Quantum Channel...", "Alice generating random bits...",
                    "Bob choosing measurement bases...", "Transmitting qubits...",
                    "Sifting keys...", "Deriving AES-256 Key..."
                ]
                for p, step in enumerate(steps):
                    time.sleep(0.3)
                    my_bar.progress(int((p + 1) * (100/len(steps))), text=step)
                my_bar.empty()

                # Backend Execution
                try:
                    file_bytes = uploaded_file.getvalue()
                    filename = uploaded_file.name
                    
                    # Call backend (expects 3 return values: enc_data, key, qubit_log)
                    result = encrypt_file_local(file_bytes, filename)
                    
                    if len(result) == 3:
                        encrypted_data_b64, key_b, qubit_log = result
                    else:
                        encrypted_data_b64, key_b = result
                        qubit_log = []

                    st.session_state['last_key_b'] = key_b
                    st.session_state['last_encrypted_data'] = encrypted_data_b64
                    st.session_state['last_filename'] = filename + ".qofl" 
                    # We don't really need qubit_log in state anymore if not visualizing, 
                    # but keeping it doesn't hurt.
                    
                    st.success("File encrypted successfully!")
                    
                except Exception as e:
                    st.error(f"Encryption failed: {str(e)}")

        # Results Display
        if 'last_key_b' in st.session_state:
            st.markdown("---")
            
            # --- QUBIT STATS ONLY (Visualizer Removed) ---
            st.markdown("### ⚛️ Quantum Channel Stats")
            c_q1, c_q2, c_q3 = st.columns(3)
            with c_q1:
                st.metric("Total Qubits Transmitted", "256") # Hardcoded from controller config
            with c_q2:
                st.metric("Sifted Key Length", f"{len(st.session_state['last_key_b'])} bits")
            with c_q3:
                # Calculate match rate
                match_rate = round((len(st.session_state['last_key_b']) / 256) * 100, 1)
                st.metric("Basis Match Rate", f"{match_rate}%")
            
            st.markdown("---")

            # Key Display
            st.markdown("### 🔑 Generated Quantum Key (Bob's Key)")
            stats, color = check_key_strength(st.session_state['last_key_b'])
            st.info(f"**Key Analysis:** {stats}", icon="📊")
            st.code(st.session_state['last_key_b'], language="text")
            
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    label="💾 Download Key (.txt)",
                    data=st.session_state['last_key_b'],
                    file_name="key_b.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with c2:
                st.download_button(
                    label="📦 Download Encrypted Package",
                    data=st.session_state['last_encrypted_data'],
                    file_name=st.session_state['last_filename'],
                    mime="text/plain",
                    use_container_width=True
                )
            
            # ✅ METRICS PDF DOWNLOAD PRESERVED
            st.divider()
            if st.button("📄 Download Metrics Report (PDF)", type="secondary"):
                pdf_bytes = generate_pdf_report()
                if pdf_bytes:
                    st.download_button("Click to Save PDF", pdf_bytes, "metrics.pdf", "application/pdf")

    # --- DECRYPTION LOGIC ---
    elif mode == "Decrypt File":
        st.subheader("File Decryption")
        enc_file = st.file_uploader("Upload Encrypted Package", type=["qofl", "bb84", "txt"])
        
        st.markdown("#### Key Input")
        # ✅ KEY UPLOAD OPTION PRESERVED
        key_input_method = st.radio("Method:", ["Paste Key String", "Upload Key File"], horizontal=True)
        
        key_b_str = ""
        if key_input_method == "Paste Key String":
            key_b_str = st.text_input("Enter Key B (Binary String):", placeholder="e.g. 101010...")
        else:
            key_file = st.file_uploader("Upload Key File (.txt)", type=["txt"])
            if key_file:
                key_b_str = key_file.getvalue().decode("utf-8").strip()

        if enc_file and key_b_str and BACKEND_AVAILABLE:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Decrypt File", type="primary", use_container_width=True):
                if not re.fullmatch(r"[01]+", key_b_str):
                    st.error("❌ Invalid Key Format.")
                else:
                    try:
                        with st.spinner("Verifying Quantum Signature & Decrypting..."):
                            key_bits = [int(k) for k in key_b_str]
                            encrypted_content = enc_file.getvalue().decode("utf-8")
                            
                            data, metadata = decrypt_file_local(encrypted_content, key_bits)
                            
                            if data is None:
                                st.error(f"Decryption Failed: {metadata.get('error')}")
                            else:
                                st.success("✅ Decryption Successful!")
                                st.json(metadata, expanded=False)
                                
                                orig_name = metadata.get("original_filename", "decrypted_file")
                                st.download_button(
                                    label="💾 Download Decrypted File",
                                    data=data,
                                    file_name=orig_name,
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ==========================================
# TAB 2: ABOUT TEAM
# ==========================================
with tab_team:
    st.header("About the Team")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        ### 🌿 **Team PakQubit**
        **Team Code:** `E`  
        **Project:** Qofl-e-Noori
        
        We are dedicated to implementing next-generation quantum security protocols 
        to protect sensitive data against future threats.
        """)
    with col_b:
        st.success("💡 **Did you know?**\n\n'Qofl-e-Noori' translates to **'Lock of Light'**, symbolizing the use of photons.")

    st.markdown("---")
    st.info("Authorized Personnel Only | Team Code E | Secure Environment")