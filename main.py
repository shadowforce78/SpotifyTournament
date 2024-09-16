from get_track import fetch_playlist_tracks, access_token, playlist_id, output_filename, save_tracks_to_file
from add_byes import add_entry, variable
from create_tournament import make_tournament
from play_tournament import start

tracks = fetch_playlist_tracks(playlist_id, access_token)

if tracks:
    # Enregistrer les titres dans un fichier texte
    save_tracks_to_file(tracks, output_filename)
    print(f"Tracks have been saved to {output_filename}")
else:
    print("No tracks found or failed to fetch the playlist.")


add_entry(variable(), output_filename)
make_tournament(output_filename)

start()