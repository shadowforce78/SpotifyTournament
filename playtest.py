import tkinter as tk
from tkinter import messagebox
import json

# Nom du fichier texte contenant les matchs
filename = "tournament_matches.txt"
save_filename = "tournament_state.json"

def read_matches(filename):
    with open(filename, "r", encoding="utf-8") as file:
        matches = [line.strip() for line in file if line.strip()]
    return matches

class TournamentApp:
    def __init__(self, root, matches):
        self.root = root
        self.root.title("Tournoi")

        # Ajout de la taille de la fenêtre
        self.root.geometry("300x200")


        self.matches = matches
        self.round_num = 1
        self.current_match = 0
        self.next_round = []

        self.label_round = tk.Label(root, text=f"--- Tour {self.round_num} ---")
        self.label_round.pack()

        self.label_match = tk.Label(root, text="")
        self.label_match.pack()

        self.button1 = tk.Button(root, text="", command=lambda: self.choose_winner(1))
        self.button1.pack()

        self.button2 = tk.Button(root, text="", command=lambda: self.choose_winner(2))
        self.button2.pack()

        self.save_button = tk.Button(root, text="Save", command=self.save_state)
        self.save_button.pack()

        self.load_button = tk.Button(root, text="Load", command=self.load_state)
        self.load_button.pack()

        self.next_match()

    def next_match(self):
        if self.current_match < len(self.matches):
            participants = self.matches[self.current_match].split(' --- ')
            if len(participants) == 2:
                self.label_match.config(text=f"Match: {participants[0]} vs {participants[1]}")
                self.button1.config(text=participants[0])
                self.button2.config(text=participants[1])
            elif "SKIP" in participants:
                # Cas où un participant a un bye (n'a pas d'adversaire)
                self.next_round.append(participants[0])
                self.current_match += 1
                self.next_match()  # Aller au prochain match immédiatement
        else:
            self.current_match = 0
            if len(self.next_round) > 1:
                self.matches = [f"{self.next_round[i]} --- {self.next_round[i + 1]}" for i in range(0, len(self.next_round), 2)]
                self.round_num += 1
                self.label_round.config(text=f"--- Tour {self.round_num} ---")
                self.next_round = []
                self.next_match()  # Commencer le prochain tour
            else:
                messagebox.showinfo("Tournoi Terminé", f"Le vainqueur du tournoi est : {self.next_round[0]}")
                self.root.quit()

    def choose_winner(self, choice):
        participants = self.matches[self.current_match].split(' --- ')
        winner = participants[choice - 1]
        self.next_round.append(winner)
        self.current_match += 1
        self.next_match()

    def save_state(self):
        state = {
            "matches": self.matches,
            "round_num": self.round_num,
            "current_match": self.current_match,
            "next_round": self.next_round
        }
        with open(save_filename, "w", encoding="utf-8") as file:
            json.dump(state, file)
        messagebox.showinfo("Sauvegarde", "L'état du tournoi a été sauvegardé.")

    def load_state(self):
        try:
            with open(save_filename, "r", encoding="utf-8") as file:
                state = json.load(file)
            self.matches = state["matches"]
            self.round_num = state["round_num"]
            self.current_match = state["current_match"]
            self.next_round = state["next_round"]
            self.label_round.config(text=f"--- Tour {self.round_num} ---")
            self.next_match()
            messagebox.showinfo("Chargement", "L'état du tournoi a été chargé.")
        except FileNotFoundError:
            messagebox.showerror("Erreur", "Aucun fichier de sauvegarde trouvé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de l'état: {e}")

def start():
    matches = read_matches(filename)
    root = tk.Tk()
    app = TournamentApp(root, matches)
    root.mainloop()

start()