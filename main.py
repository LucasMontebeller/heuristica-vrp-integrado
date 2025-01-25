import random

class Dados:
    """Classe que armazena os dados do problema."""
    def __init__(self):
        """Atributos:
        ----------
        - V: Total de veículos disponíveis.
        - E: Total de empilhadeiras disponíveis.
        - LT: Lista com o total de lotes em cada talhão.
        - LE: Matriz binária (i, a) que identifica se o lote 'i' pertence ao talhão 'a'.
        - T_ida: Lista com o tempo de ida da fábrica até cada lote.
        - T_volta: Lista com o tempo de volta do lote à fábrica (calculado como 1.15 vezes o tempo de ida).
        - DE: Matriz (a, b) que representa o tempo de deslocamento entre os talhões 'a' e 'b'.
        - TC: Tempo fixo de carregamento em horas.
        """
        self.V = 3 
        self.E = 2
        self.LT = [2, 2, 3]
        
        self.LE = [
            [1, 0, 0],  # Exemplo: lote 1 pertence ao talhão 1
            [0, 1, 0],  # lote 2 pertence ao talhão 2
            [0, 0, 1]   # lote 3 pertence ao talhão 3
        ]
        
        self.T_ida = [1, 1, 1, 1, 1, 1, 1] 
        self.T_volta = [1.15 * t for t in self.T_ida]
        
        self.DE = [
            [0, 0.5, 1.0],
            [0.5, 0, 0.8],
            [1.0, 0.8, 0]
        ]
        
        self.TC = 0.5

    @property
    def total_lotes(self):
        return sum(self.LT)
    
    @property
    def total_talhoes(self):
        return len(self.LT)


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
        self.X = [[[0 for _ in range(dados.total_lotes)] for _ in range(dados.total_lotes)] for _ in range(dados.V)] 
        self.S = [[0 for _ in range(dados.total_lotes)] for _ in range(dados.V)]
        self.B = [[0.0 for _ in range(dados.total_lotes)] for _ in range(dados.V)]
        self.D = [[0.0 for _ in range(dados.total_lotes)] for _ in range(dados.V)]
        self.W = [[0.0 for _ in range(dados.total_lotes)] for _ in range(dados.V)]
        self.H = [0.0 for _ in range(dados.total_lotes)]
        self.Y = [[[0 for _ in range(dados.total_talhoes)] for _ in range(dados.total_talhoes)] for _ in range(dados.E)]
        self.Z = [[0 for _ in range(dados.total_talhoes)] for _ in range(dados.E)]
        self.C = [[0.0 for _ in range(dados.total_talhoes)] for _ in range(dados.E)]
        self.M = 0.0

    def gera_solucao_aleatoria(self):
        """
        Gera uma solução aleatória para o problema.
        """
        # Embaralha os lotes para distribuição aleatória
        lotes = list(range(self.dados.total_lotes))
        random.shuffle(lotes)

        lotes_por_veiculo = self.dados.total_lotes // self.dados.V
        lote_atual = 0

        # Atribuir lotes aos veículos de forma aleatória
        for k in range(self.dados.V):
            for _ in range(lotes_por_veiculo):
                if lote_atual < self.dados.total_lotes:
                    lote = lotes[lote_atual]
                    # Atribuir o lote ao veículo k
                    self.S[k][lote] = 1
                    self.H[lote] = self.M  # Tempo inicial de atendimento do lote
                    lote_atual += 1

        # Garantir que todos os lotes sejam atendidos
        for i in range(self.dados.total_lotes):
            if not any(self.S[k][i] for k in range(self.dados.V)):
                self.S[0][i] = 1  # Atribuir lotes restantes ao primeiro veículo

        # Preencher a sequência de atendimento X[k][i][j]
        for k in range(self.dados.V):
            atendidos = [i for i in range(self.dados.total_lotes) if self.S[k][i] == 1]
            random.shuffle(atendidos)  # Embaralha a ordem de atendimento dos lotes para o veículo k
            for idx in range(len(atendidos) - 1):
                i, j = atendidos[idx], atendidos[idx + 1]
                self.X[k][i][j] = 1

        # Embaralha os talhões para distribuição aleatória
        talhoes = list(range(self.dados.total_talhoes))
        random.shuffle(talhoes)

        talhoes_por_empilhadeira = self.dados.total_talhoes // self.dados.E
        talhao_atual = 0

        # Atribuir talhões às empilhadeiras de forma aleatória
        for e in range(self.dados.E):
            for _ in range(talhoes_por_empilhadeira):
                if talhao_atual < self.dados.total_talhoes:
                    talhao = talhoes[talhao_atual]
                    # Atribuir o talhão à empilhadeira e
                    self.Z[e][talhao] = 1
                    self.C[e][talhao] = self.M  # Tempo inicial de atendimento do talhão
                    talhao_atual += 1

        # Garantir que todos os talhões sejam atendidos
        for a in range(self.dados.total_talhoes):
            if not any(self.Z[e][a] for e in range(self.dados.E)):
                self.Z[0][a] = 1  # Atribuir talhões restantes à primeira empilhadeira

        # Preencher a sequência de atendimento Y[e][a][b]
        for e in range(self.dados.E):
            atendidos = [a for a in range(self.dados.total_talhoes) if self.Z[e][a] == 1]
            random.shuffle(atendidos)  # Embaralha a ordem de atendimento dos talhões para a empilhadeira e
            for idx in range(len(atendidos) - 1):
                a, b = atendidos[idx], atendidos[idx + 1]
                self.Y[e][a][b] = 1

        # Atualizar tempos de deslocamento e atendimento
        for k in range(self.dados.V):
            for i in range(self.dados.total_lotes):
                if self.S[k][i] == 1:
                    self.B[k][i] = self.dados.T_ida[i]  # Tempo de ida da fábrica até o lote
                    self.D[k][i] = self.B[k][i] + self.dados.TC  # Tempo total de atendimento
                    self.H[i] = self.D[k][i]  # Atualizar instante de atendimento

        for e in range(self.dados.E):
            for a in range(self.dados.total_talhoes):
                if self.Z[e][a] == 1:
                    self.C[e][a] = self.dados.DE[a][a]  # Tempo de deslocamento entre talhões

        # Atualizar makespan
        self.M = max(self.H)            

def main():
    dados = Dados()
    modelo = Modelo(dados)
    solucao = modelo.gera_solucao_aleatoria()
    
if __name__ == "__main__":
    main()