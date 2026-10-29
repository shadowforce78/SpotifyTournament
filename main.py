"""Spotify Tournament: pit the songs of a playlist against each other until one is left."""
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk

from bracket import Bracket
from spotify_api import (SpotifyClient, SpotifyError, load_client_id, parse_playlist_id,
                         save_client_id, REDIRECT_URI)

SAVE_FILE = "tournament_state.json"

BG, PANEL, CARD, CARD_HOVER = "#121212", "#181818", "#242424", "#2f2f2f"
FG, MUTED, GREEN = "#ffffff", "#b3b3b3", "#1db954"
FONT = "Segoe UI"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spotify Tournament")
        self.geometry("820x560")
        self.minsize(640, 480)
        self.configure(bg=BG)
        self._style()

        self.client = None
        self.bracket = None
        self.results = queue.Queue()
        self.frame = None
        self.after(100, self._poll)

        client_id = load_client_id()
        if client_id:
            self.client = SpotifyClient(client_id)
            self.show_playlists()
        else:
            self.show_setup()

    # ---- helpers ----------------------------------------------------------
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TProgressbar", troughcolor=CARD, background=GREEN, borderwidth=0, thickness=6)
        s.configure("Vertical.TScrollbar", background=CARD, troughcolor=PANEL, borderwidth=0, arrowcolor=MUTED)

    def _poll(self):
        try:
            while True:
                cb = self.results.get_nowait()
                cb()
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def work(self, fn, on_ok, on_err=None):
        """Run fn in a thread; deliver result on the Tk thread."""
        def run():
            try:
                res = fn()
                self.results.put(lambda: on_ok(res))
            except Exception as e:  # noqa: BLE001 - surfaced in the UI
                self.results.put(lambda e=e: (on_err or self.fail)(e))
        threading.Thread(target=run, daemon=True).start()

    def fail(self, e):
        if hasattr(self.frame, "status"):
            self.frame.status.config(text=str(e), fg="#f15e6c")

    def switch(self, builder):
        if self.frame:
            self.frame.destroy()
        self.unbind("<Left>"); self.unbind("<Right>"); self.unbind("<Control-z>")
        self.frame = tk.Frame(self, bg=BG)
        self.frame.pack(fill="both", expand=True, padx=32, pady=24)
        builder(self.frame)
        self.frame.status = getattr(self.frame, "status", None) or tk.Label(self.frame, bg=BG)

    def label(self, parent, text, size=11, color=FG, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color, wraplength=kw.pop("wraplength", 700),
                        font=(FONT, size, "bold" if bold else "normal"), **kw)

    def button(self, parent, text, command, primary=False, **kw):
        bg, fg = (GREEN, "#000000") if primary else (CARD, FG)
        hover = "#1ed760" if primary else CARD_HOVER
        b = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=hover,
                      activeforeground=fg, relief="flat", bd=0, cursor="hand2",
                      font=(FONT, 11, "bold"), padx=18, pady=8, **kw)
        b.bind("<Enter>", lambda _: b.config(bg=hover) if str(b["state"]) == "normal" else None)
        b.bind("<Leave>", lambda _: b.config(bg=bg))
        return b

    def entry(self, parent, **kw):
        return tk.Entry(parent, bg=CARD, fg=FG, insertbackground=FG, relief="flat", bd=0,
                        font=(FONT, 11), highlightthickness=1, highlightbackground=CARD_HOVER,
                        highlightcolor=GREEN, **kw)

    # ---- screens ----------------------------------------------------------
    def show_setup(self):
        def build(f):
            self.label(f, "Configuration", 22, bold=True).pack(anchor="w")
            self.label(f, "Crée une app sur developer.spotify.com/dashboard, ajoute ce Redirect URI :",
                       color=MUTED).pack(anchor="w", pady=(8, 4))
            uri = self.entry(f, width=50)
            uri.insert(0, REDIRECT_URI)
            uri.config(state="readonly")
            uri.pack(anchor="w", pady=4, ipady=6)
            self.label(f, "Puis colle ton Client ID :", color=MUTED).pack(anchor="w", pady=(16, 4))
            cid = self.entry(f, width=50)
            cid.pack(anchor="w", ipady=6)

            def save():
                value = cid.get().strip()
                if len(value) < 20:
                    f.status.config(text="Client ID invalide.", fg="#f15e6c")
                    return
                save_client_id(value)
                self.client = SpotifyClient(value)
                self.show_playlists()

            self.button(f, "Enregistrer", save, primary=True).pack(anchor="w", pady=20)
            f.status = self.label(f, "", color=MUTED)
            f.status.pack(anchor="w")
        self.switch(build)

    def show_playlists(self):
        def build(f):
            head = tk.Frame(f, bg=BG)
            head.pack(fill="x")
            self.label(head, "Spotify Tournament", 22, bold=True).pack(side="left")
            if os.path.exists(SAVE_FILE):
                self.button(head, "Reprendre", self.resume).pack(side="right")

            self.label(f, "Choisis une playlist — les titres s'affrontent jusqu'au vainqueur.",
                       color=MUTED).pack(anchor="w", pady=(4, 16))

            f.status = self.label(f, "", color=MUTED)

            if not self.client.logged_in:
                self.button(f, "Se connecter avec Spotify", lambda: self.connect(f), primary=True).pack(anchor="w")
                f.status.pack(anchor="w", pady=12)
                return

            box = tk.Frame(f, bg=PANEL)
            box.pack(fill="both", expand=True)
            sb = ttk.Scrollbar(box, orient="vertical")
            lb = tk.Listbox(box, bg=PANEL, fg=FG, selectbackground=GREEN, selectforeground="#000000",
                            font=(FONT, 12), relief="flat", bd=0, highlightthickness=0, activestyle="none",
                            yscrollcommand=sb.set)
            sb.config(command=lb.yview)
            sb.pack(side="right", fill="y")
            lb.pack(fill="both", expand=True, padx=8, pady=8)
            f.playlists = []
            lb.insert("end", "Chargement…")

            def loaded(pls):
                f.playlists = pls
                lb.delete(0, "end")
                for p in pls:
                    n = f"   ({p['total']} titres)" if p["total"] is not None else ""
                    lb.insert("end", f"{p['name']}{n}")
                if not pls:
                    lb.insert("end", "Aucune playlist à toi ou collaborative.")

            def failed(e):
                lb.delete(0, "end")
                self.client.logout() if "401" in str(e) else None
                self.fail(e)

            self.work(self.client.my_playlists, loaded, failed)

            def start_selected(_=None):
                sel = lb.curselection()
                if sel and sel[0] < len(f.playlists):
                    self.load(f.playlists[sel[0]]["id"], f)
            lb.bind("<Double-Button-1>", start_selected)

            row = tk.Frame(f, bg=BG)
            row.pack(fill="x", pady=(12, 0))
            link = self.entry(row)
            link.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
            link.insert(0, "…ou colle un lien de playlist")
            link.bind("<FocusIn>", lambda _: link.get().startswith("…") and link.delete(0, "end"))

            def from_link():
                pid = parse_playlist_id(link.get())
                if pid:
                    self.load(pid, f)
                else:
                    f.status.config(text="Lien de playlist invalide.", fg="#f15e6c")

            self.button(row, "Lancer", from_link).pack(side="left", padx=(0, 8))
            self.button(row, "Jouer la sélection", start_selected, primary=True).pack(side="left")
            f.status.pack(anchor="w", pady=(10, 0))
            self.button(f, "Se déconnecter", lambda: (self.client.logout(), self.show_playlists())).pack(
                anchor="e", pady=(8, 0))
        self.switch(build)

    def connect(self, f):
        f.status.config(text="Autorise l'app dans ton navigateur…", fg=MUTED)
        self.work(self.client.login, lambda _: self.show_playlists())

    def load(self, playlist_id, f):
        f.status.config(text="Récupération des titres…", fg=MUTED)

        def done(tracks):
            if len(tracks) < 2:
                f.status.config(text="Il faut au moins 2 titres dans la playlist.", fg="#f15e6c")
                return
            self.bracket = Bracket(tracks)
            self.show_match()

        self.work(lambda: self.client.playlist_tracks(playlist_id), done)

    def resume(self):
        try:
            with open(SAVE_FILE, encoding="utf-8") as fh:
                self.bracket = Bracket(None, json.load(fh))
            self.show_match()
        except (OSError, ValueError, TypeError):
            self.frame.status.config(text="Sauvegarde illisible.", fg="#f15e6c")

    def save(self):
        with open(SAVE_FILE, "w", encoding="utf-8") as fh:
            json.dump(self.bracket.state(), fh)

    def show_match(self):
        b = self.bracket
        if b.champion is not None:
            return self.show_winner()
        self.save()

        def build(f):
            self.label(f, b.round_label, 20, bold=True).pack()
            self.label(f, b.match_label, color=MUTED).pack(pady=(2, 12))
            bar = ttk.Progressbar(f, maximum=b.total, value=b.decided)
            bar.pack(fill="x", pady=(0, 24))

            arena = tk.Frame(f, bg=BG)
            arena.pack(fill="both", expand=True)
            arena.columnconfigure((0, 2), weight=1, uniform="c")
            arena.rowconfigure(0, weight=1)
            for col, side in ((0, 0), (2, 1)):
                title, _, artist = b.match[side].partition(" — ")
                card = tk.Button(arena, text=f"{title}\n\n{artist}", command=lambda s=side: self.pick(s),
                                 bg=CARD, fg=FG, activebackground=GREEN, activeforeground="#000000",
                                 relief="flat", bd=0, cursor="hand2", wraplength=280,
                                 font=(FONT, 15, "bold"), padx=16, pady=16)
                card.grid(row=0, column=col, sticky="nsew")
                card.bind("<Enter>", lambda e, c=card: c.config(bg=CARD_HOVER))
                card.bind("<Leave>", lambda e, c=card: c.config(bg=CARD))
            tk.Label(arena, text="VS", bg=BG, fg=MUTED, font=(FONT, 14, "bold")).grid(row=0, column=1, padx=16)

            foot = tk.Frame(f, bg=BG)
            foot.pack(fill="x", pady=(20, 0))
            undo = self.button(foot, "↶ Annuler", self.undo)
            undo.pack(side="left")
            if not b.can_undo:
                undo.config(state="disabled", fg=MUTED)
            self.label(foot, "← / → pour choisir · Ctrl+Z pour annuler", 9, MUTED).pack(side="left", padx=16)
            self.button(foot, "Menu", self.show_playlists).pack(side="right")

        self.switch(build)
        self.bind("<Left>", lambda _: self.pick(0))
        self.bind("<Right>", lambda _: self.pick(1))
        self.bind("<Control-z>", lambda _: self.undo())

    def pick(self, side):
        self.bracket.choose(side)
        self.show_match()

    def undo(self):
        if self.bracket.can_undo:
            self.bracket.undo()
            self.show_match()

    def show_winner(self):
        title, _, artist = self.bracket.champion.partition(" — ")
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)

        def build(f):
            self.label(f, "🏆 Vainqueur", 16, GREEN, bold=True).pack(pady=(70, 16))
            self.label(f, title, 30, bold=True, wraplength=700, justify="center").pack()
            self.label(f, artist, 16, MUTED).pack(pady=(6, 40))
            self.button(f, "Nouveau tournoi", self.show_playlists, primary=True).pack()
        self.switch(build)


if __name__ == "__main__":
    App().mainloop()
