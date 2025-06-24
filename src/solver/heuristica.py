import math
import time
import random
from solver.modelo import Modelo
from solver.solucao import Solucao

class Heuristica():
    """Classe criada para representar as heuristicas utilizadas para resolver o problema."""
    def __init__(self, modelo: Modelo, tempo_limite: int):
        self.modelo = modelo
        self.tempo_limite = tempo_limite

    def random_search(self, valor_otimo) -> tuple[Solucao, int, int]:
        inicio = time.time()
        tempo_para_otimo = None

        melhor_solucao = self.modelo.gera_solucao_aleatoria()
        iteracoes = 0

        while time.time() - inicio < self.tempo_limite:
            iteracoes += 1

            solucao = self.modelo.gera_solucao_aleatoria()
            if solucao.M < melhor_solucao.M:
                melhor_solucao = solucao

            # Validacao do otimo
            if solucao.M == valor_otimo:
                tempo_para_otimo = time.time() - inicio
                break

        return melhor_solucao, iteracoes, tempo_para_otimo

    def simulated_annealing(self, valor_otimo, T_inicial = 1000, alpha = 0.999) -> tuple[Solucao, int, int]:
        inicio = time.time()
        tempo_para_otimo = None

        T = T_inicial
        solucao = self.modelo.gera_solucao_aleatoria()
        melhor_solucao = solucao
        iteracoes = 0

        # Através do fator de Boltzmann, aceita ou não a troca da solução
        aceita_nova_solucao = lambda energia, temperatura: random.random() < math.exp(-energia / temperatura)
        qtde_swaps = 1 # min(max((iteracoes - iteracoes_convergencia) // 10, 1), 5)

        while time.time() - inicio < self.tempo_limite:
            iteracoes += 1
            nova_solucao = self.modelo.gera_solucao_vizinha(solucao, qtde_swaps=qtde_swaps)

            delta_e = nova_solucao.M - solucao.M

            # redução de energia, implicando que a nova solução é melhor que a anterior
            if delta_e < 0:
                solucao = nova_solucao

            # aumento de energia, aceita novos vizinhos com probabilidade ~ T
            elif aceita_nova_solucao(delta_e, T):
                solucao = nova_solucao

            # atualiza o melhor estado
            if solucao.M < melhor_solucao.M:
                melhor_solucao = solucao

            # Validacao do otimo
            if solucao.M == valor_otimo:
                tempo_para_otimo = time.time() - inicio
                break

            T*=alpha

        return melhor_solucao, iteracoes, tempo_para_otimo
    
    def tabu_search(self, max_exec = 200, tamanho_tabu = 10) -> tuple[Solucao, int, int]:
        solucao = self.modelo.gera_solucao_aleatoria()
        melhor_solucao = solucao
        iteracoes = 0
        iteracoes_convergencia = 0

        tabu_list = []

        while iteracoes < max_exec:
            nova_solucao = self.modelo.gera_solucao_vizinha(solucao, qtde_swaps=1)

            # Se a nova solução estiver na lista Tabu, a rejeitamos, a não ser que seja melhor que a solução atual
            if nova_solucao in tabu_list and nova_solucao.M >= solucao.M:
                continue

            solucao = nova_solucao

            if solucao.M < melhor_solucao.M:
                melhor_solucao = solucao
                iteracoes_convergencia = iteracoes

            tabu_list.append(solucao)

            # Se a lista Tabu atingir o tamanho máximo, remove a solução mais antiga
            if len(tabu_list) > tamanho_tabu:
                tabu_list.pop(0)

            iteracoes += 1

        return melhor_solucao, iteracoes, iteracoes_convergencia