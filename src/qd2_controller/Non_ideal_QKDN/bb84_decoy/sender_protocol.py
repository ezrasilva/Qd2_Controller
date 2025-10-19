# networks-it-uc3m/quditto/Quditto-main/qd2_controller/src/qd2_controller/Non_ideal_QKDN/bb84_decoy/sender_protocol.py

import numpy as np
from netsquid.protocols import NodeProtocol
from netsquid.components.qprogram import QuantumProgram
from netsquid.components.instructions import INSTR_INIT, INSTR_H, INSTR_X
from netsquid.qubits.qubitapi import create_qubits

# Reutilizando a classe base do BB84 original
from ..bb84.basic_protocol import BasicProtocol

class SenderProtocol(BasicProtocol):
    """
    Protocolo do emissor (Alice) para o BB84 com Decoy States.

    Este protocolo gera e envia qubits para o receptor, mas com uma novidade:
    cada pulso é enviado com uma intensidade (número médio de fotões) escolhida
    aleatoriamente entre um estado de "sinal" e vários estados "isca" (decoy).

    Parâmetros
    ----------
    node : netsquid.nodes.Node
        O nó no qual este protocolo está a ser executado.
    key_size : int
        O número de qubits a serem transmitidos na fase quântica.
    decoy_params : dict
        Um dicionário contendo os parâmetros para os decoy states.
        Exemplo:
        {
            'signal_intensity': 0.5,
            'decoy_intensities': [0.1, 0.0],
            'state_probabilities': {
                'signal': 0.8,
                'decoy_1': 0.1,
                'decoy_2': 0.1
            }
        }
    """
    def __init__(self, node, key_size, decoy_params):
        super().__init__(node, "SenderProtocol")
        self.key_size = key_size
        self.decoy_params = decoy_params
        self.bits = []
        self.basis = []
        # Nova lista para armazenar a intensidade de cada pulso
        self.intensities_log = []

    def run(self):
        """
        Executa o protocolo do emissor.
        """
        # 1. Preparar a escolha das intensidades com base nas probabilidades
        intensities = [self.decoy_params['signal_intensity']] + self.decoy_params['decoy_intensities']
        # As probabilidades devem corresponder à ordem das intensidades
        probs = [
            self.decoy_params['state_probabilities']['signal'],
            self.decoy_params['state_probabilities']['decoy_1'],
            self.decoy_params['state_probabilities']['decoy_2']
        ]

        for i in range(self.key_size):
            # 2. Lógica principal dos Decoy States: Sortear a intensidade para este pulso
            chosen_intensity = np.random.choice(intensities, p=probs)
            self.intensities_log.append(chosen_intensity)

            # 3. Lógica original do BB84: Gerar bit e base aleatórios
            bit = np.random.randint(2)
            base = np.random.randint(2)  # 0 para base Z, 1 para base X
            self.bits.append(bit)
            self.basis.append(base)

            # 4. Preparar e enviar o qubit
            # Aqui, a simulação do NetSquid precisaria de uma fonte que possa ser
            # configurada com uma intensidade específica. Vamos assumir que a
            # função `create_qubits` pode ser modificada ou que existe uma
            # fonte (Quantum Source) que aceita este parâmetro.
            # Para fins de exemplo, a lógica de preparação do estado é a mesma.
            
            qubit_program = QuantumProgram(num_qubits=1)
            q1, = qubit_program.get_qubit_indices(1)
            qubit_program.apply(INSTR_INIT, q1)
            if bit == 1:
                qubit_program.apply(INSTR_X, q1)
            if base == 1:
                qubit_program.apply(INSTR_H, q1)
            
            # Executar o programa no processador quântico do nó
            yield self.node.qmemory.execute_program(qubit_program)

            # Obter a referência ao qubit preparado
            qubit, = self.node.qmemory.pop([0])

            # **PONTO CRÍTICO DA IMPLEMENTAÇÃO**
            # A forma como o NetSquid simula o envio com uma intensidade específica
            # pode variar. Uma abordagem comum seria ter um componente de fonte
            # (Quantum Source) que, ao ser ativado, gera um estado com um número
            # de fotões seguindo uma distribuição de Poisson com a média `chosen_intensity`.
            # A linha seguinte representa este envio conceptual.
            self.node.ports["qout"].tx_output((qubit, chosen_intensity))

            # Aguardar confirmação (ACK) do receptor para controlar o fluxo (opcional,
            # mas bom para simulações síncronas)
            yield self.await_port_input(self.node.ports["cin"])
            
        # Após o envio, armazenar os resultados para a fase clássica
        self.set_result("bits", self.bits)
        self.set_result("basis", self.basis)
        self.set_result("intensities_log", self.intensities_log)