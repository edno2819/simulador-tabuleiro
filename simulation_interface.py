import tkinter as tk
from src.core import Jogo, Tabuleiro, Jogador
from src.estrategias import Impulsivo, Exigente, Cauteloso, Aleatorio
import random


PLAYER_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12"]
PLAYER_NAME_BY_STRATEGY = {
    "impulsivo": "Impulsivo",
    "exigente": "Exigente",
    "cauteloso": "Cauteloso",
    "aleatorio": "Aleatório",
}

class TabuleiroGUI(tk.Tk):
    def __init__(self, jogo: 'Jogo'):
        super().__init__()
        self.title("Banco Imobiliário (Simplificado)")
        self.configure(bg="#0f0f0f")
        self.geometry("1100x760")
        self.resizable(False, False)

        self.jogo = jogo
        self.ordem_turnos = list(getattr(self.jogo, "ordem_turnos", self.jogo.jogadores))
        self.turn_index = 0
        self.last_dice = 0

        # Layout principal
        self.left_wrap = tk.Frame(self, bg="#0f0f0f", highlightthickness=0, bd=0)
        self.left_wrap.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(self.left_wrap, width=860, height=720, bg="#111111", highlightthickness=0, bd=0)
        self.canvas.pack(padx=10, pady=10)

        self.sidebar = tk.Frame(self, width=280, bg="#181818", highlightthickness=0, bd=0)
        self.sidebar.pack(side="right", fill="y")

        self._build_sidebar()

        self.tile_size = 84
        self.tile_positions = []   
        self.board_left_top = (0, 0)
        self.board_size = self.tile_size * 6 
        self.center_title_id = None

        self.tile_rects = []
        self.tile_labels = []

        self.token_items = {}

        # Monta layout centrado
        self.update_idletasks()
        self._layout_board()
        self._draw_board()
        self._init_tokens()
        self._refresh_sidebar()
        self._refresh_ownership_colors()

        # Inicia animação com delay de 1s
        self.after(1000, self._step)

    def _build_sidebar(self):
        def sep(parent):
            return tk.Frame(parent, height=1, bg="#303030", highlightthickness=0, bd=0)

        title = tk.Label(self.sidebar, text="Estado do Jogo", fg="#ffffff", bg="#181818",
                         font=("Segoe UI", 16, "bold"))
        title.pack(pady=(18, 8), anchor="w", padx=16)

        self.lbl_rodada = tk.Label(self.sidebar, text="Rodada: 0", fg="#cfcfcf", bg="#181818", font=("Segoe UI", 12))
        self.lbl_rodada.pack(anchor="w", padx=16)

        self.lbl_dado = tk.Label(self.sidebar, text="Último dado: -", fg="#cfcfcf", bg="#181818", font=("Segoe UI", 12))
        self.lbl_dado.pack(anchor="w", padx=16, pady=(0, 10))

        sep(self.sidebar).pack(fill="x", padx=12, pady=8)

        lbl_jogs = tk.Label(self.sidebar, text="Jogadores", fg="#ffffff", bg="#181818",
                            font=("Segoe UI", 14, "bold"))
        lbl_jogs.pack(anchor="w", padx=16, pady=(2, 6))

        self.players_frame = tk.Frame(self.sidebar, bg="#181818")
        self.players_frame.pack(fill="x", padx=8)

        self.player_rows = {}

        sep(self.sidebar).pack(fill="x", padx=12, pady=8)

        self.lbl_evento = tk.Label(self.sidebar, text="", fg="#bbbbbb", bg="#181818",
                                   wraplength=250, justify="left", font=("Segoe UI", 10))
        self.lbl_evento.pack(anchor="w", padx=16, pady=(6, 8))

        self.lbl_vencedor = tk.Label(self.sidebar, text="", fg="#f1c40f", bg="#181818",
                                     font=("Segoe UI", 12, "bold"), wraplength=250, justify="left")
        self.lbl_vencedor.pack(anchor="w", padx=16, pady=(6, 10))

        self.btn_reiniciar = tk.Button(self.sidebar, text="Reiniciar", command=self._reiniciar,
                                       bg="#2c2c2c", fg="#ffffff", activebackground="#3a3a3a",
                                       relief="flat")
        self.btn_reiniciar.pack(padx=16, pady=(6, 12), fill="x")

    def _layout_board(self):
        cw = int(self.canvas.winfo_width())
        ch = int(self.canvas.winfo_height())

        left = (cw - self.board_size) // 2
        top = (ch - self.board_size) // 2
        self.board_left_top = (left, top)

        s = self.tile_size
        x0, y0 = left, top
        pos = []
        for i in range(6):
            pos.append((x0 + i*s, y0))
        for i in range(1, 5):
            pos.append((x0 + 5*s, y0 + i*s))
        for i in range(5, -1, -1):
            pos.append((x0 + i*s, y0 + 5*s))
        for i in range(4, 0, -1):
            pos.append((x0, y0 + i*s))
        self.tile_positions = pos

    def _draw_board(self):
        self.canvas.delete("all")
        self.tile_rects.clear()
        self.tile_labels.clear()

        for idx, (x, y) in enumerate(self.tile_positions):
            r = self.canvas.create_rectangle(
                x, y, x + self.tile_size, y + self.tile_size,
                fill="#3b3b3b", outline="#666666", width=2
            )
            self.tile_rects.append(r)
            label = self.canvas.create_text(
                x + self.tile_size/2, y + self.tile_size/2,
                text=str(idx), fill="#d0d0d0", font=("Segoe UI", 11, "bold")
            )
            self.tile_labels.append(label)

        cx = self.board_left_top[0] + self.board_size/2
        cy = self.board_left_top[1] + self.board_size/2
        self.center_title_id = self.canvas.create_text(
            cx, cy, text="Banco Imobiliário\n(Simplificado)",
            fill="#f0f0f0", font=("Segoe UI", 20, "bold"), justify="center", anchor="center"
        )

    def _init_tokens(self):
        for data in self.token_items.values():
            self.canvas.delete(data["oval"])
            self.canvas.delete(data["text"])
        self.token_items.clear()

        for child in self.players_frame.winfo_children():
            child.destroy()
        self.player_rows.clear()

        for jogador in self._ordem_inicial():
            color = PLAYER_COLORS[(jogador.id - 1) % len(PLAYER_COLORS)]
            self._create_player_row(jogador, color)
            self._create_token(jogador, color)

    def _ordem_inicial(self):
        return list(self.ordem_turnos) if self.ordem_turnos else list(self.jogo.jogadores)

    def _tile_center_with_offset(self, tile_index: int, jogador: 'Jogador'):
        x, y = self.tile_positions[tile_index]
        cx, cy = x + self.tile_size/2, y + self.tile_size/2
        offsets = [(-16, -16), (16, -16), (-16, 16), (16, 16)]
        dx, dy = offsets[(jogador.id - 1) % len(offsets)]
        return cx + dx, cy + dy

    def _create_token(self, jogador: 'Jogador', color: str):
        pos = getattr(jogador, "posicao", 0)
        cx, cy = self._tile_center_with_offset(pos, jogador)
        r = 12
        oval = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="#111111", width=2)
        text = self.canvas.create_text(cx, cy, text=str(jogador.id), fill="white", font=("Segoe UI", 10, "bold"))
        self.token_items[jogador] = {"oval": oval, "text": text}

    def _move_token_to(self, jogador: 'Jogador', new_tile_index: int):
        if jogador not in self.token_items:
            return
        cx, cy = self._tile_center_with_offset(new_tile_index, jogador)
        r = 12
        ids = self.token_items[jogador]
        self.canvas.coords(ids["oval"], cx - r, cy - r, cx + r, cy + r)
        self.canvas.coords(ids["text"], cx, cy)

    def _remove_token(self, jogador: 'Jogador'):
        ids = self.token_items.pop(jogador, None)
        if ids:
            self.canvas.delete(ids["oval"])
            self.canvas.delete(ids["text"])

    def _refresh_ownership_colors(self):
        for i, prop in enumerate(self.jogo.tabuleiro):
            if prop.proprietario is None:
                fill = "#3b3b3b"
            else:
                fill = PLAYER_COLORS[(prop.proprietario.id - 1) % len(PLAYER_COLORS)]
            self.canvas.itemconfig(self.tile_rects[i], fill=fill)

    def _create_player_row(self, jogador: 'Jogador', color: str):
        row = tk.Frame(self.players_frame, bg="#181818")
        row.pack(fill="x", pady=4)

        dot = tk.Canvas(row, width=14, height=14, bg="#181818", highlightthickness=0, bd=0)
        dot.pack(side="left", padx=(5, 6))
        dot.create_oval(2, 2, 12, 12, fill=color, outline=color)

        est_nome = getattr(jogador.estrategia, "nome", "desconhecida")
        legivel = PLAYER_NAME_BY_STRATEGY.get(est_nome, est_nome)

        lbl_name = tk.Label(row, text=f"#{jogador.id} - {legivel}", fg="#ffffff", bg="#181818",
                            font=("Segoe UI", 11, "bold"))
        lbl_name.pack(side="left")

        lbl_saldo = tk.Label(row, text=f"Saldo: ${jogador.saldo}", fg="#d8d8d8", bg="#181818", font=("Segoe UI", 10))
        lbl_saldo.pack(side="right", padx=6)

        self.player_rows[jogador] = {"frame": row, "saldo": lbl_saldo}

    def _refresh_sidebar(self):
        self.lbl_rodada.config(text=f"Rodada: {getattr(self.jogo, 'rodada', 0)}")
        self.lbl_dado.config(text=f"Último dado: {self.last_dice if self.last_dice else '-'}")

        ativos = set(self.jogo.jogadores)
        for jog, row in list(self.player_rows.items()):
            if jog not in ativos:
                row["frame"].destroy()
                self._remove_token(jog)
                del self.player_rows[jog]

        for jog in self.jogo.jogadores:
            if jog not in self.player_rows:
                color = PLAYER_COLORS[(jog.id - 1) % len(PLAYER_COLORS)]
                self._create_player_row(jog, color)
                self._create_token(jog, color)
            self.player_rows[jog]["saldo"].config(text=f"Saldo: ${jog.saldo}")

    def _next_active_player(self):
        if not self.jogo.jogadores:
            return None
        n = len(self.ordem_turnos)
        tries = 0
        while tries < n:
            jogador = self.ordem_turnos[self.turn_index % n]
            self.turn_index += 1
            if jogador in self.jogo.jogadores:
                return jogador
            tries += 1
        return None

    def _step(self):
        if self.jogo.finished:
            self._on_finish()
            return

        jogador = self._next_active_player()
        if jogador is None:
            self._on_finish()
            return

        dado = Tabuleiro.jogar_dado()
        self.last_dice = dado

        self.jogo.jogada(jogador, dado)

        if not self.jogo.finished and (jogador in self.jogo.jogadores):
            comprou = self.jogo.comprar_propiedade(jogador)
            if comprou:
                self._set_evento(f"Jogador #{jogador.id} comprou a propriedade #{self.jogo.tabuleiro[jogador.posicao].id}.")
            else:
                self._set_evento(f"Jogador #{jogador.id} não comprou a propriedade.")

        if jogador in self.jogo.jogadores:
            self._move_token_to(jogador, jogador.posicao)
        else:
            self._set_evento(f"Jogador #{jogador.id} foi eliminado!")

        self._refresh_ownership_colors()
        self._refresh_sidebar()

        if self.jogo.finished:
            self._on_finish()
            return

        self.after(1000, self._step)

    def _set_evento(self, texto: str):
        self.lbl_evento.config(text=texto)

    def _on_finish(self):
        vencedor = getattr(self.jogo, "vencedor", None)
        if vencedor is None and self.jogo.jogadores:
            vencedor = sorted(self.jogo.jogadores, key=lambda j: -j.saldo)[0]
        if vencedor:
            nome_est = getattr(vencedor.estrategia, "nome", "desconhecida").upper()
            self.lbl_vencedor.config(text=f"VENCEDOR: Jogador #{vencedor.id} ({nome_est})")
        else:
            self.lbl_vencedor.config(text="Sem vencedor.")

    def _reiniciar(self):
        estrategias = [j.estrategia.__class__ for j in self._ordem_inicial()]
        novos_jogadores = [Jogador(est) for est in estrategias]
        novo_jogo = Jogo(novos_jogadores)

        self.jogo = novo_jogo
        self.ordem_turnos = list(getattr(novo_jogo, "ordem_turnos", novo_jogo.jogadores))
        self.turn_index = 0
        self.last_dice = 0
        self.lbl_vencedor.config(text="")

        self._layout_board()
        self._draw_board()
        self._init_tokens()
        self._refresh_sidebar()
        self._refresh_ownership_colors()
        self.after(1000, self._step)



if __name__ == "__main__":
    random.seed()
    jogadores = [
        Jogador(Impulsivo),
        Jogador(Exigente),
        Jogador(Cauteloso),
        Jogador(Aleatorio),
    ]
    jogo = Jogo(jogadores)
    app = TabuleiroGUI(jogo)
    app.mainloop()