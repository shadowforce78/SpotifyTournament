"""Single-elimination bracket with byes and undo. No UI, no I/O besides JSON-able state."""
import random


def round_name(pairs_left):
    return {1: "Finale", 2: "Demi-finales", 4: "Quarts de finale", 8: "Huitièmes de finale"}.get(
        pairs_left, f"Tour de {pairs_left * 2}")


class Bracket:
    def __init__(self, entries, state=None):
        if state:
            self.__dict__.update(state)
            return
        entries = list(entries)
        if len(entries) < 2:
            raise ValueError("Il faut au moins 2 titres pour un tournoi.")
        random.shuffle(entries)
        size = 1
        while size < len(entries):
            size *= 2
        byes = size - len(entries)
        # byes face a real entry, never each other
        pairs = [[e, None] for e in entries[:byes]]
        rest = entries[byes:]
        pairs += [[rest[i], rest[i + 1]] for i in range(0, len(rest), 2)]
        random.shuffle(pairs)
        self.pairs = pairs
        self.idx = 0
        self.winners = []
        self.champion = None
        self.decided = 0
        self.total = len(entries) - 1  # real matches
        self.history = []
        self._skip_byes()

    # ---- state ------------------------------------------------------------
    def state(self):
        return dict(self.__dict__)

    def _snapshot(self):
        return {k: (list(v) if isinstance(v, list) else v) for k, v in self.__dict__.items() if k != "history"}

    # ---- queries ----------------------------------------------------------
    @property
    def match(self):
        return None if self.champion is not None else self.pairs[self.idx]

    @property
    def round_label(self):
        return round_name(len(self.pairs))

    @property
    def match_label(self):
        real_before = sum(1 for p in self.pairs[:self.idx] if None not in p)
        real_total = sum(1 for p in self.pairs if None not in p)
        return f"Match {real_before + 1} / {real_total}"

    @property
    def can_undo(self):
        return bool(self.history)

    # ---- actions ----------------------------------------------------------
    def choose(self, side):
        self.history.append(self._snapshot())
        self.winners.append(self.pairs[self.idx][side])
        self.decided += 1
        self.idx += 1
        self._skip_byes()

    def undo(self):
        if self.history:
            self.__dict__.update(self.history.pop())

    def _skip_byes(self):
        while True:
            if self.idx >= len(self.pairs):
                if len(self.winners) == 1:
                    self.champion = self.winners[0]
                    return
                w = self.winners
                self.pairs = [[w[i], w[i + 1]] for i in range(0, len(w), 2)]
                self.winners, self.idx = [], 0
            a, b = self.pairs[self.idx]
            if b is None:
                self.winners.append(a)
                self.idx += 1
            else:
                return
