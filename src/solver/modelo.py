import random
from solver.dados import Dados
from solver.solucao import Solucao
from copy import deepcopy

class Modelo:
    """Representa o modelo que rege o problema, incluido as respectivas restrições."""
    def __init__(self, dados: Dados):
        self.dados = dados

    def add_restricoes_veiculos(self, solucao: Solucao) -> None:
        """Adiciona as restrições dos veiculos, preenchendo as respectivas variáveis na solução."""
        lotes_permitidos = self.__lotes_nao_atendidos_veiculos(solucao)
        # Gera arcos aleatórios para os veículos, respeitando a continuidade de fluxo
        while len(lotes_permitidos) != 0:
            k = self.__selecionar_veiculo_livre(solucao)            

            if self.__is_primeiro_atendimento(k, solucao):
                i = 0                                                          # Os veiculos devem partir da garagem
                j = self.__get_proximo_lote(0, lotes_permitidos, True)         # Primeiro lote a ser atendido
            else:
                i = self.__ultimo_lote_atendido_veiculo(k, solucao)
                ### Isso é necessário para fazer com que as empilhadeiras finalizem o atendimento dos lotes no talhão.
                l = self.__selecionar_lotes_talhoes_pendentes(lotes_permitidos, solucao)
                if len(l) == 0:
                    l = lotes_permitidos
                j = self.__get_proximo_lote(i, l, True)

            self.__rotear_veiculo(k, i, j, solucao)
            self.__atualizar_variaveis_temporais(k, i, j, solucao)

            lotes_permitidos = self.__lotes_nao_atendidos_veiculos(solucao)

        # Os veiculos devem terminar na garagem
        # Isso não gera nenhum impacto no resultado, apenas garante integridade
        self.__rotear_veiculos_volta_garagem(solucao)

    def add_restricoes_empilhadeiras(self, solucao: Solucao) -> None:
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
        self.add_restricoes_veiculos(solucao)
        self.add_restricoes_empilhadeiras(solucao)

        # Atualizar makespan
        solucao.M = max(solucao.H) # - self.dados.TC. # Agora essa variável representa o instante de atendimento do ultimo lote (ajustar na dissertação).

        return solucao
    
    def gera_solucao_vizinha(self, solucao: Solucao) -> Solucao:
        return self.__swap_veiculos(solucao)
    
    def __swap_veiculos(self, solucao_anterior: Solucao):
        """Gera uma solução vizinha atráves de swap entre dois veiculos."""
        solucao = deepcopy(solucao_anterior)
        nova_solucao = Solucao(self.dados)

        veiculos = list(self.dados.V)
        lotes = list(self.dados.L)

        # Escolhe aleatoriamente dois veiculos para o swap
        k1, k2 = random.sample(veiculos, 2)

        lotes_k1 = [l for l in lotes if solucao.S[k1 - 1][l - 1] == 1 and solucao.S[k2 - 1][l - 1] == 0]
        lotes_k2 = [l for l in lotes if solucao.S[k2 - 1][l - 1] == 1 and solucao.S[k1 - 1][l - 1] == 0]

        # Escolhe aleatoriamente dois lotes para o swap
        l1 = random.choice(lotes_k1)
        l2 = random.choice(lotes_k2)

        inicio_atendimento_l1 = solucao.B[k1 - 1][l1 - 1]
        inicio_atendimento_l2 = solucao.B[k2 - 1][l2 - 1]

        # Alterações
        self.__corte_espaco_temporal(k1, l1, l2, solucao)
        self.__propaga_alteracoes_veiculos(k1, inicio_atendimento_l1, solucao)

        self.__corte_espaco_temporal(k2, l2, l1, solucao)
        self.__propaga_alteracoes_veiculos(k2, inicio_atendimento_l2, solucao)

        # Recalcula empilhadeiras com base na nova ordem de H
        self.add_restricoes_empilhadeiras(nova_solucao)

        # Atualiza makespan
        nova_solucao.M = max(nova_solucao.H)

        return nova_solucao
        
    def __corte_espaco_temporal(self, k, i_old, i_new, solucao: Solucao) -> None:
        """Realiza o swap entre dois lotes."""
        anterior = self.__get_lote_atendimento_anterior(k, i_old, solucao)
        posterior = self.__get_lote_atendimento_posterior(k, i_old, solucao)

        # Remove o lote antigo
        solucao.X[k - 1][anterior][i_old] = 0
        solucao.X[k - 1][i_old][posterior] = 0
        solucao.S[k - 1][i_old - 1] = 0

        # Limpa variáveis temporais do lote removido
        solucao.W[k - 1][i_old - 1] = 0
        solucao.B[k - 1][i_old - 1] = 0
        solucao.D[k - 1][i_old - 1] = 0
        solucao.H[i_old - 1] = 0

        # Propor as novas conexões: (anterior, i_new) e (i_new, posterior) 
        self.__rotear_veiculo(k, anterior, i_new, solucao)
        self.__atualizar_variaveis_temporais(k, anterior, i_new, solucao)

        self.__rotear_veiculo(k, i_new, posterior, solucao)
        self.__atualizar_variaveis_temporais(k, i_new, posterior, solucao)

    def __propaga_alteracoes_veiculos(self, k, inicio_atendimento_lote, solucao: Solucao) -> None:
        """Propaga as alterações do Swap nas variáveis temporais e espaciais."""
        lotes_atendimento_posterior = sorted([l for l in self.dados.L if solucao.S[k - 1][l - 1] == 1 and solucao.B[k - 1][l - 1] > inicio_atendimento_lote], key=lambda l: solucao.B[k - 1][l - 1])
        for j in lotes_atendimento_posterior:
            i = self.__get_lote_atendimento_anterior(k, j, solucao)
            self.__rotear_veiculo(k, i, j, solucao)
            self.__atualizar_variaveis_temporais(k, i, j, solucao)

    def __get_lote_atendimento_anterior(self, k, j, solucao: Solucao) -> int:
        return next(i for i in range(self.dados.nL + 1) if solucao.X[k - 1][i][j] == 1)
    
    def __get_lote_atendimento_posterior(self, k, i, solucao: Solucao) -> int:
        return next(j for j in range(1, self.dados.nL + 2) if solucao.X[k - 1][i][j] == 1)
    
    def __lotes_nao_atendidos_veiculos(self, solucao: Solucao) -> list:
        """Encontra uma lista de lotes que nenhum veículo atendeu ainda."""
        lotes_atendidos = set()
        for v in self.dados.V:
            for l in self.dados.L:
                if solucao.S[v - 1][l - 1] == 1:
                    lotes_atendidos.add(l - 1)
        
        return [lote for lote in self.dados.L if lote - 1 not in lotes_atendidos]
            
    def __ultimo_lote_atendido_veiculo(self, k, solucao: Solucao) -> int:
        """Encontra o ultimo lote atendido pelo veiculo 'k'"""
        return max((lote for lote in self.dados.L if solucao.S[k - 1][lote - 1] == 1), key=lambda lote: solucao.B[k - 1][lote - 1], default=None)

    def __ultimo_tallhao_atendido_empilhadeira(self, e, solucao: Solucao) -> int:
        """Encontra o ultimo talhão atendido pela empilhadeira 'e'"""
        return max((talhao for talhao in self.dados.T if solucao.Z[e - 1][talhao - 1] == 1), key=lambda talhao: solucao.C[e - 1][talhao], default=None)
    
    def __get_talhao_from_lote(self, i) -> int:
        for a in self.dados.T:
            if self.dados.LE[a][i] == 1:
                return a
        return None
    
    def __get_proximo_lote(self, lote_inicial, lotes_permitidos, random_selection = True) -> int:
        """Escolhe o próximo lote a ser atendido."""
        if random_selection:
            return random.choice(lotes_permitidos)
        else:
            # Escolhe o melhor lote baseado no tempo de deslocamento
            melhor_lote = (lambda lista: min(lista, key=(lambda j: self.dados.T_volta[lote_inicial - 1] + self.dados.T_ida[j - 1])))
            return melhor_lote(lotes_permitidos)

    def __selecionar_veiculo_livre(self, solucao: Solucao) -> tuple[int, bool]:
        """Seleciona um veículo que não atendeu nenhum lote ainda ou o que finalizou primeiro."""
        for k in self.dados.V:
            if self.__is_primeiro_atendimento(k, solucao):
                return k

        return min(
            self.dados.V,
            key=lambda v: max(
                solucao.H[i] for i in range(self.dados.nL)
                if solucao.S[v - 1][i] == 1
            )
        )
    
    def __is_primeiro_atendimento(self, k, solucao: Solucao) -> bool:
        """Verifica se o veículo ainda não atendeu nenhum lote."""
        return self.__ultimo_lote_atendido_veiculo(k, solucao) is None  
    
    def __get_talhoes_iniciados(self, solucao: Solucao) -> set:
        """Talhões em que o atendimento já começou."""
        return {
                self.__get_talhao_from_lote(l - 1)
                    for v in self.dados.V
                        for l in self.dados.L
                            if solucao.S[v - 1][l - 1] == 1
            }
    
    def __selecionar_talhoes_iniciados_nao_finalizados(self, solucao: Solucao) -> set:
        """Talhões em que o atendimento já começou, mas ainda não finalizou"""
        talhoes_iniciados = self.__get_talhoes_iniciados(solucao)
        return {
                talhao
                for talhao in talhoes_iniciados
                if sum(
                    solucao.S[v - 1][l - 1] == 1
                        for v in self.dados.V
                            for l in self.dados.L
                                if self.__get_talhao_from_lote(l - 1) == talhao
                ) != self.dados.LT[talhao - 1]
            }

    def __selecionar_lotes_talhoes_pendentes(self, lotes_permitidos, solucao: Solucao) -> list:
        """Seleciona lotes em que o atendimento já começou, mas ainda não finalizou"""
        talhoes = self.__selecionar_talhoes_iniciados_nao_finalizados(solucao)
        lotes_prioritarios = [l for l in lotes_permitidos if self.__get_talhao_from_lote(l - 1) in talhoes]
        return lotes_prioritarios

    def __rotear_veiculo(self, k, i, j, solucao: Solucao) -> None:
        """Preenche as variáveis X[k][i][j] e S[k][j] com os respectivos indices."""
        solucao.X[k - 1][i][j] = 1
        solucao.S[k - 1][j - 1] = 1

    def __atualizar_variaveis_temporais(self, k, i, j, solucao: Solucao) -> None:
        """Preenche as variáveis W[k][j], B[k][j], D[k][j] e H[j]"""
        # Tratamento para lotes no mesmo talhão
        proximo_talhao = self.__get_talhao_from_lote(j - 1)
        if (i == 0): # garagem
            tempo_minimo_chegada_proximo_talhao = self.dados.T_ida[j - 1]
        else:
            tempo_minimo_chegada_proximo_talhao = solucao.D[k - 1][i - 1] + self.dados.TC + self.dados.T_volta[i - 1] + self.dados.T_ida[j - 1]

        tempo_inicio_atendimento_ultimo_veiculo_lote = max(
            (
                solucao.D[v - 1][l] for v in self.dados.V if v != k 
                for l in range(self.dados.nL) if self.__get_talhao_from_lote(l) == proximo_talhao and solucao.S[v - 1][l] == 1
            ),
            default=0
        )

        tempo_espera_atendimento_proximo_talhao = 0
        if tempo_inicio_atendimento_ultimo_veiculo_lote > 0:
            tempo_espera_atendimento_proximo_talhao = tempo_inicio_atendimento_ultimo_veiculo_lote + self.dados.TC - tempo_minimo_chegada_proximo_talhao

        if tempo_espera_atendimento_proximo_talhao > 0:
            solucao.W[k - 1][j - 1] = tempo_espera_atendimento_proximo_talhao

        # Atualiza demais variáveis temporais
        solucao.B[k - 1][j - 1] = tempo_minimo_chegada_proximo_talhao # + solucao.W[k - 1][i - 1] # + self.dados.TC
        solucao.D[k - 1][j - 1] = solucao.B[k - 1][j - 1] + solucao.W[k - 1][j - 1]
        solucao.H[j - 1] = solucao.D[k - 1][j - 1]

    def __rotear_veiculos_volta_garagem(self, solucao: Solucao) -> None:
        """Preenche a variável X[k][0][i], representando a volta do veiculo para garagem."""
        for k in self.dados.V:
            i = self.__ultimo_lote_atendido_veiculo(k, solucao)
            solucao.X[k - 1][i][self.dados.nL + 1] = 1
