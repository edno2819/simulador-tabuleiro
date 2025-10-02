from src.core import Jogo, Tabuleiro, Jogador
from src.estrategias import Impulsivo, Exigente, Cauteloso, Aleatorio


def simulador(qtd_casas=20, jogadores=4):
    estrategias = [
        Impulsivo,
        Exigente,
        Cauteloso,
        Aleatorio,
    ]
    jogadores = [Jogador(estrategias[i % len(estrategias)])
                 for i in range(jogadores)]

    jogo = Jogo(jogadores, qtd_casas)

    while not jogo.finished:

        for jogador in list(jogo.jogadores):
            if jogo.finished:
                break

            dado = Tabuleiro.jogar_dado()
            jogo.jogada(jogador, dado)
            if not jogo.finished and jogador in jogo.jogadores:
                jogo.comprar_propiedade(jogador)

    return jogo.resultado()
