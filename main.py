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
        self.nL = 8
        self.nT = 3
        self.nV = 3
        self.nE = 2
        self.TC = 1

        self.V = [v for v in range(1, self.nV + 1)]
        self.E = [e for e in range(1, self.nE + 1)]
        self.L = [l for l in range(1, self.nL + 1)]
        self.T = [a for a in range(1, self.nT + 1)]

        self.LT = [3, 3, 2]
        
        # total de linhas = total de talhões 'a' + 2 virtuais
        # total de colunas = total de lotes 'i'
        self.LE = [ 
                [0,	0,	0,	0,	0,	0,	0,	0],
                [1,	1,	1,	0,	0,	0,	0,	0],
                [0,	0,	0,	1,	1,	1,	0,	0],
                [0,	0,	0,	0,	0,	0,	1,	1],
                [0,	0,	0,	0,	0,	0,	0,	0]
        ]
        
        self.T_ida = [0.78, 0.78, 0.78, 1.57, 1.57, 1.57, 0.2, 0.2]
        self.T_volta = [1.15 * t for t in self.T_ida]
        
        self.DE = [
            [0,  0,  0,  0, 0],
            [0,  0, 3.03, 1.24, 0],
            [0, 3.03,  0,  2.15, 0],
            [0, 1.24,  2.15,  0, 0],
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

    def __talhoes_nao_atendidos_empilhadeiras(self, solucao: Solucao) -> list:
        """Encontra uma lista de talhões que nenhuma empilhadeira atendeu ainda."""
        talhoes_atendidos = set()
        for e in self.dados.E:
            for a in self.dados.T:
                if solucao.Z[e - 1][a - 1] == 1:
                    talhoes_atendidos.add(a - 1)
        
        return [talhao for talhao in self.dados.T if talhao - 1 not in talhoes_atendidos]
            
    def __ultimo_lote_atendido_veiculo(self, k, solucao: Solucao) -> int:
        """Encontra o ultimo lote atendido pelo veiculo 'k'"""
        return max((lote for lote in self.dados.L if solucao.S[k - 1][lote - 1] == 1), key=lambda lote: solucao.B[k - 1][lote - 1], default=None)

    def __ultimo_tallhao_atendido_empilhadeira(self, e, solucao: Solucao) -> int:
        """Encontra o ultimo lote atendido pela empilhadeira 'e'"""
        return max((talhao for talhao in self.dados.T if solucao.Z[e - 1][talhao - 1] == 1), key=lambda talhao: solucao.C[e - 1][talhao - 1], default=None)
    
    def __get_talhao_from_lote(self, i) -> int:
        for a in self.dados.T:
            if self.dados.LE[a][i] == 1:
                return a
        return None

    def __add_restricoes_veiculos(self, solucao: Solucao) -> None:
        """Adiciona as restrições dos veiculos, preenchendo as respectivas variáveis na solução."""
        # Os veiculos devem partir da garagem
        for k in self.dados.V:
            lotes_permitidos = self.__lotes_nao_atendidos_veiculos(solucao)
            random_j = random.choice(lotes_permitidos)         # primeiro lote a ser atendido
            solucao.X[k - 1][0][random_j] = 1
            solucao.S[k - 1][random_j - 1] = 1
            
            # Tratamento para lotes no mesmo talhão
            proximo_talhao = self.__get_talhao_from_lote(random_j - 1)
            tempo_minimo_chegada_proximo_talhao = self.dados.T_ida[random_j - 1]
            tempo_finalizacao_ultimo_veiculo_lote = max(
                (
                    solucao.D[v - 1][l] for v in self.dados.V if v != k 
                    for l in range(self.dados.nL) if self.__get_talhao_from_lote(l) == proximo_talhao and solucao.S[v - 1][l] == 1
                ),
                default=0
            )

            tempo_espera_atendimento_proximo_talhao = 0
            if tempo_finalizacao_ultimo_veiculo_lote > 0:
                tempo_espera_atendimento_proximo_talhao = tempo_finalizacao_ultimo_veiculo_lote + self.dados.TC - tempo_minimo_chegada_proximo_talhao

            if tempo_espera_atendimento_proximo_talhao > 0:
                solucao.W[k - 1][random_j - 1] = tempo_espera_atendimento_proximo_talhao

            # Atualiza demais variáveis temporais
            solucao.B[k - 1][random_j - 1] = tempo_minimo_chegada_proximo_talhao
            solucao.D[k - 1][random_j - 1] = solucao.B[k - 1][random_j - 1] + solucao.W[k - 1][random_j - 1]
            solucao.H[random_j - 1] = solucao.D[k - 1][random_j - 1]

        # Gera arcos aleatórios para os veículos, respeitando a continuidade de fluxo
        for _ in range(self.dados.nL + 2):
            # k = random.choice(self.dados.V)
            # Pega o veiculo que terminou o atendimento no ultimo lote mais cedo
            k = min(
                    self.dados.V,
                    key=lambda v: max(
                        solucao.H[i] for i in range(self.dados.nL)
                        if solucao.S[v - 1][i] == 1
                    )
                )
            i = self.__ultimo_lote_atendido_veiculo(k, solucao)
            lotes_permitidos = self.__lotes_nao_atendidos_veiculos(solucao)

            if lotes_permitidos:
                ### Isso é necessário para fazer com que as empilhadeiras finalizem o atendimento dos lotes no talhão.
                # Verifica se há talhões em que o atendimento já começou, mas ainda não finalizou
                talhoes_iniciados = {
                    self.__get_talhao_from_lote(l - 1)
                        for v in self.dados.V
                            for l in self.dados.L
                                if solucao.S[v - 1][l - 1] == 1
                }

                # Talhões onde pelo menos um lote foi atendido e nem todos os lotes foram atendidos
                talhoes_iniciados_nao_finalizados = {
                    talhao
                    for talhao in talhoes_iniciados
                    if sum(
                        solucao.S[v - 1][l - 1] == 1
                            for v in self.dados.V
                                for l in self.dados.L
                                    if self.__get_talhao_from_lote(l - 1) == talhao
                    ) != self.dados.LT[talhao - 1]
                }

                # Prioriza lotes em talhões que já começaram a ser atendidos
                lotes_prioritarios = [l for l in lotes_permitidos if self.__get_talhao_from_lote(l - 1) in talhoes_iniciados_nao_finalizados]

                # Ao invés de random, poderia priorizar pelo tempo T_volta(i) + T_Ida(j)
                # random_j = random.choice(lotes_prioritarios) if lotes_prioritarios else random.choice(lotes_permitidos)
                melhor_lote = (lambda lista: min(lista, key=(lambda j: self.dados.T_volta[i - 1] + self.dados.T_ida[j - 1])))

                # Escolhe o melhor lote baseado no tempo de deslocamento
                if lotes_prioritarios:
                    random_j = melhor_lote(lotes_prioritarios)
                else:
                    random_j = melhor_lote(lotes_permitidos)

                solucao.X[k - 1][i][random_j] = 1
                solucao.S[k - 1][random_j - 1] = 1

                # Tratamento para lotes no mesmo talhão
                proximo_talhao = self.__get_talhao_from_lote(random_j - 1)
                tempo_minimo_chegada_proximo_talhao = solucao.D[k - 1][i - 1] + self.dados.TC + self.dados.T_volta[i - 1] + self.dados.T_ida[random_j - 1]
                tempo_inicio_atendimento_ultimo_veiculo_lote = max(
                    (
                        solucao.D[v - 1][l] for v in self.dados.V if v != k 
                        for l in range(self.dados.nL) if self.__get_talhao_from_lote(l) == proximo_talhao and solucao.S[v - 1][l] == 1
                    ),
                    default=0
                )

                tempo_espera_atendimento_proximo_talhao = tempo_inicio_atendimento_ultimo_veiculo_lote + self.dados.TC - tempo_minimo_chegada_proximo_talhao
                if tempo_espera_atendimento_proximo_talhao > 0:
                    solucao.W[k - 1][random_j - 1] = tempo_espera_atendimento_proximo_talhao

                # Atualiza demais variáveis temporais
                solucao.B[k - 1][random_j - 1] = tempo_minimo_chegada_proximo_talhao # + solucao.W[k - 1][i - 1] # + self.dados.TC
                solucao.D[k - 1][random_j - 1] = solucao.B[k - 1][random_j - 1] + solucao.W[k - 1][random_j - 1]
                solucao.H[random_j - 1] = solucao.D[k - 1][random_j - 1]

        # Os veiculos devem terminar na garagem
        # Isso não gera nenhum impacto no resultado, apenas garante integridade
        for k in self.dados.V:
            i = self.__ultimo_lote_atendido_veiculo(k, solucao)
            solucao.X[k - 1][i][self.dados.nL + 1] = 1

    def __add_restricoes_empilhadeiras(self, solucao: Solucao) -> None:
        """Adiciona as restrições relacionadas às empilhadeiras à solução."""
        # Ordena os lotes atendidos pelos veículos
        lotes_ordenados_tempo = sorted(range(len(solucao.H)), key=lambda i: solucao.H[i])
        for i in lotes_ordenados_tempo:
            talhao = self.__get_talhao_from_lote(i)

            # Caso seja o primeiro atendimento, i.e a empilhadeira está saindo da garagem
            if any(all(z == 0 for z in solucao.Z[e - 1]) for e in self.dados.E) and not any(solucao.Z[e - 1][talhao - 1] == 1 for e in self.dados.E):
                empilhadeira_disponivel = random.choice([e for e in self.dados.E if self.__ultimo_tallhao_atendido_empilhadeira(e, solucao) is None])
                solucao.Y[empilhadeira_disponivel - 1][0][talhao] = 1
                solucao.Z[empilhadeira_disponivel - 1][talhao - 1] = 1
                solucao.C[empilhadeira_disponivel - 1][talhao] = solucao.H[i]
            # Verifica se já tem alguma empilhadeira atendendo o respectivo talhão
            elif any(solucao.Z[e - 1][talhao - 1] == 1 for e in self.dados.E):
                # O problema está na atualização de B. 
                empilhadeira_atendendo = next((e for e in self.dados.E if solucao.Z[e - 1][talhao - 1] == 1), None)
                tempo_inicio_atendimento_ultimo_lote = max(
                    (solucao.H[l] for l in lotes_ordenados_tempo
                    if lotes_ordenados_tempo.index(l) < lotes_ordenados_tempo.index(i)  # Apenas lotes anteriores ao atual
                    and self.__get_talhao_from_lote(l) == talhao  # Apenas lotes do mesmo talhão
                    and solucao.Z[empilhadeira_atendendo - 1][self.__get_talhao_from_lote(l) - 1] == 1),
                    default=0
                )
                tempo_finaliza_atendimento_ultimo_lote = tempo_inicio_atendimento_ultimo_lote + self.dados.TC

                tempo_chegada_veiculo_lote, k = next(((solucao.B[k - 1][i], k) for k in self.dados.V if solucao.B[k - 1][i] != 0), 0)

                # O lote só é completamente atendido quando a empilhadeira chega nele.
                # O veiculo chegou primeiro
                if (tempo_finaliza_atendimento_ultimo_lote > tempo_chegada_veiculo_lote):
                    tempo_chegada_veiculo_lote, k = next(((solucao.B[k - 1][i], k) for k in self.dados.V if solucao.B[k - 1][i] != 0), 0)
                    solucao.W[k - 1][i] = tempo_finaliza_atendimento_ultimo_lote - tempo_chegada_veiculo_lote
                    solucao.D[k - 1][i] = solucao.B[k - 1][i] + solucao.W[k - 1][i]
                    solucao.H[i] = solucao.D[k - 1][i]
                    # Tem que propagar o atraso na variável B dos próximos atendimentos do veiculo
                    # for j in lotes_ordenados_tempo:
                    #     if solucao.B[k - 1][j] > solucao.B[k - 1][i]:
                    #         solucao.B[k - 1][j] += solucao.W[k - 1][i]
                    #         solucao.D[k - 1][j] += solucao.W[k - 1][i]
                    #         solucao.H[j] = solucao.B[k - 1][j]

            # Alguma empilhadeira precisará se deslocar para atender o respectivo talhão.
            else:
                # Escolhe a empilhadeira que finalizou todos os lotes do seu talhão mais cedo
                empilhadeira_disponivel = min(
                    self.dados.E,
                    key=lambda e: max(
                        solucao.H[i] for i in range(self.dados.nL)
                        if solucao.Z[e - 1][self.__get_talhao_from_lote(i) - 1] == 1  # Apenas lotes atendidos pela empilhadeira
                    )
                )
                ultimo_talhao_atendido = self.__ultimo_tallhao_atendido_empilhadeira(empilhadeira_disponivel, solucao)
                ultimo_lote_atendido, tempo_inicio_atendimento_ultimo_lote = max(
                    ((i, solucao.H[i]) for i in range(self.dados.nL) 
                        if self.__get_talhao_from_lote(i) == ultimo_talhao_atendido and solucao.Z[empilhadeira_disponivel - 1][self.__get_talhao_from_lote(i) - 1] == 1),
                    key=lambda x: x[1],
                    default=(None, 0)
                )
                tempo_deslocamento_empilhadeira = tempo_inicio_atendimento_ultimo_lote + self.dados.TC + self.dados.DE[ultimo_talhao_atendido][talhao]
                tempo_chegada_veiculo_lote, k = next(((solucao.B[k - 1][i], k) for k in self.dados.V if solucao.B[k - 1][i] != 0), 0)

                solucao.Y[empilhadeira_disponivel - 1][ultimo_talhao_atendido][talhao] = 1
                solucao.Z[empilhadeira_disponivel - 1][talhao - 1] = 1
                solucao.C[empilhadeira_disponivel - 1][talhao] = tempo_deslocamento_empilhadeira

                # Veiculo ficou esperando
                if (tempo_deslocamento_empilhadeira > tempo_chegada_veiculo_lote):
                    solucao.W[k - 1][i] = tempo_deslocamento_empilhadeira - tempo_chegada_veiculo_lote
                    solucao.D[k - 1][i] = solucao.B[k - 1][i] + solucao.W[k - 1][i]
                    solucao.H[i] = solucao.D[k - 1][i]
                    # Tem que propagar o atraso na variável B dos próximos atendimentos do veiculo
                    for j in lotes_ordenados_tempo:
                        if solucao.B[k - 1][j] > solucao.B[k - 1][i]:
                            solucao.B[k - 1][j] += solucao.W[k - 1][i]
                            solucao.D[k - 1][j] += solucao.W[k - 1][i]
                            solucao.H[j] = solucao.B[k - 1][j]
 
    def gera_solucao_aleatoria(self) -> Solucao:
        """Gera uma solução aleatória para o problema."""

        solucao = Solucao(self.dados)
        self.__add_restricoes_veiculos(solucao)
        self.__add_restricoes_empilhadeiras(solucao)

        # Atualizar makespan
        solucao.M = max(solucao.H) - self.dados.TC # O otimizado não está considerando isso para o ultimo lote.

        return solucao  
    
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
    solucao, iteracoes = heuristica.simulated_annealing(max_exec=20000)
    
if __name__ == "__main__":
    main()

## Rever experimentos:
# Exp08_02
# Exp08_04
# Exp08_05