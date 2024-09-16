import random


def make_tournament(file):
    # Recuperer toutes les entrées du fichier et les mettre dans une liste
    with open(file, 'r', encoding='utf-8') as file:
        # Shuffle toutes les entrées
        lines = file.readlines()
        random.shuffle(lines)
        entries = [line.strip() for line in lines]
        midpoint = len(entries) // 2
        left_side = entries[:midpoint]
        right_side = entries[midpoint:]

    # Créer des paires de matchs
    matches = list(zip(left_side, right_side))

    # Enregistrer les matchs dans un fichier texte
    with open('tournament_matches.txt', 'w', encoding='utf-8') as file:
        for match in matches:
            file.write(f"{match[0]} --- {match[1]}\n")

make_tournament('all_playlist_tracks.txt')