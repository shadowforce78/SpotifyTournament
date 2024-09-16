def getline(file):
    with open(file, 'r', encoding='utf-8') as file:
        return len(file.readlines())
    
print(getline('all_playlist_tracks.txt'))