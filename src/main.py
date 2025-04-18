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
        solucao, iteracoes = heuristica.simulated_annealing(max_exec=20000)
        
        tempo_execucao = time.time() - inicio
        
        solucoes[arquivo] = {
            "solucao": solucao,
            "tempo_execucao": tempo_execucao
        }
    return solucoes

def main():
    dados = carregar_dados()
    solucoes = executa_instancias(dados)
    for arquivo, resultado in solucoes.items():
        print(f"{arquivo} - Solução: {resultado['solucao'].M}, Tempo: {resultado['tempo_execucao']:.4f} segundos")

if __name__ == "__main__":
    main()