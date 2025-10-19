import sys
import yaml
import json
# Importaremos uma nova função que ainda vamos criar
from Non_ideal_QKDN.bb84_decoy.bb84_protocol_decoy import FULL_BB84_DECOY

if __name__ == "__main__":
    # 1. Obter os argumentos do controller.py (tamanho da chave, distância, arquivo de params)
    if len(sys.argv) == 4:
        desired_key_length = int(sys.argv[1])
        distance = float(sys.argv[2])
        params_file = str(sys.argv[3])
    else:
        sys.exit("Erro: Número incorreto de argumentos.")

    # 2. Carregar os parâmetros de simulação do arquivo YAML
    with open(params_file, "r") as f:
        PARAMETER_VALUES = yaml.safe_load(f)

    # Adicionar os parâmetros dinâmicos ao dicionário
    PARAMETER_VALUES["distance"] = distance
    PARAMETER_VALUES["required_length"] = desired_key_length
    
    # 3. Chamar a nova função principal que executa o BB84 com Decoy States
    # Esta função retornará a chave final e as estatísticas da simulação
    final_key, sim_stats = FULL_BB84_DECOY(PARAMETER_VALUES)

    # 4. Extrair os resultados e formatar a saída para o controller.py
    simulated_time = sim_stats.get("total_duration_s", 0)
    
    # A chave final já deve ser idêntica para Alice e Bob
    alice_final_key = [int(bit) for bit in final_key]
    bob_final_key = [int(bit) for bit in final_key]

    result = {
        "alice_key": alice_final_key,
        "bob_key": bob_final_key,
        "time": simulated_time
    }

    # 5. Imprimir o resultado em formato JSON
    print(json.dumps(result))