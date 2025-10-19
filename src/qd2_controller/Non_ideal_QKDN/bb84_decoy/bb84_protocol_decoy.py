# networks-it-uc3m/quditto/Quditto-main/qd2_controller/src/qd2_controller/Non_ideal_QKDN/bb84_decoy/bb84_protocol_decoy.py

import netsquid as ns
import numpy as np
from ..bb84_decoy.sender_protocol import SenderProtocol
from ..bb84_decoy.receiver_protocol_decoy import ReceiverProtocol
from ..network import QKDNetwork
# Importar as novas funções matemáticas
from ..math_tools import estimate_single_photon_yield, estimate_single_photon_error_rate, decoy_state_secure_key_rate, H

def FULL_BB84_DECOY(PARAMETER_VALUES):
    """
    Executa uma simulação completa do BB84 com Decoy States.
    """
    ns.sim_reset()

    # Extrair parâmetros
    distance = PARAMETER_VALUES["distance"]
    key_size = PARAMETER_VALUES["required_length"]
    decoy_params = {
        'signal_intensity': PARAMETER_VALUES.get('signal_intensity', 0.5),
        'decoy_intensities': PARAMETER_VALUES.get('decoy_intensities', [0.1, 0.0]),
        'state_probabilities': PARAMETER_VALUES.get('state_probabilities', {'signal': 0.8, 'decoy_1': 0.1, 'decoy_2': 0.1})
    }

    # 1. Configurar a rede
    network = QKDNetwork(distance)
    alice_node, bob_node = network.get_nodes()

    # 2. Iniciar os protocolos
    sender_protocol = SenderProtocol(alice_node, key_size, decoy_params)
    receiver_protocol = ReceiverProtocol(bob_node, key_size)
    sender_protocol.start()
    receiver_protocol.start()
    
    # 3. Executar a simulação NetSquid
    stats = ns.sim_run()
    
    # 4. FASE DE PÓS-PROCESSAMENTO CLÁSSICO
    
    # Obter resultados da simulação
    alice_bits = sender_protocol.get_result("bits")
    alice_basis = sender_protocol.get_result("basis")
    alice_intensities = sender_protocol.get_result("intensities_log")
    bob_results = receiver_protocol.get_result("measurements")

    # Simular comunicação clássica: Alice anuncia bases e intensidades
    bob_sifted_bits = []
    alice_sifted_bits = []
    sifted_intensities = []

    for i in range(key_size):
        if bob_results[i] is not None:  # Se Bob detectou algo
            bob_basis, bob_bit = bob_results[i]
            if bob_basis == alice_basis[i]:
                # As bases coincidem, manter o bit
                bob_sifted_bits.append(bob_bit)
                alice_sifted_bits.append(alice_bits[i])
                sifted_intensities.append(alice_intensities[i])

    # 5. Análise dos Decoy States
    
    # Calcular yields e QBERs para cada tipo de estado
    results_by_intensity = {}
    all_intensities = [decoy_params['signal_intensity']] + decoy_params['decoy_intensities']

    for intensity in set(all_intensities):
        # Filtrar os bits por intensidade
        indices = [i for i, x in enumerate(sifted_intensities) if x == intensity]
        alice_bits_intensity = [alice_sifted_bits[i] for i in indices]
        bob_bits_intensity = [bob_sifted_bits[i] for i in indices]
        
        num_sent = alice_intensities.count(intensity)
        num_detected = len(alice_bits_intensity)
        
        if num_sent == 0:
            yield_val = 0
            qber_val = 0
        else:
            yield_val = num_detected / num_sent
            errors = sum(a != b for a, b in zip(alice_bits_intensity, bob_bits_intensity))
            qber_val = errors / num_detected if num_detected > 0 else 0
            
        results_by_intensity[intensity] = {'yield': yield_val, 'qber': qber_val}

    # Estimar Y1 e e1
    signal_intensity = decoy_params['signal_intensity']
    decoy_intensity = decoy_params['decoy_intensities'][0] # Usando o primeiro isca para a estimativa
    
    y1 = estimate_single_photon_yield(
        results_by_intensity[signal_intensity]['yield'],
        results_by_intensity[decoy_intensity]['yield'],
        signal_intensity,
        decoy_intensity
    )
    
    e1 = estimate_single_photon_error_rate(
        results_by_intensity[signal_intensity]['qber'],
        results_by_intensity[decoy_intensity]['qber'],
        results_by_intensity[signal_intensity]['yield'],
        results_by_intensity[decoy_intensity]['yield'],
        y1
    )

    # 6. Geração da chave final
    
    # Obter os bits que vieram dos pulsos de SINAL
    signal_indices = [i for i, x in enumerate(sifted_intensities) if x == signal_intensity]
    final_alice_raw_key = [alice_sifted_bits[i] for i in signal_indices]

    # Calcular a taxa de chave segura
    qber_signal = results_by_intensity[signal_intensity]['qber']
    f_ec = 1.1 # Eficiência da correção de erros (exemplo)
    
    secure_rate = decoy_state_secure_key_rate(y1, e1, qber_signal, H, f_ec)
    
    final_key_len = int(len(final_alice_raw_key) * secure_rate)
    
    if final_key_len > 0:
        # Em uma simulação real, aqui entrariam a correção de erros e a amplificação de privacidade.
        # Por simplicidade, vamos apenas truncar a chave.
        final_key = final_alice_raw_key[:final_key_len]
    else:
        final_key = []

    # Preparar a saída
    sim_stats = {"total_duration_s": ns.sim_time() / 1e9}
    
    return final_key, sim_stats