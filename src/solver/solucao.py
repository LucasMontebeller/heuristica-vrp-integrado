from solver.dados import Dados

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

        self.solucao_veiculos = None  