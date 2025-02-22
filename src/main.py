from solver import Dados, Modelo, Heuristica

def main():
    dados = Dados()
    modelo = Modelo(dados)
    heuristica = Heuristica(modelo)
    solucao, iteracoes = heuristica.simulated_annealing(max_exec=20000)

if __name__ == "__main__":
    main()