import random
from copy import deepcopy
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
        while lotes_nao_atendidos:
            k = self.__selecionar_veiculo_aleatorio()
            ultimo_lote_veiculo = self.__ultimo_lote_atendido_veiculo(k, solucao)
            tempo_inicio_atendimento_ultimo_lote_veiculo = self.__get_tempo_inicio_atendimento_lote_veiculo(ultimo_lote_veiculo, k, solucao)

            proximo_lote = self.__selecionar_proximo_lote_aleatorio(lotes_nao_atendidos)
            proximo_talhao = self.__get_talhao_from_lote(proximo_lote - 1)

            e = self.__get_empilhadeira_talhao(proximo_talhao, solucao)
            if e is not None:
                empilhadeira_inicio_atendimento_ultimo_lote = self.__get_tempo_inicio_atendimento_ultimo_lote(proximo_talhao, solucao)
                empilhadeira_inicio_atendimento_proximo_lote = empilhadeira_inicio_atendimento_ultimo_lote + self.dados.TC
            else:
                e = self.__selecionar_empilhadeira_livre(solucao)
                if self.__empilhadeira_apta_deslocamento_talhao(e, solucao):          
                    ultimo_talhao = self.__ultimo_talhao_atendido_empilhadeira(e, solucao) or 0    
                    empilhadeira_inicio_atendimento_proximo_lote = self.__get_tempo_chegada_proximo_talhao_empilhadeira(ultimo_talhao, proximo_talhao, ultimo_lote_veiculo, proximo_lote, tempo_inicio_atendimento_ultimo_lote_veiculo, solucao)

                    self.__rotear_empilhadeira(e, ultimo_talhao, proximo_talhao, solucao)
                    self.__set_tempo_chegada_empilhadeira_talhao(e, proximo_talhao, empilhadeira_inicio_atendimento_proximo_lote, solucao)
                else:
                    # Impossivel fazer o roteamento. É necessário fazer outra escolha de veículo e lote.
                    continue
            
            self.__rotear_veiculo(k, ultimo_lote_veiculo, proximo_lote, solucao)
            self.__atualizar_variaveis_temporais_veiculo(k, ultimo_lote_veiculo, proximo_lote, tempo_inicio_atendimento_ultimo_lote_veiculo, empilhadeira_inicio_atendimento_proximo_lote, solucao)

            lotes_nao_atendidos.remove(proximo_lote)

        # Os veiculos devem terminar na garagem
        # Isso não gera nenhum impacto no resultado, apenas garante integridade
        self.__rotear_veiculos_volta_garagem(solucao)

        self.__atualizar_makespan(solucao)

        return solucao
    
    def gera_solucao_vizinha(self, solucao: Solucao, qtde_swaps: int = 1) -> Solucao:
        """Gera uma solução vizinha para o problema. Consiste no swap de lotes entre veículos."""
        sequencia_atendimento_empilhadeira_original = dict()
        for e in self.dados.E:
            sequencia_atendimento_empilhadeira_original[e] = sorted((talhao for talhao in self.dados.T if solucao.Z[e - 1][talhao - 1] == 1), key=lambda talhao: solucao.C[e - 1][talhao])

        sequencia_atendimento_veiculo_original = dict()
        for k in self.dados.V:
            sequencia_atendimento_veiculo_original[k] = sorted(
            ((lote, solucao.H[lote - 1]) for lote in self.dados.L if solucao.S[k - 1][lote - 1] == 1),
            key=lambda item: solucao.D[k - 1][item[0] - 1]
        )

        if len(sequencia_atendimento_veiculo_original) < 2:
            raise ValueError("Não é possível gerar uma solução vizinha com menos de dois veículos.")

        # Loop força encontrar uma solução vizinha
        lotes_nao_atendidos = [0] # Apenas para entrar no loop
        maximo_swap = self.__get_numero_maximo_swap(sequencia_atendimento_veiculo_original)
        cont_swap = 0
        while lotes_nao_atendidos and cont_swap < maximo_swap:
            sol_vizinha = Solucao(self.dados)
            sequencia_atendimento_empilhadeira = deepcopy(sequencia_atendimento_empilhadeira_original)
            sequencia_atendimento_veiculo = deepcopy(sequencia_atendimento_veiculo_original)

            # 1) Passo 1: Pegar o lote de um veiculo e colocar em outro, de forma aleatória.
            for _ in range(qtde_swaps):
                k_old = random.choice([k for k in self.dados.V if len(sequencia_atendimento_veiculo[k]) > 0])
                k_new = random.choice([k for k in self.dados.V if k != k_old])

                lote_swap = random.choice(sequencia_atendimento_veiculo[k_old])
                sequencia_atendimento_veiculo[k_old].remove(lote_swap)
                posicao_swap = random.choice(range(len(sequencia_atendimento_veiculo[k_new]) + 1))
                sequencia_atendimento_veiculo[k_new].insert(posicao_swap, lote_swap)

            # 2) Passo 2: Chamar um metodo similar a gera_solucao_aleatoria para recalcular a solução. 
            # A diferença é que agora a sequência de atendimento já está definida. 
            # Caso não seja possivel, alterar a posição do novo lote a ser atendido e rodar novamente.
            lotes_nao_atendidos = self.__get_lotes_nao_atendidos(sol_vizinha)
            cont = 0
            while lotes_nao_atendidos and cont <= 10:
                k = min((k for k in sequencia_atendimento_veiculo.keys()), key=lambda k: sequencia_atendimento_veiculo[k][0][1] if sequencia_atendimento_veiculo[k] else float('inf'))
                ultimo_lote_veiculo = self.__ultimo_lote_atendido_veiculo(k, sol_vizinha)
                tempo_inicio_atendimento_ultimo_lote_veiculo = self.__get_tempo_inicio_atendimento_lote_veiculo(ultimo_lote_veiculo, k, sol_vizinha)

                lote_tempo = sequencia_atendimento_veiculo[k][0]
                proximo_lote = lote_tempo[0]
                proximo_talhao = self.__get_talhao_from_lote(proximo_lote - 1)

                e = self.__get_empilhadeira_talhao(proximo_talhao, sol_vizinha)
                if e is not None:
                    empilhadeira_inicio_atendimento_ultimo_lote = self.__get_tempo_inicio_atendimento_ultimo_lote(proximo_talhao, sol_vizinha)
                    empilhadeira_inicio_atendimento_proximo_lote = empilhadeira_inicio_atendimento_ultimo_lote + self.dados.TC
                else:
                    e = next((key for key, value in sequencia_atendimento_empilhadeira.items() if proximo_talhao in value), None)
                    if self.__empilhadeira_apta_deslocamento_talhao(e, sol_vizinha):          
                        ultimo_talhao = self.__ultimo_talhao_atendido_empilhadeira(e, sol_vizinha) or 0    
                        empilhadeira_inicio_atendimento_proximo_lote = self.__get_tempo_chegada_proximo_talhao_empilhadeira(ultimo_talhao, proximo_talhao, ultimo_lote_veiculo, proximo_lote, tempo_inicio_atendimento_ultimo_lote_veiculo, sol_vizinha)

                        self.__rotear_empilhadeira(e, ultimo_talhao, proximo_talhao, sol_vizinha)
                        self.__set_tempo_chegada_empilhadeira_talhao(e, proximo_talhao, empilhadeira_inicio_atendimento_proximo_lote, sol_vizinha)
                    else:
                        # Impossivel fazer o roteamento. É necessário fazer outra escolha de veículo e lote.
                        cont += 1
                        continue
                
                self.__rotear_veiculo(k, ultimo_lote_veiculo, proximo_lote, sol_vizinha)
                self.__atualizar_variaveis_temporais_veiculo(k, ultimo_lote_veiculo, proximo_lote, tempo_inicio_atendimento_ultimo_lote_veiculo, empilhadeira_inicio_atendimento_proximo_lote, sol_vizinha)

                sequencia_atendimento_veiculo[k].remove(lote_tempo)
                lotes_nao_atendidos.remove(proximo_lote)
                cont = 0

            cont_swap += 1

        if lotes_nao_atendidos:
            raise ValueError("Não foi possível gerar uma solução vizinha.")
        
        # Os veiculos devem terminar na garagem
        # Isso não gera nenhum impacto no resultado, apenas garante integridade
        self.__rotear_veiculos_volta_garagem(sol_vizinha)

        self.__atualizar_makespan(sol_vizinha)
        
        return sol_vizinha
        
    def __get_lotes_nao_atendidos(self, solucao: Solucao) -> list:
        """Retorna uma lista de lotes ainda não atendidos."""
        lotes_atendidos = set()
        for v in self.dados.V:
            for l in self.dados.L:
                if solucao.S[v - 1][l - 1] == 1:
                    lotes_atendidos.add(l - 1)
        
        return [lote for lote in self.dados.L if lote - 1 not in lotes_atendidos]
        
    def __selecionar_veiculo_aleatorio(self) -> int:
        """Seleciona um veículo aleatório."""
        return random.choice([k for k in self.dados.V])
    
    def __ultimo_lote_atendido_veiculo(self, k: int, solucao: Solucao) -> int:
        """Encontra o ultimo lote atendido pelo veiculo 'k'"""
        return max((lote for lote in self.dados.L if solucao.S[k - 1][lote - 1] == 1), key=lambda lote: solucao.B[k - 1][lote - 1], default=0)
    
    def __get_tempo_inicio_atendimento_lote_veiculo(self, i: int, k: int, solucao: Solucao) -> float:
        """Retorna o tempo de inicio de atendimento do lote pelo veículo 'k'"""
        return solucao.D[k -1][i - 1]

    def __selecionar_proximo_lote_aleatorio(self, lotes_permitidos: list) -> int:
        """Escolhe o próximo lote a ser atendido baseado na lista permitida."""
        return random.choice(lotes_permitidos)
    
    def __get_talhao_from_lote(self, i: int) -> int:
        """Retorna o talhão que o lote está contido."""
        for a in self.dados.T:
            if self.dados.LE[a][i] == 1:
                return a
            
        return None
    
    def __get_empilhadeira_talhao(self, talhao: int, solucao: Solucao) -> int:
        """Retorna a empilhadeira 'e' que está atendendo o talhão"""
        return next((e for e in self.dados.E if solucao.C[e - 1][talhao] != 0), None)
    
    def __get_tempo_inicio_atendimento_ultimo_lote(self, talhao: int, solucao: Solucao) -> float:
        "Retorna o tempo de inicio de atendimento do ultimo lote com base no talhão"
        return max(solucao.H[i - 1] for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == talhao)
    
    def __selecionar_empilhadeira_livre(self, solucao: Solucao) -> int:
        """Seleciona uma empilhadeira que não atendeu nenhum talhão ainda ou alguma que já finalizou. Ambas de forma aleatória."""
        empilhadeiras_nao_atenderam = [e for e in self.dados.E if self.__ultimo_talhao_atendido_empilhadeira(e, solucao) is None]
        if empilhadeiras_nao_atenderam:
            return random.choice(empilhadeiras_nao_atenderam)

        empilhadeiras_candidatas = [e for e in self.dados.E if self.__todos_lotes_atendidos(e, solucao)]
        if len(empilhadeiras_candidatas) == 0:
            return None
        
        return random.choice(empilhadeiras_candidatas)
    
    def __empilhadeira_apta_deslocamento_talhao(self, e: int, solucao: Solucao) -> bool:
        """Verifica se a empilhadeira 'e' pode se deslocar para outro talhão."""
        return e is not None and (self.__is_primeiro_atendimento_empilhadeira(e, solucao) or self.__todos_lotes_atendidos(e, solucao))
    
    def __is_primeiro_atendimento_empilhadeira(self, e: int, solucao: Solucao) -> bool:
        """Verifica se a empilhadeira ainda não atendeu nenhum lote."""
        return self.__ultimo_talhao_atendido_empilhadeira(e, solucao) is None  
    
    def __todos_lotes_atendidos(self, e: int, solucao: Solucao) -> bool:
        """Verifica se a empilhadeira 'e' atendeu todos os lotes do seu ultimo talhão."""
        ultimo_talhao = self.__ultimo_talhao_atendido_empilhadeira(e, solucao)
        return ultimo_talhao not in self.__selecionar_talhoes_iniciados_nao_finalizados(solucao)
    
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
    
    def __get_talhoes_iniciados(self, solucao: Solucao) -> set:
        """Talhões em que o atendimento já começou."""
        return {
                self.__get_talhao_from_lote(l - 1)
                    for v in self.dados.V
                        for l in self.dados.L
                            if solucao.S[v - 1][l - 1] == 1
            }
    
    def __ultimo_talhao_atendido_empilhadeira(self, e: int, solucao: Solucao) -> int:
        """Encontra o ultimo talhão atendido pela empilhadeira 'e'"""
        return max((talhao for talhao in self.dados.T if solucao.Z[e - 1][talhao - 1] == 1), key=lambda talhao: solucao.C[e - 1][talhao], default=None)
    
    def __get_tempo_chegada_proximo_talhao_empilhadeira(self, ultimo_talhao: int, proximo_talhao: int, ultimo_lote_veiculo: int, proximo_lote: int, tempo_inicio_atendimento_ultimo_lote_veiculo: float, solucao: Solucao) -> float:
        """Retorna o tempo de chegada da empilhadeira no próximo talhão a ser atendido"""
        if ultimo_talhao == 0: # primeiro atendimento da empilhadeira
            if ultimo_lote_veiculo == 0: # primeiro atendimento do veiculo
                tempo_chegada_proximo_talhao = self.dados.T_ida[proximo_lote - 1]
            else:
                tempo_chegada_proximo_talhao = tempo_inicio_atendimento_ultimo_lote_veiculo + self.dados.TC + self.dados.T_volta[ultimo_lote_veiculo - 1] + self.dados.T_ida[proximo_lote - 1]
        else:
            empilhadeira_inicio_atendimento_ultimo_lote = max(solucao.H[i -1] for i in self.dados.L if self.__get_talhao_from_lote(i - 1) == ultimo_talhao)
            tempo_chegada_proximo_talhao = empilhadeira_inicio_atendimento_ultimo_lote + self.dados.TC + self.dados.DE[ultimo_talhao][proximo_talhao]

        return tempo_chegada_proximo_talhao
    
    def __rotear_empilhadeira(self, e: int, a: int, b: int, solucao: Solucao) -> None:
        """Preenche as variáveis Y[e][a][b] e Z[e][b] com os respectivos indices."""
        solucao.Y[e - 1][a][b] = 1
        solucao.Z[e - 1][b - 1] = 1

    def __set_tempo_chegada_empilhadeira_talhao(self, e: int, talhao: int, tempo: float, solucao: Solucao) -> None:
        """Preenche a variável C[e][b], representando o tempo de chegada da empilhadeira no talhao."""
        solucao.C[e - 1][talhao] = tempo
    
    def __rotear_veiculo(self, k: int, i: int, j: int, solucao: Solucao) -> None:
        """Preenche as variáveis X[k][i][j] e S[k][j] com os respectivos indices."""
        solucao.X[k - 1][i][j] = 1
        solucao.S[k - 1][j - 1] = 1

    def __atualizar_variaveis_temporais_veiculo(self, k: int, ultimo_lote_veiculo: int, proximo_lote: int, tempo_inicio_atendimento_ultimo_lote_veiculo: float, empilhadeira_inicio_atendimento_proximo_lote: float, solucao: Solucao) -> None:
        """Preenche as variáveis B[k][i], W[k][i], D[k][i] e H[i], representando os tempos de chegada, atraso e atendimento do veículo 'k', respectivamente"""
        if ultimo_lote_veiculo == 0: # garagem
            tempo_minimo_chegada_proximo_lote = self.dados.T_ida[proximo_lote - 1]
        else:
            tempo_minimo_chegada_proximo_lote = tempo_inicio_atendimento_ultimo_lote_veiculo + self.dados.TC + self.dados.T_volta[ultimo_lote_veiculo - 1] + self.dados.T_ida[proximo_lote - 1]

        solucao.B[k - 1][proximo_lote - 1] = tempo_minimo_chegada_proximo_lote
        solucao.W[k - 1][proximo_lote - 1] = max(0, empilhadeira_inicio_atendimento_proximo_lote - tempo_minimo_chegada_proximo_lote)  # Tempo de espera do veículo
        solucao.D[k - 1][proximo_lote - 1] = tempo_minimo_chegada_proximo_lote + solucao.W[k - 1][proximo_lote - 1]
        solucao.H[proximo_lote - 1] = solucao.D[k - 1][proximo_lote - 1]

    def __rotear_veiculos_volta_garagem(self, solucao: Solucao) -> None:
        """Preenche a variável X[k][i][nL + 1], representando a volta do veiculo para garagem."""
        for k in self.dados.V:
            i = self.__ultimo_lote_atendido_veiculo(k, solucao) or 0
            solucao.X[k - 1][i][self.dados.nL + 1] = 1

    def __atualizar_makespan(self, solucao: Solucao) -> None:
        """Atualiza a variável makespan 'M'."""
        solucao.M = max(solucao.H)

    def __get_numero_maximo_swap(self, sequencia_atendimento_veiculo_original: dict) -> int:
        """Retorna o número máximo de swaps possíveis."""
        maximo_swap = 0
        for k_old in self.dados.V:
            n_old = len(sequencia_atendimento_veiculo_original[k_old])
            for k_new in self.dados.V:
                if k_old == k_new:
                    continue
                n_new = len(sequencia_atendimento_veiculo_original[k_new])
                maximo_swap += n_old * (n_new + 1)

        return maximo_swap