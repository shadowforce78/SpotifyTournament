import tkinter as tk

playlist_id = None  # Variable pour stocker le playlist ID

def ask_for_playlist():
    global playlist_id
    
    # Crée une fenêtre Tkinter pour récupérer le lien de la playlist Spotify
    root = tk.Tk()
    root.title("Spotify Playlist ID Input")
    root.geometry("300x200")
    root.resizable(False, False)
    
    link_entry = tk.Entry(root, width=40)
    label = tk.Label(root, text="Enter your Spotify Playlist Link:")
    label.pack(pady=10)
    link_entry.pack(pady=10)
    
    def submit():
        global playlist_id
        playlist_link = link_entry.get()
        if "spotify.com/playlist/" in playlist_link:
            # Récupère l'ID de la playlist
            playlist_id = playlist_link.split("/playlist/")[1].split("?")[0]
            root.destroy()  # Ferme la fenêtre après soumission
        else:
            label.config(text="Invalid link. Please enter a valid Spotify playlist link.")
    
    button = tk.Button(root, text="Submit", command=submit)
    button.pack(pady=10)
    
    root.mainloop()

    return playlist_id  # Retourne la valeur après que la fenêtre ait été fermée

# Appelle la fonction et récupère l'ID de la playlist
#playlist_id = ask_for_playlist()