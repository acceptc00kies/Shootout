# Architecture: Wild West Shootout

Technical architecture and design decisions.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     index.html                            │   │
│  │  - Game UI and rendering                                  │   │
│  │  - AI opponent logic                                      │   │
│  │  - Firebase SDK integration                               │   │
│  │  - Stats API communication                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────┬───────────────┘
                         │                        │
                         ▼                        ▼
┌────────────────────────────────────┐  ┌────────────────────────┐
│         FIREBASE (Google)          │  │    RAILWAY (Stats)      │
│  ┌──────────────────────────────┐  │  │  ┌──────────────────┐  │
│  │     Realtime Database        │  │  │  │   Flask API      │  │
│  │  - PvP game state            │  │  │  │  - User accounts │  │
│  │  - Player actions            │  │  │  │  - Stats storage │  │
│  │  - Security Rules validation │  │  │  │  - Leaderboards  │  │
│  └──────────────────────────────┘  │  │  └──────────────────┘  │
│  ┌──────────────────────────────┐  │  │  ┌──────────────────┐  │
│  │     Anonymous Auth           │  │  │  │   data.json      │  │
│  │  - Player identification     │  │  │  │  - Persistent    │  │
│  │  - Zero-friction login       │  │  │  │    storage       │  │
│  └──────────────────────────────┘  │  │  └──────────────────┘  │
└────────────────────────────────────┘  └────────────────────────┘
```

---

## Components

### Frontend (index.html)
**Technology:** Single HTML file with embedded CSS and vanilla JavaScript
**Purpose:**
- Game rendering and UI
- AI opponent logic (6 difficulty levels)
- Firebase SDK for realtime PvP
- Stats API client for accounts/leaderboards

### Firebase Realtime Database
**Technology:** Firebase Realtime Database
**Purpose:**
- Store active PvP game state
- Realtime sync between players
- Security Rules enforce valid game state

### Firebase Anonymous Auth
**Technology:** Firebase Authentication (Anonymous provider)
**Purpose:**
- Identify players without requiring signup
- Enable Security Rules to validate player identity
- Support upgrade to full accounts later

### Railway Stats API
**Technology:** Python Flask + Gunicorn
**Purpose:**
- Persistent user accounts (separate from Firebase anonymous)
- Stats tracking (wins, losses, achievements)
- Leaderboard queries

---

## Data Flow

### PvP Game Flow
1. Host creates game → writes to `/pvp_games/{id}` with status "waiting"
2. Guest joins → updates game with guest UID
3. Each player submits action → writes to their slot
4. Both actions present → client computes result
5. Result written → round advances or game ends
6. Stats synced to Railway API

### AI Game Flow
1. Player selects difficulty → AI profile loaded
2. Player submits action → AI computes response
3. Result calculated locally → displayed
4. Stats synced to Railway API

---

## Technology Choices

| Component | Technology | Reasoning |
|-----------|------------|-----------|
| Frontend | Vanilla JS + HTML | Zero build tools, deploy anywhere |
| PvP Sync | Firebase Realtime DB | Excellent realtime, free tier |
| Auth | Firebase Anonymous | Zero friction, upgradeable |
| Stats Backend | Railway + Flask | Python support, simple deploy |
| Security | Firebase Rules | Free tier validation |

---

## External Services

| Service | Purpose | Config Files |
|---------|---------|--------------|
| Firebase | Realtime DB + Auth | `firebase.json`, `.firebaserc` |
| Railway | Stats API hosting | `Procfile`, `railway.json` |

---

## Security Boundaries

### Trusted (Server-side)
- Firebase Security Rules
- Railway API validation

### Untrusted (Client-side)
- All game state computations
- UI rendering
- AI logic

See [SECURITY.md](SECURITY.md) for detailed security architecture.

---

## Known Limitations

1. **Game logic runs client-side** - Security Rules validate structure, not logic
2. **Anonymous auth data loss** - Clearing browser loses Firebase account
3. **Separate account systems** - Firebase auth and Railway accounts are independent
4. **No ranked matchmaking** - Random opponent matching only
