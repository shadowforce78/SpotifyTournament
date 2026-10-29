# Spotify Tournament

Fais s'affronter les titres d'une playlist Spotify en tournoi à élimination directe (byes gérés automatiquement, annulation, sauvegarde auto).

## Installation
1. `pip install -r requirements.txt`
2. Crée une app sur https://developer.spotify.com/dashboard et ajoute le Redirect URI `http://127.0.0.1:8888/callback`.
3. `python main.py` puis colle ton Client ID (ou définis `SPOTIFY_CLIENT_ID`).

## Limites de l'API Spotify (depuis fév. 2026)
- Les titres d'une playlist ne sont lisibles que si tu en es **propriétaire ou collaborateur**.
- Le propriétaire de l'app en Development Mode doit avoir un compte Premium.
