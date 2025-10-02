import random
from typing import List, Optional, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.estrategias import Estrategia, Impulsivo, Exigente, Cauteloso, Aleatorio

console = Console()


class Jogador:
    _contador_id = 0

    def __init__(self, estrategia_cls: type[Estrategia]):
        Jogador._contador_id += 1
        self.id = Jogador._contador_id
        self.saldo = 300
        self.estrategia = estrategia_cls()
        self.propriedades: List['Propriedade'] = []
        self.posicao = 0

    def alterar_saldo(self, valor: int) -> int:
        self.saldo += valor
        return self.saldo

    def adicionar_propriedade(self, propriedade: 'Propriedade'):
        self.propriedades.append(propriedade)

    def remover_propriedade(self, propriedade: 'Propriedade'):
        if propriedade in self.propriedades:
            self.propriedades.remove(propriedade)

    def limpar_propriedades(self):
        for p in self.propriedades:
            p.proprietario = None
            self.remover_propriedade(p)

    def nome_estrategia(self) -> str:
        return self.estrategia.nome

    def print_infos(self):
        estrategia_nome = self.estrategia.__class__.__name__
        propriedades_info = f"{len(self.propriedades)} propriedade(s)"

        console.print(Panel(
            f"[bold cyan]Jogador #{self.id}[/bold cyan]\n"
            f"💰 Saldo: [green]${self.saldo}[/green]\n"
            f"🎯 Estratégia: [yellow]{estrategia_nome}[/yellow]\n"
            f"🏠 Propriedades: {propriedades_info}",
            border_style="cyan"
        ))


class Propriedade:
    _contador_id = 0

    def __init__(self, preco: int, aluguel: int):
        Propriedade._contador_id += 1
        self.id = Propriedade._contador_id
        self.preco = preco
        self.aluguel = aluguel
        self.proprietario: Optional[Jogador] = None

    def definir_proprietario(self, jogador: Jogador):
        self.proprietario = jogador
        jogador.adicionar_propriedade(self)

    def print_infos(self):
        proprietario_info = f"Jogador #{self.proprietario.id}" if self.proprietario else "[red]Disponível[/red]"
        console.print(
            f"🏠 [bold]Propriedade #{self.id}[/bold] | "
            f"Preço: [green]${self.preco}[/green] | "
            f"Aluguel: [yellow]${self.aluguel}[/yellow] | "
            f"Dono: {proprietario_info}"
        )


class Tabuleiro:
    propriedades: List[Propriedade] = []
    PORCENTAGEM_ALUGUEL = 0.25

    @classmethod
    def inicializar(cls, qtd_casas: int) -> List[Propriedade]:
        cls.propriedades = []
        for _ in range(qtd_casas):
            preco = random.randint(100, 300)
            aluguel = int(preco * cls.PORCENTAGEM_ALUGUEL)
            cls.propriedades.append(Propriedade(preco, aluguel))
        return cls.propriedades

    @classmethod
    def jogar_dado(cls) -> int:
        return random.randint(1, 6)

    @classmethod
    def nova_posicao(cls, atual: int, passos: int) -> int:
        n = len(cls.propriedades)
        return (atual + passos) % n


class Jogo:
    RECOMPENSA_VOLTA = 100
    MAX_RODADAS = 1000
    QTD_CASAS = 20

    def __init__(self, jogadores: List[Jogador], qtd_casas: int = QTD_CASAS):
        self.jogadores: List[Jogador] = jogadores
        self.jogadores_iniciais: List[Jogador] = jogadores.copy()
        random.shuffle(self.jogadores)
        self.ordem_turnos: List[Jogador] = self.jogadores

        self.tabuleiro = Tabuleiro.inicializar(qtd_casas)
        self.rodada = 0
        self.finished = False
        self.termino_por_tempo = False
        self.vencedor: Optional[Jogador] = None

    def pagar_aluguel(self, propriedade: Propriedade, inquilino: Jogador):
        dono = propriedade.proprietario
        if dono and dono != inquilino:
            inquilino.alterar_saldo(-propriedade.aluguel)
            dono.alterar_saldo(propriedade.aluguel)
            if inquilino.saldo < 0:
                self.remover_jogador(inquilino)

    def remover_jogador(self, jogador: Jogador):
        jogador.limpar_propriedades()
        if jogador in self.jogadores:
            self.jogadores.remove(jogador)

    def jogo_finalizado(self) -> bool:
        if len(self.jogadores) == 1:
            self.vencedor = self.jogadores[0]
            self.finished = True
            self.termino_por_tempo = False
            return True

        if self.rodada >= self.MAX_RODADAS:
            self.termino_por_tempo = True
            self.finished = True
            self.vencedor = self._ranking_por_saldo()[0]
            return True

        return False


    def jogada(self, jogador: Jogador, numero_dado: int):
        if self.finished or jogador not in self.jogadores:
            return

        pos_anterior = jogador.posicao
        jogador.posicao = Tabuleiro.nova_posicao(jogador.posicao, numero_dado)
        self.rodada += 1

        # Deu uma volta completa
        if jogador.posicao < pos_anterior:
            jogador.alterar_saldo(self.RECOMPENSA_VOLTA)

        casa = self.tabuleiro[jogador.posicao]

        # Se tem dono e não é o próprio, paga aluguel
        if casa.proprietario and casa.proprietario != jogador:
            self.pagar_aluguel(casa, jogador)

        self.jogo_finalizado()

    def comprar_propiedade(self, jogador: Jogador) -> bool:
        if self.finished or jogador not in self.jogadores:
            return False

        prop = self.tabuleiro[jogador.posicao]
        if prop.proprietario is not None:
            return False

        if jogador.saldo < prop.preco:
            return False

        if not jogador.estrategia.decide_compra(jogador, prop):
            return False

        jogador.alterar_saldo(-prop.preco)
        prop.definir_proprietario(jogador)
        return True

    def print_infos(self):
        console.print(
            f"\n[bold magenta]═══════════════════════════════════════[/bold magenta]")
        console.print(
            f"[bold magenta]        ESTADO DO JOGO - Rodada {self.rodada}[/bold magenta]")
        console.print(
            f"[bold magenta]═══════════════════════════════════════[/bold magenta]\n")

        console.print("[bold blue]👥 JOGADORES:[/bold blue]\n")
        for jogador in self.jogadores:
            jogador.print_infos()
            console.print()

        console.print(
            "\n[bold blue]🏘️  TABULEIRO (Propriedades):[/bold blue]\n")

        tabela = Table(show_header=True, header_style="bold magenta")
        tabela.add_column("ID", style="dim", width=6)
        tabela.add_column("Preço", justify="right")
        tabela.add_column("Aluguel", justify="right")
        tabela.add_column("Proprietário", justify="center")

        for prop in self.tabuleiro:
            proprietario_info = f"Jogador #{prop.proprietario.id}" if prop.proprietario else "Disponível"
            tabela.add_row(
                f"#{prop.id}",
                f"${prop.preco}",
                f"${prop.aluguel}",
                proprietario_info
            )

        console.print(tabela)

    def _ranking_por_saldo(self) -> List[Jogador]:
        ordem_index = {j: i for i, j in enumerate(self.ordem_turnos)}

        def chave(j: Jogador) -> Tuple[int, int]:
            # Maior saldo primeiro e desempate por ordem de turno inicial
            return -j.saldo, ordem_index.get(j, 9999)

        return sorted(self.jogadores, key=chave)

    def resultado(self) -> Dict[str, object]:
        ranking = self._ranking_por_saldo()
        vencedor_nome = ranking[0].nome_estrategia(
        ) if ranking else "sem_vencedor"
        jogadores_nomes = [j.nome_estrategia() for j in self.jogadores_iniciais]
        return {
            "vencedor": vencedor_nome,
            "jogadores": jogadores_nomes,
            "termino_por_tempo": self.termino_por_tempo,
            "rodadas": self.rodada,
        }

    def print_result(self):
        console.print("\n[bold green]📊 RESULTADO DA PARTIDA[/bold green]")

        if self.vencedor is None and self.jogadores:
            self.vencedor = self._ranking_por_saldo()[0]

        if self.vencedor:
            console.print(
                f"🏆 Vencedor: [bold yellow]{self.vencedor.nome_estrategia().upper()}[/bold yellow] "
                f"(Jogador #{self.vencedor.id})"
            )
        else:
            console.print("Sem vencedor definido.")

        if self.termino_por_tempo:
            console.print(
                "⏱️ Jogo terminou por limite de 1000 rodadas.")

        console.print(f"🔁 Total de rodadas: [bold]{self.rodada}[/bold]\n")

        ranking = self._ranking_por_saldo()
        tabela = Table(show_header=True, header_style="bold magenta")
        tabela.add_column("Posição", justify="right")
        tabela.add_column("Jogador", justify="left")
        tabela.add_column("Estratégia", justify="left")
        tabela.add_column("Saldo", justify="right")

        for i, j in enumerate(ranking, start=1):
            tabela.add_row(
                f"{i}",
                f"#{j.id}",
                j.nome_estrategia(),
                f"${j.saldo}"
            )
        console.print(tabela)


# =========================
# Simulador para testes
# =========================
def simulation_test():
    console.print(
        "[bold green]🎮 Iniciando Simulação do Jogo...[/bold green]\n")

    # 4 jogadores com estratégias distintas
    jogadores: List[Jogador] = [
        Jogador(Impulsivo),
        Jogador(Impulsivo),
        Jogador(Impulsivo),
        Jogador(Impulsivo),

        Jogador(Exigente),
        Jogador(Exigente),
        Jogador(Exigente),
        Jogador(Exigente),

        Jogador(Cauteloso),
        Jogador(Cauteloso),
        Jogador(Cauteloso),
        Jogador(Cauteloso),

        Jogador(Aleatorio),
        Jogador(Aleatorio),
        Jogador(Aleatorio),
        Jogador(Aleatorio),
    ]

    jogo = Jogo(jogadores)
    jogo.print_infos()

    while not jogo.finished:

        for jogador in list(jogo.jogadores):
            if jogo.finished:
                break

            dado = Tabuleiro.jogar_dado()
            jogo.jogada(jogador, dado)

            # Se o jogador não foi eliminado, tenta comprar pela estratégia
            if not jogo.finished and jogador in jogo.jogadores:
                jogo.comprar_propiedade(jogador)

    jogo.print_infos()
    jogo.print_result()
