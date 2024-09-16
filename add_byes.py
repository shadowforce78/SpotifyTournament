def get_list(text_file):
    # Recuperer le nombre de lignes du fichier
    with open(text_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        number_of_lines = len(lines)

    return number_of_lines

def next_power_of_2(n):
    if n < 1:
        return 1
    # Trouver la plus petite multiple de 2 supérieure ou égale à n (2**x >= n)
    x = 0
    while 2 ** x < n:
        x += 1
    return 2 ** x



# Exemple d'utilisation
def variable():
    n = get_list('all_playlist_tracks.txt')
    result = next_power_of_2(n)
    byes_total = (result - n)
    return byes_total

def add_entry(byes_total, text_file):
    byes = "SKIP"
    # Ajouter les byes au fichier texte
    with open(text_file, 'a', encoding='utf-8') as file:
        for _ in range(byes_total):
            file.write(byes + "\n")


def main():
    add_entry(variable(), 'all_playlist_tracks.txt')

main()