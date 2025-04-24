import random
from solver.dados import Dados
from solver.solucao import Solucao

class Modelo:
    """Representa o modelo que rege o problema, incluido as respectivas restrições."""
    def __init__(self, dados: Dados):
        self.dados = dados

    def gera_solucao_aleatoria(self) -> Solucao:
        """Gera uma solução aleatória para o problema."""

        solucao = Solucao(self.dados)
        self.__add_restricoes_veiculos(solucao)
        self.__add_restricoes_empilhadeiras(solucao)

        # Atualizar makespan
        solucao.M = max(solucao.H) # - self.dados.TC. # Agora essa variável representa o instante de atendimento do ultimo lote (ajustar na dissertação).

        return solucao
    
    def gera_solucao_vizinha(self, solucao: Solucao) -> Solucao:
        """Gera uma solução vizinha para o problema."""

        raise NotImplementedError('Função não implementada ainda!')

    def __add_restricoes_veiculos(self, solucao: Solucao) -> None:
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

    def __add_restricoes_empilhadeiras(self, solucao: Solucao) -> None:
        """Adiciona as restrições relacionadas às empilhadeiras à solução."""
        lotes_por_talhao = self.__get_agrupamento_talhao_lotes()
        
        # Ordena os lotes atendidos pelos veículos
        for talhao, i in lotes_por_talhao.items():
            lotes_por_talhao[talhao] = sorted(i, key=lambda i: solucao.H[i])
        
        for b in lotes_por_talhao:
            e = self.__selecionar_empilhadeira_livre(solucao)
            for i in lotes_por_talhao[b]:
                if self.__is_primeiro_atendimento_empilhadeira(e, solucao): 
                    a = 0
                    self.__rotear_empilhadeira(e, a, b, solucao)
                    solucao.C[e - 1][talhao] = solucao.H[i]

                elif self.__ultimo_tallhao_atendido_empilhadeira(e, solucao) == b: # A empilhadeira está atendendo o talhão ainda
                    pass
                else: # precisará se deslocar para atender o respectivo talhão.
                    pass
        
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

    def __selecionar_veiculo_livre(self, solucao: Solucao) -> int:
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

    def __get_agrupamento_talhao_lotes(self) -> dict[int, list]:
        """Retorna um dicionario com os talhoes e seus respectivos lotes."""
        lotes_por_talhao = {talhao: [] for talhao in self.dados.T}
        for i in range(self.dados.nL):
            talhao = self.__get_talhao_from_lote(i)
            if talhao is not None:
                lotes_por_talhao[talhao].append(i)

        return lotes_por_talhao
    
    def __selecionar_empilhadeira_livre(self, solucao: Solucao) -> int:
        """Seleciona uma empilhadeira que não atendeu nenhum talhão ainda ou o que finalizou primeiro."""
        for e in self.dados.E:
            if self.__ultimo_tallhao_atendido_empilhadeira(e, solucao) is None:
                return e

        return min(
                self.dados.E,
                key=lambda e: max(
                    solucao.H[i] for i in range(self.dados.nL)
                    if solucao.Z[e - 1][self.__get_talhao_from_lote(i) - 1] == 1  # Apenas lotes atendidos pela empilhadeira
                )
            )

    def __is_primeiro_atendimento_empilhadeira(self, e, solucao: Solucao) -> bool:
        """Verifica se a empilhadeira ainda não atendeu nenhum lote."""
        return self.__ultimo_tallhao_atendido_empilhadeira(e, solucao) is None  
    
    def __rotear_empilhadeira(self, e, a, b, solucao: Solucao) -> None:
        """Preenche as variáveis Y[e][a][b] e Z[e][b] com os respectivos indices."""
        solucao.Y[e - 1][a][b] = 1
        solucao.Z[e - 1][b - 1] = 1