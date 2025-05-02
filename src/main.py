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
        
        inicio = time.time()
        
        modelo = Modelo(dados)
        heuristica = Heuristica(modelo)
        # TODO: Executar random_search várias vezes e plotar gráfico de convergência x iteracoes. Isso vai dar o quão restrintivo o gerador de solucoes está.
        # solucao, iteracoes, iteracoes_convergencia = heuristica.random_search(max_exec=1000)
        solucao, iteracoes = heuristica.simulated_annealing()
        
        tempo_execucao = time.time() - inicio
        
        solucoes[arquivo] = {
            "solucao": solucao,
            "tempo_execucao": tempo_execucao,
            "iteracoes_convergencia": 0 #iteracoes_convergencia
        }

    return solucoes

def main():
    dados = carregar_dados()
    solucoes = executa_instancias(dados)
    for arquivo, resultado in solucoes.items():
        print(f"{arquivo} - Solução: {resultado['solucao'].M}, Tempo: {resultado['tempo_execucao']:.4f} segundos, Iterações convergencia: {resultado['iteracoes_convergencia']}")

if __name__ == "__main__":
    main()