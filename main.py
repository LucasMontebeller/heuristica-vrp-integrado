class Dados:
    def __init__(self):
        self.V = 3                                            # Total de veículos
        self.E = 2                                            # Total de empilhadeiras
        self.LT = [2, 2, 3]                                   # Total de lotes em cada talhão 'a'
        self.LE = [                                           # Matriz binária (i, a) que identifica se o lote 'i' pertence ao talhao 'a'
            [],
            [],
            []
        ]
        self.T_ida = [1, 1, 1, 1, 1, 1, 1]                    # Tempo de ida da frabica ao lote
        self.T_volta = [1.15 * t for t in self.T_ida]         # Tempo de volta do lote a fabrica
        self.DE = [                                           # Matriz (a,b) que representa o tempo de deslocamento entre os talhões 'a' e 'b'
            []
        ]
        self.TC = 0.5                                         # Tempo de carregamento fixo (em horas)

    @property
    def total_lotes(self):
        return sum(self.LT)
    
    @property
    def total_talhoes(self):
        return len(self.LT)

def get_neighbors():
    pass

def main():
    dados = Dados()
    print(dados.total_lotes)
    print(dados.total_talhoes)
    
if __name__ == "__main__":
    main()