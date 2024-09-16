
import requests

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
access_token = 'BQBEdwGIA1zDiOBVXQd3HUNBSUlNkkBmG9-mHxbfpQ5B9GCeukiRb713rCkuf5jvdWMUaPHckwnOV4WXx-ft1KH6MiwB1JqObD6Yn3Gc13eG-7yRaq4'
# playlist_id = '1WZSJgwtsA6LFMypnCEI6d' #https://open.spotify.com/playlist/1WZSJgwtsA6LFMypnCEI6d?si=2a96a04f02dc46e7
output_filename = 'all_playlist_tracks.txt'
playlist_id = '2Wmv4FsoPRrVRpyXWZKaz8'

# Récupérer tous les titres de la playlist
tracks = fetch_playlist_tracks(playlist_id, access_token)

if tracks:
    # Enregistrer les titres dans un fichier texte
    save_tracks_to_file(tracks, output_filename)
    print(f"Tracks have been saved to {output_filename}")
else:
    print("No tracks found or failed to fetch the playlist.")
