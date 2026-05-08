# 🧩 ArrStack — Stack média automatisée

Une stack Docker complète pour télécharger, organiser et streamer vos films, séries et musique — avec sous-titres et un dashboard centralisé.

> **[CT101] Docker** ← Samba → **[CT103] Jellyfin** (serveur média séparé)

---

## 📦 Services

| Service | Rôle | Port |
|---|---|---|
| **Prowlarr** | Gestionnaire d'indexeurs pour les \*Arr | `9696` |
| **Sonarr** | Gestion des séries TV | `8989` |
| **Radarr** | Gestion des films | `7878` |
| **Lidarr** | Gestion de la musique | `8686` |
| **Bazarr** | Téléchargement automatique de sous-titres | `6767` |
| **Deluge** | Client torrent 🧲 | `8112` (Web UI) |
| **Heimdall** | Tableau de bord web | `8080` |

> 🎬 **Jellyfin** tourne sur un conteneur séparé (CT103) et accède aux médias via un partage Samba. Pas de Plex ici.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                Proxmox CT101 (Docker)               │
│                                                     │
│  [Heimdall] ──┬── [Prowlarr] ── indexeurs           │
│               ├── [Sonarr]    ── TV (/mnt/media/TV) │
│               ├── [Radarr]    ── Films (/mnt/media/Movies)
│               ├── [Lidarr]    ── Musique            │
│               ├── [Bazarr]    ── Sous-titres        │
│               └── [Deluge]    ── ↓ torrents         │
│                                  (/mnt/media/torrents)
│                         │                           │
│                    ┌────┘                           │
│                    ▼ Samba mount                    │
│            ┌──────────────────┐                     │
│            │   CT103 Jellyfin  │                     │
│            │   (serveur média) │                     │
│            └──────────────────┘                     │
└─────────────────────────────────────────────────────┘
```

### Volumes

| Chemin hôte | Usage |
|---|---|
| `/opt/arrstack/` | Configurations persistantes de tous les services |
| `/mnt/media/TV/` | Séries (sortie Sonarr) |
| `/mnt/media/Movies/` | Films (sortie Radarr) |
| `/mnt/media/Music/` | Musique (sortie Lidarr) |
| `/mnt/media/torrents/` | Téléchargements Deluge |

Tous les services partagent ces montures pour une coordination propre des fichiers.

---

## 🚀 Démarrage

```bash
# Cloner le dépôt
git clone git@github.com:limbsjones/torrents_stack.git
cd torrents_stack

# Lancer la stack
docker compose up -d

# Accès rapide
xdg-open http://localhost:8080   # Heimdall
# ou chaque service directement sur son port
```

### Prérequis

- Docker Engine 24+ et Docker Compose v2
- Les points de montage `/mnt/media/` doivent exister et être accessibles
- Optionnel : un partage Samba si les médias sont consommés par un autre hôte (CT103)

---

## 🔧 Configuration initiale

- [ ] Connecter Prowlarr à Sonarr, Radarr et Lidarr
- [ ] Ajouter des indexeurs (TorrentGalaxy, YTS, etc.)
- [ ] Configurer les profils de qualité et dossiers racines
- [ ] Lier Deluge aux \*Arr (catégories torrent, watch folders)
- [ ] Ajouter des fournisseurs de sous-titres dans Bazarr (OpenSubtitles, etc.)
- [ ] Personnaliser Heimdall (liens, icônes, fonds)
- [ ] Configurer Jellyfin (CT103) pour pointer sur les dossiers Samba

### Variables d'environnement

Le fichier `.env` contient :

```env
PUID=1000
PGID=1000
TZ=America/Toronto
```

Ajustez `PUID`/`PGID` selon votre utilisateur Docker.

---

## ✨ Fonctionnalités

- 🎯 Recherche et téléchargement automatiques
- 🧠 Organisation et renommage intelligents (Sonarr/Radarr)
- 🎞️ Sous-titres automatiques (Bazarr)
- 🧩 Dashboard centralisé (Heimdall)
- 📡 100% local, pas de dépendance cloud
- 🐳 Entièrement Dockerisé, portable
- ✅ Healthchecks sur tous les services

---

## 🧹 Maintenance

```bash
# Arrêter la stack
docker compose down

# Arrêter + supprimer les volumes (⚠️ données perdues)
docker compose down -v

# Mettre à jour toutes les images
docker compose pull
docker compose up -d

# Voir les logs en temps réel
docker compose logs -f
```

---

## 🔐 Bonus (optionnel)

- 🔒 HTTPS avec Traefik ou Caddy
- 🧳 Accès distant via Tailscale
- 🔑 Portail d'authentification (Authelia)
- 📥 Trackers privés dans Prowlarr

---

## 📚 Crédits

- [Sonarr](https://sonarr.tv) · [Radarr](https://radarr.video) · [Lidarr](https://lidarr.audio)
- [Bazarr](https://www.bazarr.media) · [Deluge](https://deluge-torrent.org)
- [Prowlarr](https://github.com/Prowlarr/Prowlarr) · [Heimdall](https://heimdall.site)
- [linuxserver.io](https://linuxserver.io) — images Docker

---

## 📄 Licence

MIT — faites ce que vous voulez.
