import random
from abc import ABC

class Estrategia(ABC):
    nome: str = "generica"
    
    @classmethod
    def decide_compra(self, jogador: 'Jogador', propriedade: 'Propriedade') -> bool:
        return False


class Impulsivo(Estrategia):
    nome = "impulsivo"

    def decide_compra(self, jogador: 'Jogador', propriedade: 'Propriedade') -> bool:
        return True


class Exigente(Estrategia):
    nome = "exigente"

    def decide_compra(self, jogador: 'Jogador', propriedade: 'Propriedade') -> bool:
        return propriedade.aluguel > 50


class Cauteloso(Estrategia):
    nome = "cauteloso"

    def decide_compra(self, jogador: 'Jogador', propriedade: 'Propriedade') -> bool:
        return (jogador.saldo - propriedade.preco) >= 80


class Aleatorio(Estrategia):
    nome = "aleatorio"

    def decide_compra(self, jogador: 'Jogador', propriedade: 'Propriedade') -> bool:
        return random.choice([True, False])
