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
        self.__rotear_veiculos(solucao)
        # self.__rotear_empilhadeiras(solucao)

        # Atualizar makespan
        solucao.M = max(solucao.H) # - self.dados.TC. # Agora essa variável representa o instante de atendimento do ultimo lote (ajustar na dissertação).

        return solucao
    
    def gera_solucao_vizinha(self, solucao: Solucao) -> Solucao:
        """Gera uma solução vizinha para o problema."""

        raise NotImplementedError('Função não implementada ainda!')

    def __rotear_veiculos(self, solucao: Solucao) -> None:
        """Gera arcos aleatórios para os veículos, preenchendo as respectivas variáveis na solução."""
        lotes_nao_atendidos = self.__lotes_nao_atendidos_veiculos(solucao)
        while len(lotes_nao_atendidos) != 0:
            k = self.__selecionar_veiculo_livre(solucao)

            ultimo_lote_veiculo = self.__ultimo_lote_atendido_veiculo(k, solucao) or 0    

            proximo_lote = self.__get_proximo_lote(0, lotes_nao_atendidos, True)
            proximo_talhao = self.__get_talhao_from_lote(proximo_lote - 1)

            # É possivel o próximo lote ser atendido?

            # 1) Existe alguma empilhadeira neste talhão?
            e = next((e for e in self.dados.E if solucao.C[e - 1][proximo_talhao] != 0), None)
            if e is not None:
                empilhadeira_inicio_atendimento_ultimo_lote = max(solucao.H[i -1] for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == proximo_talhao)
                empilhadeira_inicio_atendimento_proximo_lote = empilhadeira_inicio_atendimento_ultimo_lote + self.dados.TC

            # 2) Caso contrário, deve existir alguma empilhadeira livre capaz de ir até seu respectivo talhão.
            else:
                e = self.__selecionar_empilhadeira_livre(solucao)
                if e is not None and self.__empilhadeira_apta_deslocamento_talhao(e, solucao):          
                    ultimo_talhao = self.__ultimo_talhao_atendido_empilhadeira(e, solucao) or 0               
                    empilhadeira_inicio_atendimento_ultimo_lote = max(solucao.H[i -1] for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == ultimo_talhao) if ultimo_lote_veiculo != 0 else self.dados.T_ida[proximo_lote - 1]
                    tempo_chegada_proximo_talhao = empilhadeira_inicio_atendimento_ultimo_lote
                    if ultimo_talhao != 0:
                        tempo_chegada_proximo_talhao += self.dados.TC + self.dados.DE[ultimo_talhao][proximo_talhao]

                    empilhadeira_inicio_atendimento_proximo_lote = tempo_chegada_proximo_talhao
                    self.__rotear_empilhadeira(e, ultimo_talhao, proximo_talhao, solucao)
                    self.__set_tempo_chegada_empilhadeira_talhao(e, proximo_talhao, tempo_chegada_proximo_talhao, solucao)
                else:
                    # 3) Senão, é impossivel fazer o roteamento. É necessário escolher outro conjunto de dados (verificar possibilidade).
                    continue
            
            # Veiculos
            self.__rotear_veiculo(k, ultimo_lote_veiculo, proximo_lote, solucao)

            # Atualizar variáveis temporais do veiculo
            if ultimo_lote_veiculo == 0: # garagem
                tempo_minimo_chegada_proximo_lote = self.dados.T_ida[proximo_lote - 1]
            else:
                veiculo_tempo_inicio_atendimento_ultimo_lote = empilhadeira_inicio_atendimento_ultimo_lote 
                tempo_minimo_chegada_proximo_lote = veiculo_tempo_inicio_atendimento_ultimo_lote + self.dados.TC + self.dados.T_volta[ultimo_lote_veiculo - 1] + self.dados.T_ida[proximo_lote - 1]

            solucao.B[k - 1][proximo_lote - 1] = tempo_minimo_chegada_proximo_lote
            solucao.W[k - 1][proximo_lote - 1] = max(0, empilhadeira_inicio_atendimento_proximo_lote - tempo_minimo_chegada_proximo_lote)  # Tempo de espera do veículo
            solucao.D[k - 1][proximo_lote - 1] = tempo_minimo_chegada_proximo_lote + solucao.W[k - 1][proximo_lote - 1]
            solucao.H[proximo_lote - 1] = solucao.D[k - 1][proximo_lote - 1]

            lotes_nao_atendidos.remove(proximo_lote)

        # Os veiculos devem terminar na garagem
        # Isso não gera nenhum impacto no resultado, apenas garante integridade
        self.__rotear_veiculos_volta_garagem(solucao)

    def __rotear_empilhadeiras(self, solucao: Solucao) -> None:
        """Sequencia as empilhadeiras para atender os veiculos, preenchendo as respectivas variáveis na solução."""
        # Passo 1: Montar a lista de eventos
        eventos = []
        for lote in range(self.dados.nL):
            for k in self.dados.V:
                if solucao.S[k - 1][lote] == 1:  # Verifica se o veículo k atende o lote
                    eventos.append((solucao.B[k - 1][lote], lote, k))  # (tempo_chegada_veiculo, lote, veiculo)

        # Passo 2: Ordenar os eventos pela chegada
        eventos.sort()

        # Estruturas auxiliares
        empilhadeira_em_talhao = {}  # Armazena qual empilhadeira está em qual talhão e o tempo que estará livre
        empilhadeiras_livres = [e for e in self.dados.E]  # Lista de empilhadeiras livres
        lotes_standby = []  # Lotes que precisam de empilhadeira mas não tem disponível ainda

        # Passo 3: Processar os eventos de acordo com a chegada dos veículos
        for tempo_chegada_veiculo, lote, veiculo in eventos:
            # NOVO: Verificar se o veiculo está bloqueado em outro atendimento pendente
            if any(item[2] == [veiculo] for item in lotes_standby):
                continue  # Pule este evento por agora (o veículo está preso aguardando outro lote)

            talhao = self.__get_talhao_from_lote(lote)

            # Passo 4: Verificar se tem empilhadeira disponível para o talhão
            if talhao in empilhadeira_em_talhao:
                # Tem empilhadeira disponível, o atendimento pode começar
                empilhadeira, tempo_disponivel = empilhadeira_em_talhao[talhao]
                tempo_inicio_atendimento = max(tempo_chegada_veiculo, tempo_disponivel)

                # Registrar o tempo de atendimento do veículo
                solucao.W[veiculo - 1][lote] = max(0, tempo_inicio_atendimento - tempo_chegada_veiculo)  # Tempo de espera do veículo
                solucao.D[veiculo - 1][lote] = tempo_chegada_veiculo + solucao.W[veiculo - 1][lote]
                solucao.H[lote] = solucao.D[veiculo - 1][lote]  # Atualiza o tempo de atendimento do lote

                # Atualizar o tempo de liberação da empilhadeira
                empilhadeira_em_talhao[talhao] = (empilhadeira, tempo_inicio_atendimento + self.dados.TC)

            else:
                # Não tem empilhadeira no talhão, então vamos tentar alocar uma empilhadeira livre
                if empilhadeiras_livres:
                    empilhadeira = empilhadeiras_livres.pop(0)  # Pega a primeira empilhadeira livre
                    tempo_chegada_empilhadeira = tempo_chegada_veiculo  # O tempo que a empilhadeira chega ao talhão

                    # Registrar o tempo de chegada da empilhadeira ao talhão
                    solucao.C[empilhadeira - 1][talhao] = tempo_chegada_empilhadeira

                    # Registrar o tempo de atendimento
                    solucao.W[veiculo - 1][lote] = max(0, tempo_chegada_empilhadeira - tempo_chegada_veiculo)
                    solucao.D[veiculo - 1][lote] = tempo_chegada_veiculo + solucao.W[veiculo - 1][lote]
                    solucao.H[lote] = solucao.D[veiculo - 1][lote]

                    # Adicionar a empilhadeira ao talhão
                    empilhadeira_em_talhao[talhao] = (empilhadeira, tempo_chegada_empilhadeira + self.dados.TC)

                else:
                    # Não há empilhadeiras livres para deslocar, então coloca o lote em stand-by
                    lotes_standby.append((tempo_chegada_veiculo, lote, veiculo))

            # Passo 5: Após todos os eventos principais, alocar empilhadeiras para os lotes em stand-by
            # Tentar alocar empilhadeira para lotes em stand-by
            for tempo_chegada_standby, lote_standby, veiculo_standby in lotes_standby:
                talhao_standby = self.__get_talhao_from_lote(lote_standby)

                # Verificar se existe empilhadeira disponível para este talhão
                if talhao_standby in empilhadeira_em_talhao:
                    empilhadeira, tempo_disponivel = empilhadeira_em_talhao[talhao_standby]
                    tempo_inicio_atendimento = max(tempo_chegada_standby, tempo_disponivel)

                    # Registrar o tempo de atendimento
                    solucao.H[lote_standby] = tempo_inicio_atendimento
                    solucao.W[veiculo_standby - 1][lote_standby] = max(0, tempo_inicio_atendimento - tempo_chegada_standby)

                    # Atualizar o tempo de liberação da empilhadeira
                    solucao.C[empilhadeira - 1][talhao_standby] = tempo_inicio_atendimento + self.dados.TE[lote_standby]

                    # Remover lote da fila de stand-by
                    lotes_standby.remove((tempo_chegada_standby, lote_standby, veiculo_standby))
                        
        
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

    def __ultimo_talhao_atendido_empilhadeira(self, e, solucao: Solucao) -> int:
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
        veiculos_nao_atenderam = [k for k in self.dados.V if self.__is_primeiro_atendimento(k, solucao)]
        if veiculos_nao_atenderam:
            return random.choice(veiculos_nao_atenderam)
        
        return min(
            self.dados.V,
            key=lambda k: max(
                solucao.D[k - 1][i - 1] for i in range(self.dados.nL)
                if solucao.S[k - 1][i] == 1
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
        # solucao.D[k - 1][j - 1] = solucao.B[k - 1][j - 1] + solucao.W[k - 1][j - 1]
        # solucao.H[j - 1] = solucao.D[k - 1][j - 1]

    def __atualiza_tempo_chegada_veiculo_lote(self, k, i, j, solucao: Solucao) -> None:
        """Preenche a variável B[k][j]"""
        is_garagem = i == 0

        if is_garagem:
            tempo_minimo_chegada_proximo_lote = self.dados.T_ida[j - 1]
        else:
            tempo_minimo_finaliza_atendimento_ultimo_lote = solucao.B[k - 1][i - 1] + self.dados.TC
            tempo_minimo_chegada_proximo_lote = tempo_minimo_finaliza_atendimento_ultimo_lote + self.dados.T_volta[i - 1] + self.dados.T_ida[j - 1]

        solucao.B[k - 1][j - 1] = tempo_minimo_chegada_proximo_lote

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
        """Seleciona uma empilhadeira que não atendeu nenhum talhão ainda ou alguma que já finalizou."""
        empilhadeiras_nao_atenderam = [e for e in self.dados.E if self.__ultimo_talhao_atendido_empilhadeira(e, solucao) is None]
        if empilhadeiras_nao_atenderam:
            return random.choice(empilhadeiras_nao_atenderam)

        empilhadeiras_candidatas = [e for e in self.dados.E if self.__todos_lotes_atendidos(e, solucao)]
        if len(empilhadeiras_candidatas) == 0:
            return None
        
        return random.choice(empilhadeiras_candidatas)

        # Seleciona a empilhadeira que finalizou o atendimento no seu último talhão mais cedo
        # empilhadeira = None
        # horario_inicio_atendimento = float('inf')
        # for e in empilhadeiras_candidatas:
        #     ultimo_talhao_atendido = self.__ultimo_talhao_atendido_empilhadeira(e, solucao)
        #     ultimo_horario_inicio_atendimento = max(solucao.H[i -1] for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == ultimo_talhao_atendido)
        #     if ultimo_horario_inicio_atendimento < horario_inicio_atendimento:
        #         horario_inicio_atendimento = ultimo_horario_inicio_atendimento
        #         empilhadeira = e

        # return empilhadeira

    def __is_primeiro_atendimento_empilhadeira(self, e, solucao: Solucao) -> bool:
        """Verifica se a empilhadeira ainda não atendeu nenhum lote."""
        return self.__ultimo_talhao_atendido_empilhadeira(e, solucao) is None  
    
    def __rotear_empilhadeira(self, e, a, b, solucao: Solucao) -> None:
        """Preenche as variáveis Y[e][a][b] e Z[e][b] com os respectivos indices."""
        solucao.Y[e - 1][a][b] = 1
        solucao.Z[e - 1][b - 1] = 1

    def __set_tempo_chegada_empilhadeira_talhao(self, e, talhao, tempo, solucao: Solucao) -> None:
        """Preenche a variável C[e][b], representando o tempo de chegada da empilhadeira no talhao."""
        solucao.C[e - 1][talhao] = tempo

    def __todos_lotes_atendidos(self, e, solucao) -> bool:
        """Verifica se a empilhadeira 'e' atendeu todos os lotes do seu ultimo talhão."""
        ultimo_talhao = self.__ultimo_talhao_atendido_empilhadeira(e, solucao)
        return ultimo_talhao not in self.__selecionar_talhoes_iniciados_nao_finalizados(solucao)

    def __empilhadeira_apta_deslocamento_talhao(self, e, solucao) -> bool:
        """Verifica se a empilhadeira 'e' pode se deslocar para outro talhão."""
        return self.__is_primeiro_atendimento_empilhadeira(e, solucao) or self.__todos_lotes_atendidos(e, solucao)