import random

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
        


class Modelo:
    """Classe base do problema, armazenando as variáveis de decisão e um gerador de soluções."""
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
        self.dados = dados
        self.X = [[[0 for _ in range(dados.nL + 2)] for _ in range(dados.nL + 2)] for _ in range(dados.nV)]  # aqui entre os lotes virtuais
        self.S = [[0 for _ in range(dados.nL)] for _ in range(dados.nV)]
        self.B = [[0.0 for _ in range(dados.nL)] for _ in range(dados.nV)]
        self.D = [[0.0 for _ in range(dados.nL)] for _ in range(dados.nV)] 
        self.W = [[0.0 for _ in range(dados.nL)] for _ in range(dados.nV)]
        self.H = [0.0 for _ in range(dados.nL)]
        # self.Y = [[[0 for _ in range(dados.total_talhoes)] for _ in range(dados.total_talhoes)] for _ in range(dados.E)]
        # self.Z = [[0 for _ in range(dados.total_talhoes)] for _ in range(dados.E)]
        # self.C = [[0.0 for _ in range(dados.total_talhoes)] for _ in range(dados.E)]
        self.M = 0.0

    def lotes_nao_atendidos(self):
        """Encontra uma lista de lotes que nenhum veículo atendeu ainda."""
        lotes_atendidos = set()
        for v in self.dados.V:
            for l in self.dados.L:
                if self.S[v - 1][l - 1] == 1:
                    lotes_atendidos.add(l - 1)
        
        return [lote for lote in self.dados.L if lote - 1 not in lotes_atendidos]

    def gera_solucao_aleatoria(self):
        """Gera uma solução aleatória para o problema."""

        # Os veiculos devem partir da garagem
        for k in self.dados.V:
            lotes_permitidos = self.lotes_nao_atendidos()
            random_j = random.choice(lotes_permitidos)         # primeiro lote a ser atendido
            self.X[k - 1][0][random_j] = 1
            self.S[k - 1][random_j - 1] = 1
            self.B[k - 1][random_j - 1] = self.dados.T_ida[random_j - 1]

        # Gera arcos aleatórios para os veículos, respeitando a continuidade de fluxo
        for _ in range(self.dados.nL + 2):
            k = random.choice(self.dados.V)

            # Encontra o ultimo lote atendido pelo veiculo 'k'   
            i = max(
                (lote for lote in self.dados.L if self.S[k - 1][lote - 1] == 1),
                key=lambda lote: self.B[k - 1][lote - 1])

            lotes_permitidos = self.lotes_nao_atendidos()

            if lotes_permitidos:
                random_j = random.choice(lotes_permitidos)
                self.X[k - 1][i][random_j] = 1
                self.S[k - 1][random_j - 1] = 1
                self.B[k - 1][random_j - 1] = self.W[k - 1][i] + self.dados.TC + self.dados.T_volta[i - 1] + self.dados.T_ida[random_j - 1]

        # Garantir que todos os lotes sejam atendidos
        # for i in range(self.dados.total_lotes):
        #     if not any(self.S[k][i] for k in range(self.dados.V)):
        #         self.S[0][i] = 1  # Atribuir lotes restantes ao primeiro veículo

        # # Preencher a sequência de atendimento X[k][i][j]
        # for k in range(self.dados.V):
        #     atendidos = [i for i in range(self.dados.total_lotes) if self.S[k][i] == 1]
        #     random.shuffle(atendidos)  # Embaralha a ordem de atendimento dos lotes para o veículo k
        #     for idx in range(len(atendidos) - 1):
        #         i, j = atendidos[idx], atendidos[idx + 1]
        #         self.X[k][i][j] = 1

        # # Embaralha os talhões para distribuição aleatória
        # talhoes = list(range(self.dados.total_talhoes))
        # random.shuffle(talhoes)

        # talhoes_por_empilhadeira = self.dados.total_talhoes // self.dados.E
        # talhao_atual = 0

        # # Atribuir talhões às empilhadeiras de forma aleatória
        # for e in range(self.dados.E):
        #     for _ in range(talhoes_por_empilhadeira):
        #         if talhao_atual < self.dados.total_talhoes:
        #             talhao = talhoes[talhao_atual]
        #             # Atribuir o talhão à empilhadeira e
        #             self.Z[e][talhao] = 1
        #             self.C[e][talhao] = self.M  # Tempo inicial de atendimento do talhão
        #             talhao_atual += 1

        # # Garantir que todos os talhões sejam atendidos
        # for a in range(self.dados.total_talhoes):
        #     if not any(self.Z[e][a] for e in range(self.dados.E)):
        #         self.Z[0][a] = 1  # Atribuir talhões restantes à primeira empilhadeira

        # # Preencher a sequência de atendimento Y[e][a][b]
        # for e in range(self.dados.E):
        #     atendidos = [a for a in range(self.dados.total_talhoes) if self.Z[e][a] == 1]
        #     random.shuffle(atendidos)  # Embaralha a ordem de atendimento dos talhões para a empilhadeira e
        #     for idx in range(len(atendidos) - 1):
        #         a, b = atendidos[idx], atendidos[idx + 1]
        #         self.Y[e][a][b] = 1

        # # Atualizar tempos de deslocamento e atendimento
        # for k in range(self.dados.V):
        #     for i in range(self.dados.total_lotes):
        #         if self.S[k][i] == 1:
        #             self.B[k][i] = self.dados.T_ida[i]  # Tempo de ida da fábrica até o lote
        #             self.D[k][i] = self.B[k][i] + self.dados.TC  # Tempo total de atendimento
        #             self.H[i] = self.D[k][i]  # Atualizar instante de atendimento

        # for e in range(self.dados.E):
        #     for a in range(self.dados.total_talhoes):
        #         if self.Z[e][a] == 1:
        #             self.C[e][a] = self.dados.DE[a][a]  # Tempo de deslocamento entre talhões

        # Atualizar makespan
        self.M = max(self.H)      

def main():
    dados = Dados()
    modelo = Modelo(dados)
    solucao = modelo.gera_solucao_aleatoria()
    
if __name__ == "__main__":
    main()