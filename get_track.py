
import requests
from ask_for_playlist import ask_for_playlist

def get_access_token(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read().strip()

def fetch_playlist_tracks(playlist_id, access_token):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    tracks = []
    offset = 0
    limit = 50

    while True:
        params = {
            "offset": offset,
            "limit": limit
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Failed to retrieve the playlist. Status code:", response.status_code)
            print("Response:", response.text)
            break

        response_json = response.json()
        items = response_json.get('items', [])
        if not items:
            break

        for item in items:
            track = item['track']
            track_info = f"{track['name']} by {track['artists'][0]['name']}"
            tracks.append(track_info)

        if len(items) < limit:
            # end of the playlist
            break

        offset += limit

    return tracks

def save_tracks_to_file(tracks, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for track in tracks:
            file.write(track + "\n")

# URL de la playlist Spotify publique
access_token = 'BQDPDWZJgSR6pFRfvvKu_3Vx2Bu__zVtk-mgRs50412OE-PSIQiSuLhNoKzsLSnN11tZBnl2qvpCxTsT37Zs9byYFPCic6o9cx2jMY2ICPAXLpbCqrY'
# playlist_id = '1WZSJgwtsA6LFMypnCEI6d' #https://open.spotify.com/playlist/1WZSJgwtsA6LFMypnCEI6d?si=2a96a04f02dc46e7
output_filename = 'all_playlist_tracks.txt'
#playlist_id = '3dviBA7fJkKYxuUYPa5ItD'
playlist_id = ask_for_playlist()

# Récupérer tous les titres de la playlist
tracks = fetch_playlist_tracks(playlist_id, access_token)

if tracks:
    # Enregistrer les titres dans un fichier texte
    save_tracks_to_file(tracks, output_filename)
    print(f"Tracks have been saved to {output_filename}")
else:
    print("No tracks found or failed to fetch the playlist.")
