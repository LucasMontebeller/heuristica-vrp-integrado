import math
import random
from solver.modelo import Modelo
from solver.solucao import Solucao

class Heuristica():
    """Classe criada para representar as heuristicas utilizadas para resolver o problema."""
    def __init__(self, modelo: Modelo):
        self.modelo = modelo

    def random_search(self, max_exec = 100) -> tuple[Solucao, int, int]:
        melhor_solucao = self.modelo.gera_solucao_aleatoria()
        iteracoes = 0
        iteracoes_convergencia = 0

        while iteracoes < max_exec:
            solucao = self.modelo.gera_solucao_aleatoria()
            if solucao.M < melhor_solucao.M:
                melhor_solucao = solucao
                iteracoes_convergencia = iteracoes

            iteracoes += 1

        return melhor_solucao, iteracoes, iteracoes_convergencia

    def simulated_annealing(self, T_inicial = 100, alpha = 0.995) -> tuple[Solucao, int]:
        T = T_inicial
        solucao = self.modelo.gera_solucao_aleatoria()
        melhor_solucao = solucao
        iteracoes = 0
        iteracoes_convergencia = 0

        # Através do fator de Boltzmann, aceita ou não a troca da solução
        aceita_nova_solucao = lambda energia, temperatura: random.random() < math.exp(-energia / temperatura)

        while T > 0.01:
            nova_solucao = self.modelo.gera_solucao_vizinha(solucao)

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
                iteracoes_convergencia = iteracoes

            T*=alpha
            iteracoes += 1

        return melhor_solucao, iteracoes, iteracoes_convergencia