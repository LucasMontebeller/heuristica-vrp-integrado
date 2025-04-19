import math
import random
from solver.modelo import Modelo

class Heuristica():
    """Classe criada para representar as heuristicas utilizadas para resolver o problema."""
    def __init__(self, modelo: Modelo):
        self.modelo = modelo

    def simulated_annealing(self, T_inicial = 100, alpha = 0.995, max_exec = 500):
        T = T_inicial
        solucao = self.modelo.gera_solucao_aleatoria() # solucao inicial
        melhor_solucao = solucao
        cont = 0

        # Através do fator de Boltzmann, aceita ou não a troca da solução
        aceita_nova_solucao = lambda energia, temperatura: random.random() < math.exp(-energia / temperatura)

        while T > 0.1 and cont < max_exec:
            nova_solucao = self.modelo.gera_solucao_aleatoria()  # talvez deva se relacionar com a anterior (vizinho)

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

            T*=alpha
            cont += 1

        return melhor_solucao, cont