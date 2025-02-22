import json
import os
from solver import Dados, Modelo, Heuristica

def carregar_dados() -> list[Dados]:
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

def executa_instancias(instancias: list[tuple[str, Dados]]) -> dict[str, any]:
    solucoes = {}
    for arquivo, dados in instancias:
        modelo = Modelo(dados)
        heuristica = Heuristica(modelo)
        solucao, iteracoes = heuristica.simulated_annealing(max_exec=20000)
        solucoes[arquivo] = solucao
    return solucoes

def main():
    dados = carregar_dados()
    solucoes = executa_instancias(dados)
    for arquivo, sol in solucoes.items():
        print(f"{arquivo} - {sol.M}")

if __name__ == "__main__":
    main()