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