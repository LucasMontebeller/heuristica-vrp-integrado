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

        lotes_nao_atendidos = self.__get_lotes_nao_atendidos(solucao)
        while len(lotes_nao_atendidos) != 0:
            k = self.__selecionar_veiculo_aleatorio()

            ultimo_lote_veiculo = self.__ultimo_lote_atendido_veiculo(k, solucao) or 0
            if ultimo_lote_veiculo != 0:
                veiculo_tempo_inicio_atendimento_ultimo_lote = max(solucao.H[i -1] for i in self.dados.L if i == ultimo_lote_veiculo)  

            proximo_lote = self.__selecionar_proximo_lote_aleatorio(lotes_nao_atendidos)
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
                    if ultimo_talhao == 0: # primeiro atendimento da empilhadeira
                        empilhadeira_inicio_atendimento_ultimo_lote = 0
                        if ultimo_lote_veiculo == 0: # primeiro atendimento do veiculo
                            tempo_chegada_proximo_talhao = self.dados.T_ida[proximo_lote - 1]
                        else:
                            tempo_chegada_proximo_talhao = veiculo_tempo_inicio_atendimento_ultimo_lote + self.dados.TC + self.dados.T_volta[ultimo_lote_veiculo - 1] + self.dados.T_ida[proximo_lote - 1]
                    else:
                        empilhadeira_inicio_atendimento_ultimo_lote = max(solucao.H[i -1] for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == ultimo_talhao)
                        tempo_chegada_proximo_talhao = empilhadeira_inicio_atendimento_ultimo_lote + self.dados.TC + self.dados.DE[ultimo_talhao][proximo_talhao]

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
                tempo_minimo_chegada_proximo_lote = veiculo_tempo_inicio_atendimento_ultimo_lote + self.dados.TC + self.dados.T_volta[ultimo_lote_veiculo - 1] + self.dados.T_ida[proximo_lote - 1]

            solucao.B[k - 1][proximo_lote - 1] = tempo_minimo_chegada_proximo_lote
            solucao.W[k - 1][proximo_lote - 1] = max(0, empilhadeira_inicio_atendimento_proximo_lote - tempo_minimo_chegada_proximo_lote)  # Tempo de espera do veículo
            solucao.D[k - 1][proximo_lote - 1] = tempo_minimo_chegada_proximo_lote + solucao.W[k - 1][proximo_lote - 1]
            solucao.H[proximo_lote - 1] = solucao.D[k - 1][proximo_lote - 1]

            lotes_nao_atendidos.remove(proximo_lote)

        # Os veiculos devem terminar na garagem
        # Isso não gera nenhum impacto no resultado, apenas garante integridade
        self.__rotear_veiculos_volta_garagem(solucao)

        # Atualizar makespan
        solucao.M = max(solucao.H) # - self.dados.TC. # Agora essa variável representa o instante de atendimento do ultimo lote (ajustar na dissertação).

        return solucao
    
    def gera_solucao_vizinha(self, solucao: Solucao) -> Solucao:
        """Gera uma solução vizinha para o problema."""

        raise NotImplementedError('Função não implementada ainda!')
        
        
    def __get_lotes_nao_atendidos(self, solucao: Solucao) -> list:
        """Retorna uma lista de lotes ainda não atendidos."""
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
        """Retorna o talhão que o lote está contido."""
        for a in self.dados.T:
            if self.dados.LE[a][i] == 1:
                return a
            
        return None
    
    def __selecionar_proximo_lote_aleatorio(self, lotes_permitidos) -> int:
        """Escolhe o próximo lote a ser atendido baseado na lista permitida."""
        return random.choice(lotes_permitidos)

    def __selecionar_veiculo_aleatorio(self) -> int:
        """Seleciona um veículo aleatório."""
        return random.choice([k for k in self.dados.V])
    
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

    def __rotear_veiculo(self, k, i, j, solucao: Solucao) -> None:
        """Preenche as variáveis X[k][i][j] e S[k][j] com os respectivos indices."""
        solucao.X[k - 1][i][j] = 1
        solucao.S[k - 1][j - 1] = 1

    def __rotear_veiculos_volta_garagem(self, solucao: Solucao) -> None:
        """Preenche a variável X[k][0][i], representando a volta do veiculo para garagem."""
        for k in self.dados.V:
            i = self.__ultimo_lote_atendido_veiculo(k, solucao) or 0
            solucao.X[k - 1][i][self.dados.nL + 1] = 1
    
    def __selecionar_empilhadeira_livre(self, solucao: Solucao) -> int:
        """Seleciona uma empilhadeira que não atendeu nenhum talhão ainda ou alguma que já finalizou. Ambas de forma aleatória."""
        empilhadeiras_nao_atenderam = [e for e in self.dados.E if self.__ultimo_talhao_atendido_empilhadeira(e, solucao) is None]
        if empilhadeiras_nao_atenderam:
            return random.choice(empilhadeiras_nao_atenderam)

        empilhadeiras_candidatas = [e for e in self.dados.E if self.__todos_lotes_atendidos(e, solucao)]
        if len(empilhadeiras_candidatas) == 0:
            return None
        
        return random.choice(empilhadeiras_candidatas)

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