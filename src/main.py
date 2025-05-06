import json
import os
import time
import numpy as np
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

def execucao_heuristica_multiple_times(heuristica, max_exec=1000, n_execucoes=10):
    solucoes = []
    tempos = []
    iteracoes = []
    iteracoes_convergencia = []

    for _ in range(n_execucoes):
        inicio = time.time()
        solucao, iteracao, iteracao_convergencia = heuristica(max_exec=max_exec)
        tempo_execucao = time.time() - inicio

        solucoes.append(solucao.M)
        tempos.append(tempo_execucao)
        iteracoes.append(iteracao)
        iteracoes_convergencia.append(iteracao_convergencia)

    return {
        "solucoes": solucoes,
        "media_solucao": np.mean(solucoes),
        "desvio_padrao_solucao": np.std(solucoes),
        "media_tempos_execucao": np.mean(tempos),
        "desvio_padrao_tempos_execucao": np.std(tempos),
        "media_iteracoes": np.mean(iteracoes),
        "desvio_padrao_iteracoes": np.std(iteracoes),
        "media_iteracoes_convergencia": np.mean(iteracoes_convergencia),
        "desvio_padrao_iteracoes_convergencia": np.std(iteracoes_convergencia)
    }

def executa_instancias(instancias: list[tuple[str, Dados]], n_execucoes=10) -> dict[str, dict]:
    solucoes = {}
    for arquivo, dados in instancias:
        modelo = Modelo(dados)
        heuristica = Heuristica(modelo)
        max_exec = 1000
        
        solucoes_random = execucao_heuristica_multiple_times(heuristica.random_search, max_exec=max_exec, n_execucoes=n_execucoes)
        solucoes_annealing = execucao_heuristica_multiple_times(heuristica.simulated_annealing, max_exec=max_exec, n_execucoes=n_execucoes)
        solucoes_tabu = execucao_heuristica_multiple_times(heuristica.tabu_search, max_exec=max_exec, n_execucoes=n_execucoes)

        solucoes[arquivo] = {
            "random_search": solucoes_random,
            "simulated_annealing": solucoes_annealing,
            "tabu_search": solucoes_tabu
        }

    return solucoes

def salvar_resultados(solucoes: dict[str, dict], nome_arquivo="resultados.json"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(solucoes, f, ensure_ascii=False, indent=4)

def main():
    dados = carregar_dados()
    solucoes = executa_instancias(dados, n_execucoes=20)
    salvar_resultados(solucoes)

    # for arquivo, resultado in solucoes.items():
    #     print(f"###### {arquivo} ######")
    #     for heuristica, resultado_heuristica in resultado.items():
    #         print(f"  {heuristica}:")
    #         print(f"    Média da solução: {resultado_heuristica['media_solucao']}")
    #         print(f"    Desvio padrão da solução: {resultado_heuristica['desvio_padrao_solucao']}")
    #         print(f"    Média das iterações: {resultado_heuristica['media_iteracoes']}")
    #         print(f"    Desvio padrão das iterações: {resultado_heuristica['desvio_padrao_iteracoes']}")
    #         print(f"    Média do tempo de execução: {resultado_heuristica['media_tempos_execucao']:.4f} segundos")
    #         print(f"    Desvio padrão do tempo de execução: {resultado_heuristica['desvio_padrao_tempos_execucao']:.4f} segundos")
    #         print(f"    Média de iterações até convergência: {resultado_heuristica['media_iteracoes_convergencia']}")
    #         print(f"    Desvio padrão de iterações até convergência: {resultado_heuristica['desvio_padrao_iteracoes_convergencia']}")
    #         print("\n")

if __name__ == "__main__":
    main()