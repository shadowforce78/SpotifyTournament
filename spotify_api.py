"""Minimal Spotify Web API client: OAuth (Authorization Code + PKCE) and playlist reading.

Endpoints used (checked against the Feb 2026 Web API changes):
  POST https://accounts.spotify.com/api/token
  GET  /v1/me
  GET  /v1/me/playlists
  GET  /v1/playlists/{id}/items      (replaces the removed /tracks endpoint)
"""
import base64
import hashlib
import json
import os
import re
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

API = "https://api.spotify.com/v1"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
REDIRECT_HOST, REDIRECT_PORT = "127.0.0.1", 8888
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"
SCOPES = "playlist-read-private playlist-read-collaborative"

CONFIG_FILE = "config.json"
TOKEN_FILE = ".spotify_token.json"


class SpotifyError(Exception):
    pass


def load_client_id():
    if os.environ.get("SPOTIFY_CLIENT_ID"):
        return os.environ["SPOTIFY_CLIENT_ID"].strip()
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f).get("client_id", "").strip() or None
    except (OSError, ValueError):
        return None


def save_client_id(client_id):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"client_id": client_id.strip()}, f)


def parse_playlist_id(text):
    """Accepts an open.spotify.com URL, a spotify:playlist: URI or a bare 22-char id."""
    text = text.strip()
    m = re.search(r"playlist[/:]([A-Za-z0-9]{22})", text) or re.fullmatch(r"([A-Za-z0-9]{22})", text)
    return m.group(1) if m else None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        self.server.result = {k: v[0] for k, v in query.items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<body style='font-family:sans-serif;background:#121212;color:#fff;text-align:center;"
            "padding-top:20vh'><h2>Connecté à Spotify ✔</h2><p>Tu peux fermer cet onglet.</p></body>".encode()
        )

    def log_message(self, *args):
        pass


class SpotifyClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.token = self._load_token()
        self._me = None

    # ---- auth -------------------------------------------------------------
    def _load_token(self):
        try:
            with open(TOKEN_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _store_token(self, data):
        old_refresh = (self.token or {}).get("refresh_token")
        self.token = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", old_refresh),
            "expires_at": time.time() + data.get("expires_in", 3600) - 30,
        }
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(self.token, f)

    def _token_request(self, payload):
        r = requests.post(TOKEN_URL, data={"client_id": self.client_id, **payload}, timeout=15)
        if r.status_code != 200:
            raise SpotifyError(f"Authentification refusée ({r.status_code}) : {r.text}")
        self._store_token(r.json())

    @property
    def logged_in(self):
        return bool(self.token and self.token.get("refresh_token"))

    def login(self, timeout=180):
        """Opens the browser, waits for the redirect. Blocking: call from a worker thread."""
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(16)

        try:
            server = HTTPServer((REDIRECT_HOST, REDIRECT_PORT), _CallbackHandler)
        except OSError as e:
            raise SpotifyError(f"Port {REDIRECT_PORT} indisponible : {e}")
        server.result = None
        server.timeout = 1

        webbrowser.open(AUTH_URL + "?" + urlencode({
            "client_id": self.client_id, "response_type": "code", "redirect_uri": REDIRECT_URI,
            "scope": SCOPES, "state": state, "code_challenge_method": "S256", "code_challenge": challenge,
        }))
        deadline = time.time() + timeout
        try:
            while server.result is None and time.time() < deadline:
                server.handle_request()
        finally:
            server.server_close()

        res = server.result
        if not res:
            raise SpotifyError("Connexion expirée.")
        if res.get("state") != state or "code" not in res:
            raise SpotifyError(f"Connexion refusée : {res.get('error', 'réponse invalide')}")
        self._token_request({
            "grant_type": "authorization_code", "code": res["code"],
            "redirect_uri": REDIRECT_URI, "code_verifier": verifier,
        })

    def logout(self):
        self.token = self._me = None
        try:
            os.remove(TOKEN_FILE)
        except OSError:
            pass

    def _access_token(self):
        if not self.logged_in:
            raise SpotifyError("Non connecté.")
        if time.time() >= self.token["expires_at"]:
            self._token_request({"grant_type": "refresh_token", "refresh_token": self.token["refresh_token"]})
        return self.token["access_token"]

    # ---- requests ---------------------------------------------------------
    def _get(self, url, params=None):
        if not url.startswith("http"):
            url = API + url
        for _ in range(4):
            r = requests.get(url, params=params, timeout=15,
                             headers={"Authorization": f"Bearer {self._access_token()}"})
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", "1")) + 1)
                continue
            if r.status_code == 401:
                self.token["expires_at"] = 0  # force refresh on retry
                continue
            if r.status_code in (403, 404):
                raise SpotifyError(
                    f"Accès refusé ({r.status_code}). Seules les playlists dont tu es propriétaire "
                    "ou collaborateur sont lisibles via l'API Spotify.")
            if r.status_code != 200:
                raise SpotifyError(f"Erreur Spotify {r.status_code} : {r.text}")
            return r.json()
        raise SpotifyError("Spotify ne répond pas (trop de tentatives).")

    def _paginate(self, path, params):
        data = self._get(path, params)
        while True:
            yield from data.get("items", [])
            if not data.get("next"):
                return
            data = self._get(data["next"])

    # ---- data -------------------------------------------------------------
    def me(self):
        if not self._me:
            self._me = self._get("/me")
        return self._me

    def my_playlists(self):
        """Playlists whose items the API will actually return: owned or collaborative."""
        uid = self.me()["id"]
        out = []
        for p in self._paginate("/me/playlists", {"limit": 50}):
            if not p:
                continue
            if p["owner"]["id"] == uid or p.get("collaborative"):
                meta = p.get("items") or p.get("tracks") or {}  # field renamed in Feb 2026
                out.append({"id": p["id"], "name": p["name"], "total": meta.get("total")})
        return out

    def playlist_tracks(self, playlist_id):
        names = []
        for row in self._paginate(f"/playlists/{playlist_id}/items", {"limit": 50, "additional_types": "track"}):
            item = row.get("item") or row.get("track")  # `track` is the pre-2026 name
            if not item or not item.get("name"):
                continue
            artists = item.get("artists") or []
            who = artists[0]["name"] if artists else (item.get("show") or {}).get("name")
            names.append(f"{item['name']} — {who}" if who else item["name"])
        return names
