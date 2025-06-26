# 🎬 Self-Hosted Media Automation Stack

A fully automated media server stack built with Docker Compose.  
Automatically finds, downloads, organizes, and streams TV shows, movies, and music — with subtitles — all accessible via a sleek dashboard.

---

## 🧩 Included Containers

| Service      | Purpose                           | Port            |
| ------------ | --------------------------------- | --------------- |
| **Prowlarr** | Indexer manager for \*Arr apps    | `9696`          |
| **Sonarr**   | TV show management                | `8989`          |
| **Radarr**   | Movie management                  | `7878`          |
| **Lidarr**   | Music management                  | `8686`          |
| **Bazarr**   | Subtitles automation              | `6767`          |
| **Deluge**   | Torrent downloader                | `8112` (Web UI) |
| **Plex**     | Media playback & streaming server | `32400`         |
| **Heimdall** | Web dashboard for quick access    | `80`            |

---

## 🏗️ Folder Structure

```
.
├── compose.yaml
├── tv/                  # TV shows (Sonarr output)
├── movies/              # Movies (Radarr output)
├── music/               # Music (Lidarr output)
├── downloads/           # Deluge downloads
├── bazarr/config/
├── deluge/config/
├── heimdall/config/
├── lidarr/config/
├── plex/config/
├── prowlarr/config/
├── radarr/config/
├── sonarr/config/
```

> All services share access to `/downloads`, `/tv`, `/movies`, and `/music` to coordinate file handling.

---

## 🚀 Getting Started

1. **Clone the repo:**

   ```bash
   git clone https://github.com/yourusername/media-automation-stack.git
   cd media-automation-stack
   ```

2. **Start all containers:**

   ```bash
   docker-compose up -d
   ```

3. **Access your dashboard:**

   - [http://localhost](http://localhost) → Heimdall
   - Or access each service directly via its port

---

## 🛠️ First-Time Setup Checklist

- [ ] Link Prowlarr to Sonarr, Radarr, Lidarr
- [ ] Add working indexers (TorrentGalaxy, YTS, etc.)
- [ ] Configure quality profiles and root folders
- [ ] Connect Deluge to all \*Arr apps
- [ ] Set up Plex libraries for `/tv`, `/movies`, `/music`
- [ ] Add subtitle providers in Bazarr (e.g. OpenSubtitles, Subscene)
- [ ] Customize Heimdall with links and logos

---

## ✅ Features

- 🎯 Automatic search and downloading of content
- 🧠 Smart organization and renaming
- 🎞️ Subtitles downloaded for movies and shows
- 🧩 Unified dashboard with Heimdall
- 📡 LAN-friendly, no cloud dependency
- 📦 Fully Dockerized, portable setup

---

## 🔐 Optional Add-Ons

- 🔒 HTTPS with Traefik or Caddy
- 🧳 Remote access via Tailscale or VPN
- 🔑 Login protection via Authelia or Heimdall auth
- 🎬 Add Bazarr for subtitles (already included)
- 📥 Use private trackers with Prowlarr

---

## 🧼 Maintenance

**Stop the stack:**

```bash
docker-compose down
```

**Stop and remove everything (⚠️ wipes data):**

```bash
docker-compose down -v
```

---

## 📚 Credits

- [Sonarr](https://sonarr.tv/)
- [Radarr](https://radarr.video/)
- [Lidarr](https://lidarr.audio/)
- [Bazarr](https://www.bazarr.media/)
- [Deluge](https://deluge-torrent.org/)
- [Plex](https://www.plex.tv/)
- [Prowlarr](https://github.com/Prowlarr/Prowlarr)
- [Heimdall](https://heimdall.site/)
- Inspired by the r/selfhosted community

---

## 🧙 License

MIT — use freely, modify as needed.
