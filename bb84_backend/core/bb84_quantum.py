import secrets
from typing import List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Optional: Post-quantum authentication
try:
    from dilithium import Dilithium, parameter_sets
    PQCRYPTO_AVAILABLE = True
except ImportError:
    PQCRYPTO_AVAILABLE = False

import secrets
from typing import List, Tuple, Dict
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Optional: Post-quantum authentication
try:
    from dilithium import Dilithium, parameter_sets
    PQCRYPTO_AVAILABLE = True
except ImportError:
    PQCRYPTO_AVAILABLE = False

def bb84_protocol(length: int = 128, authenticate: bool = False) -> Tuple[List[int], List[int], List[Dict]]:
    """
    Optimized BB84 protocol simulation returning keys and a visual log.
    """
    # 1. Generate all random bits and bases at once (Space: O(N))
    alice_bits = [secrets.randbits(1) for _ in range(length)]
    alice_bases = [secrets.choice(['Z', 'X']) for _ in range(length)]
    bob_bases = [secrets.choice(['Z', 'X']) for _ in range(length)]

    # 2. Vectorized Simulation: One circuit for all qubits (Time: O(1) overhead)
    qc = QuantumCircuit(length, length)
    for i in range(length):
        # Alice prepares state
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 'X':
            qc.h(i)
        
        # Bob measures in his basis
        if bob_bases[i] == 'X':
            qc.h(i)
        qc.measure(i, i)

    # Execute simulation once
    simulator = AerSimulator()
    job = simulator.run(qc, shots=1, memory=True)
    result = job.result()
    
    # Get the raw bitstring (Little Endian -> reverse to match list index)
    raw_measurements = result.get_memory()[0][::-1]
    bob_results = [int(bit) for bit in raw_measurements]

    # 3. Key Sifting
    # We identify which indices matched bases to extract the final key
    matching_indices = [i for i, (a, b) in enumerate(zip(alice_bases, bob_bases)) if a == b]
    key_alice = [alice_bits[i] for i in matching_indices]
    key_bob = [bob_results[i] for i in matching_indices]

    # 4. Generate Qubit History Log (For UI Visualization)
    # We only log the first 50 qubits to keep the return payload light for the UI
    qubit_log = []
    for i in range(min(length, 50)):
        # Determine status based on basis matching
        status = "MATCH" if alice_bases[i] == bob_bases[i] else "DISCARD"
        
        qubit_log.append({
            "index": i,
            "alice_bit": alice_bits[i],
            "alice_basis": alice_bases[i],
            "bob_basis": bob_bases[i],
            "bob_result": bob_results[i],
            "status": status
        })

    # 5. Post-quantum authentication (Optional)
    if authenticate and PQCRYPTO_AVAILABLE:
        public_data = "".join(alice_bases).encode("utf-8")
        dil = Dilithium(parameter_set=parameter_sets["Dilithium5"])
        pk, sk = dil.generate_keypair()
        signature = dil.sign(public_data, sk)
        if not dil.verify(public_data, signature, pk):
            raise ValueError("Post-quantum signature verification failed.")

    # Returns: Alice's Key, Bob's Key, and the History Log
    return key_alice, key_bob, qubit_log