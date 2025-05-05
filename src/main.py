import json
import os
import time
from solver import Dados, Modelo, Heuristica

def carregar_dados() -> list[tuple[str, Dados]]:
    pasta = "data"
    arquivos_json = [f for f in os.listdir(pasta) if f.endswith(".json")]
    
    dados_lista = []
    for arquivo in arquivos_json:
        caminho_completo = os.path.join(pasta, arquivo)
        try:
            with open(caminho_completo, "r", encoding="utf-8") as f:
                dados_json = json.load(f)
                dados_lista.append((arquivo, Dados(**dados_json)))
        except (json.JSONDecodeError, OSError, TypeError) as e:
            print(f"Erro ao carregar {arquivo}: {e}")
    
    return dados_lista

def executa_instancias(instancias: list[tuple[str, Dados]]) -> dict[str, dict]:
    solucoes = {}
    for arquivo, dados in instancias:
        # if arquivo != 'exp0_inicial.json':
        #     continue
        
        modelo = Modelo(dados)
        heuristica = Heuristica(modelo)
        max_exec = 1000

        inicio = time.time()
        solucao_random, iteracoes_random, iteracoes_convergencia_random = heuristica.random_search(max_exec=max_exec)
        tempo_execucao_random = time.time() - inicio

        inicio = time.time()
        solucao_annealing, iteracoes_annealing, iteracoes_convergencia_annealing = heuristica.simulated_annealing(alpha=0.998, max_exec=max_exec)
        tempo_execucao_annealing = time.time() - inicio

        inicio = time.time()
        solucao_tabu, iteracoes_tabu, iteracoes_convergencia_tabu = heuristica.busca_tabu(max_exec=max_exec, tamanho_tabu=20)
        tempo_execucao_tabu = time.time() - inicio

        solucoes[arquivo] = {
            "random_search": {
                "solucao": solucao_random.M,
                "iteracoes": iteracoes_random,
                "iteracoes_convergencia": iteracoes_convergencia_random,
                "tempo_execucao": tempo_execucao_random
            },
            "simulated_annealing": {
                "solucao": solucao_annealing.M,
                "iteracoes": iteracoes_annealing,
                "iteracoes_convergencia": iteracoes_convergencia_annealing,
                "tempo_execucao": tempo_execucao_annealing
            },
            "busca_tabu": {
                "solucao": solucao_tabu.M,
                "iteracoes": iteracoes_tabu,
                "iteracoes_convergencia": iteracoes_convergencia_tabu,
                "tempo_execucao": tempo_execucao_tabu
            }
        }

    return solucoes

def main():
    dados = carregar_dados()
    solucoes = executa_instancias(dados)
    for arquivo, resultado in solucoes.items():
        print(f"###### {arquivo} ######")
        for heuristica, resultado_heuristica in resultado.items():
            print(f"  {heuristica}:")
            print(f"    Solução: {resultado_heuristica['solucao']}")
            print(f"    Iterações: {resultado_heuristica['iteracoes']}")
            print(f"    Iterações para convergência: {resultado_heuristica['iteracoes_convergencia']}")
            print(f"    Tempo de execução: {resultado_heuristica['tempo_execucao']:.4f} segundos")
            print("\n")

if __name__ == "__main__":
    main()