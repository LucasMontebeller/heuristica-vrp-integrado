import random
import math

class Dados:
    """Classe que armazena os dados do problema."""
    def __init__(self):
        """Atributos:
        ----------
        - nL: Total de lotes disponíveis.
        - nT: Total de talhões disponíveis.
        - nV: Total de veículos disponíveis.
        - nE: Total de empilhadeiras disponíveis.
        - TC: Tempo fixo de carregamento em horas.
        - V: Conjunto dos veículos.
        - E: Conjunto das empilhadeiras.
        - L: Conjunto dos lotes.
        - T: Conjunto dos talhões.
        - LT: Lista com o total de lotes em cada talhão.
        - LE: Matriz binária (a, i) que identifica se o lote 'i' pertence ao talhão 'a'.
        - T_ida: Lista com o tempo de ida da fábrica até cada lote.
        - T_volta: Lista com o tempo de volta do lote à fábrica (calculado como 1.15 vezes o tempo de ida).
        - DE: Matriz (a, b) que representa o tempo de deslocamento entre os talhões 'a' e 'b'.
        """
        self.nL = 6
        self.nT = 3
        self.nV = 2
        self.nE = 2
        self.TC = 0.5

        self.V = [v for v in range(1, self.nV + 1)]
        self.E = [e for e in range(1, self.nE + 1)]
        self.L = [l for l in range(1, self.nL + 1)]
        self.T = [a for a in range(1, self.nT + 1)]

        self.LT = [2, 3, 1]
        
        # total de linhas = total de talhões 'a' + 2 virtuais
        # total de colunas = total de lotes 'i'
        self.LE = [ 
            [0,	0,	0,	0,	0,	0],
            [1,	1,	0,	0,	0,	0],
            [0,	0,	1,	1,	1,	0],
            [0,	0,	0,	0,	0,	1],
            [0,	0,	0,	0,	0,	0],
        ]
        
        self.T_ida = [2, 2, 1.5, 1.5, 1.5, 3] 
        self.T_volta = [1.15 * t for t in self.T_ida]
        
        self.DE = [
            [0,  0,  0,  0, 0],
            [0,  0, 10, 12, 0],
            [0, 10,  0,  9, 0],
            [0, 12,  9,  0, 0],
            [0,  0,  0,  0, 0],
        ]
        
class Solucao:
    """Representa uma solução gerada para o problema."""
    def __init__(self, dados: Dados):
        """
        Variáveis de Decisão:
        ---------------------
        - X[k][i][j]: Variável binária. Indica se o veículo 'k' atende o lote 'j' logo após 'i'.
        - S[k][i]: Variável binária. Indica se o veículo 'k' atende o lote 'i'.
        - B[k][i]: Tempo em que o veículo 'k' chega no lote 'i' (em horas).
        - D[k][i]: Tempo em que o veículo 'k' começa a ser carregado com o lote 'i' (em horas).
        - W[k][i]: Tempo de espera do veículo 'k' no talhão para ser carregado com o lote 'i' (em horas).
        - H[i]: Tempo em que o lote 'i' foi completamente atendido (em horas).
        - Y[e][a][b]: Variável binária. Indica se a empilhadeira 'e' atende o talhão 'b' logo após 'a'.
        - Z[e][a]: Variável binária. Indica se a empilhadeira 'e' atende o talhão 'a'.
        - C[e][a]: Tempo em que a empilhadeira 'e' começa a atender o talhão 'a' (em horas).
        - M: Tempo de início do atendimento do último lote, em horas (valor contínuo).
        """
        self.X = [[[0 for _ in range(dados.nL + 2)] for _ in range(dados.nL + 2)] for _ in range(dados.nV)]  # aqui entre os lotes virtuais
        self.S = [[0 for _ in range(dados.nL)] for _ in range(dados.nV)]
        self.B = [[0 for _ in range(dados.nL)] for _ in range(dados.nV)]
        self.D = [[0 for _ in range(dados.nL)] for _ in range(dados.nV)] 
        self.W = [[0 for _ in range(dados.nL)] for _ in range(dados.nV)]
        self.H = [0 for _ in range(dados.nL)]
        self.Y = [[[0 for _ in range(dados.nT + 2)] for _ in range(dados.nT + 2)] for _ in range(dados.nE)]
        self.Z = [[0 for _ in range(dados.nT)] for _ in range(dados.nE)]
        self.C = [[0.0 for _ in range(dados.nT + 2)] for _ in range(dados.nE)]
        self.M = 0.0

class Modelo:
    """Representa o modelo que rege o problema, incluido as respectivas restrições."""
    def __init__(self, dados: Dados):
        self.dados = dados

    def __lotes_nao_atendidos_veiculos(self, solucao: Solucao) -> list:
        """Encontra uma lista de lotes que nenhum veículo atendeu ainda."""
        lotes_atendidos = set()
        for v in self.dados.V:
            for l in self.dados.L:
                if solucao.S[v - 1][l - 1] == 1:
                    lotes_atendidos.add(l - 1)
        
        return [lote for lote in self.dados.L if lote - 1 not in lotes_atendidos]
    
    def __talhoes_nao_atendidos_empilhadeira(self, solucao: Solucao) -> list:
        """Encontra uma lista de talhões que nenhuma empilhadeira atendeu ainda."""
        talhoes_atendidos = set()
        for e in self.dados.E:
            for a in self.dados.T:
                if solucao.Z[e - 1][a - 1] == 1:
                    talhoes_atendidos.add(a - 1)
        
        return [talhao for talhao in self.dados.T if talhao - 1 not in talhoes_atendidos]
    
    def __ultimo_lote_atendido(self, k, solucao: Solucao) -> int:
        """Encontra o ultimo lote atendido pelo veiculo 'k'"""
        return max((lote for lote in self.dados.L if solucao.S[k - 1][lote - 1] == 1), key=lambda lote: solucao.B[k - 1][lote - 1], default=None)
    
    def __get_talhao_from_lote(self, i) -> int:
        for a in self.dados.T:
            if self.dados.LE[a][i] == 1:
                return a
        return None

    def __add_restricoes_veiculos(self, solucao: Solucao) -> None:
        """Adiciona as restrições dos veículos."""
        # Os veiculos devem partir da garagem
        for k in self.dados.V:
            lotes_permitidos = self.__lotes_nao_atendidos_veiculos(solucao)
            random_j = random.choice(lotes_permitidos)         # primeiro lote a ser atendido
            solucao.X[k - 1][0][random_j] = 1
            solucao.S[k - 1][random_j - 1] = 1
            
            # Tratamento para lotes no mesmo talhão
            proximo_talhao = self.__get_talhao_from_lote(random_j - 1)
            tempo_minimo_chegada_proximo_talhao = self.dados.T_ida[random_j - 1]
            chegada_ultimo_veiculo_talhao = max(
                (
                    solucao.D[v - 1][l] for v in self.dados.V if v != k 
                    for l in range(self.dados.nL) if self.__get_talhao_from_lote(l) == proximo_talhao and solucao.S[v - 1][l] == 1
                ),
                default=0
            )
            tempo_espera_atendimento_proximo_talhao = chegada_ultimo_veiculo_talhao + self.dados.TC - tempo_minimo_chegada_proximo_talhao
            if tempo_espera_atendimento_proximo_talhao > 0:
                solucao.W[k - 1][random_j - 1] = tempo_espera_atendimento_proximo_talhao

            # Atualiza demais variáveis temporais
            solucao.B[k - 1][random_j - 1] = tempo_minimo_chegada_proximo_talhao
            solucao.D[k - 1][random_j - 1] = solucao.B[k - 1][random_j - 1] + solucao.W[k - 1][random_j - 1]
            solucao.H[random_j - 1] = solucao.D[k - 1][random_j - 1]

        # Gera arcos aleatórios para os veículos, respeitando a continuidade de fluxo
        for _ in range(self.dados.nL + 2):
            k = random.choice(self.dados.V)
            i = self.__ultimo_lote_atendido(k, solucao)
            lotes_permitidos = self.__lotes_nao_atendidos_veiculos(solucao)

            if lotes_permitidos:
                random_j = random.choice(lotes_permitidos)
                solucao.X[k - 1][i][random_j] = 1
                solucao.S[k - 1][random_j - 1] = 1

                # Tratamento para lotes no mesmo talhão
                proximo_talhao = self.__get_talhao_from_lote(random_j - 1)
                tempo_minimo_chegada_proximo_talhao = solucao.B[k - 1][i - 1] + self.dados.T_volta[i - 1] + self.dados.T_ida[random_j - 1]
                chegada_ultimo_veiculo_talhao = max(
                    (
                        solucao.D[v - 1][l] for v in self.dados.V if v != k 
                        for l in range(self.dados.nL) if self.__get_talhao_from_lote(l) == proximo_talhao and solucao.S[v - 1][l] == 1
                    ),
                    default=0
                )
                tempo_espera_atendimento_proximo_talhao = chegada_ultimo_veiculo_talhao + self.dados.TC - tempo_minimo_chegada_proximo_talhao
                if tempo_espera_atendimento_proximo_talhao > 0:
                    solucao.W[k - 1][random_j - 1] = tempo_espera_atendimento_proximo_talhao

                # Atualiza demais variáveis temporais
                solucao.B[k - 1][random_j - 1] = tempo_minimo_chegada_proximo_talhao + solucao.W[k - 1][i - 1] + self.dados.TC
                solucao.D[k - 1][random_j - 1] = solucao.B[k - 1][random_j - 1] + solucao.W[k - 1][random_j - 1]
                solucao.H[random_j - 1] = solucao.D[k - 1][random_j - 1]

        # Os veiculos devem terminar na garagem
        for k in self.dados.V:
            i = self.__ultimo_lote_atendido(k, solucao)
            solucao.X[k - 1][i][self.dados.nL + 1] = 1

    def __add_restricoes_empilhadeiras(self, solucao: Solucao) -> None:
        """Adiciona as restrições relacionadas às empilhadeiras à solução."""

        lotes_nao_atribuidos = set(range(len(solucao.H)))

        # Atribui cada empilhadeira a um talhão, a partir da garagem
        for e in self.dados.E:
            talhoes_permitidos = self.__talhoes_nao_atendidos_empilhadeira(solucao)
            
            # Encontra o primeiro lote válido a ser atendido, i.e, aquele que o veiculo chegou primeiro e nenhuma empilhadeira atendeu ainda.
            while len(lotes_nao_atribuidos) > 0:
                primeiro_lote_atendido = min(lotes_nao_atribuidos, key=solucao.H.__getitem__)
                primeiro_talhao = self.__get_talhao_from_lote(primeiro_lote_atendido)
                lotes_nao_atribuidos.remove(primeiro_lote_atendido)

                if primeiro_talhao in talhoes_permitidos:
                    break

            if primeiro_talhao is not None:
                solucao.Y[e - 1][0][primeiro_talhao] = 1
                solucao.Z[e - 1][primeiro_talhao - 1] = 1
                solucao.C[e - 1][primeiro_talhao] = solucao.H[primeiro_lote_atendido]
           
        # Baseado no talhão inicial, atende todos os lotes deste, obedecendo a sequência pré-estabelecida pelo roteamento de veículos
        # for e in self.dados.E:
        #     for a in self.dados.T:
        #         # Verifica se a empilhadeira já está atribuída ao talhão
        #         if solucao.Z[e - 1][a - 1] == 1:

        #             # Obtém os lotes pertencentes ao talhão atual, ordenados pelo tempo H (atendimento dos veículos)
        #             lotes_do_talhao = [i for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == a]
        #             lotes_do_talhao.sort(key=lambda i: solucao.H[i - 1])  # Ordena por tempo de atendimento

        lotes_ordenados_tempo = sorted(range(len(solucao.H)), key=lambda i: solucao.H[i])
        for i in lotes_ordenados_tempo:
            talhao = self.__get_talhao_from_lote(i)

                    



    def gera_solucao_aleatoria(self) -> Solucao:
        """Gera uma solução aleatória para o problema."""

        solucao = Solucao(self.dados)
        self.__add_restricoes_veiculos(solucao)
        self.__add_restricoes_empilhadeiras(solucao)

        # Atualizar makespan
        solucao.M = max(solucao.H)

        return solucao  
    
class Heuristica():
    """Classe criada para representar as heuristicas utilizadas para resolver o problema."""
    def __init__(self, modelo: Modelo):
        self.modelo = modelo

    def simulated_annealing(self, T_inicial = 100, alpha = 0.995):
        T = T_inicial
        solucao = self.modelo.gera_solucao_aleatoria() # solucao inicial
        melhor_solucao = solucao
        cont = 0

        # Através do fator de Boltzmann, aceita ou não a troca da solução
        aceita_nova_solucao = lambda energia, temperatura: random.random() < math.exp(-energia / temperatura)

        while T > 0.1:
            nova_solucao = self.modelo.gera_solucao_aleatoria()

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

def main():
    dados = Dados()
    modelo = Modelo(dados)
    heuristica = Heuristica(modelo)
    solucao, iteracoes = heuristica.simulated_annealing()
    
if __name__ == "__main__":
    main()