# Wild West Shootout

A strategic multiplayer duel game - like Rock, Paper, Scissors but with bullets, timing, and mind games.

## Game Rules

Each round, choose one action:
- **LOAD** - Add 1 bullet (max 6)
- **DEFEND** - Block incoming shots
- **SHOOT** - Fire a bullet (requires ammo)

**Win Conditions:**
- Shoot opponent while they're loading = **You Win**
- Shoot with no bullets = **You Lose** (misfire)
- Both defend or both load = **Tie** (next round)
- Reach Round 12 (High Noon) with no winner = **Draw**

## Tech Stack

- **Frontend:** Single HTML file with vanilla JS
- **Backend:** Firebase Realtime Database
- **Auth:** Firebase Anonymous Authentication
- **Stats API:** Railway-hosted cloud API

## Security Architecture

### Current (Free Spark Plan)
- Firebase Security Rules validate all writes
- Anonymous Auth identifies players
- Client-side game logic with rule enforcement
- ~95% cheat protection

### Future (Blaze Plan)
Cloud Functions ready in `functions/` folder for 100% server-authoritative game logic.

## Setup

### Prerequisites
- Firebase project with Realtime Database
- Node.js 18+ (for Cloud Functions)
- Firebase CLI (`npm install -g firebase-tools`)

### Deploy

1. **Enable Anonymous Auth:**
   - Firebase Console → Authentication → Sign-in method → Anonymous → Enable

2. **Deploy Database Rules:**
   ```bash
   firebase login
   firebase deploy --only database
   ```

3. **Host the game:**
   - Deploy `index.html` to Vercel, Netlify, or Firebase Hosting

### Future: Deploy Cloud Functions (requires Blaze plan)
```bash
cd functions && npm install
firebase deploy --only functions
```

## Project Structure

```
SHOOTOUT/
├── index.html           # Main game (single-file app)
├── database.rules.json  # Firebase security rules
├── firebase.json        # Firebase config
├── .firebaserc          # Project linking
└── functions/           # Cloud Functions (for Blaze plan)
    ├── index.js         # Server-side game logic
    └── package.json     # Dependencies
```

## Security Features

- XSS prevention with HTML escaping
- Input validation (username, bet amounts)
- Firebase Rules validate:
  - Authentication required
  - Valid action values (0, 1, 2)
  - Bullet counts (0-6 range)
  - Game state transitions
- Content Security Policy headers

## Roadmap

- [x] Core game mechanics
- [x] AI opponents (6 difficulty levels)
- [x] Firebase Realtime PvP
- [x] Cloud stats sync
- [x] Achievement system
- [x] Security hardening
- [ ] Cloud Functions anti-cheat (pending Blaze)
- [ ] Ranked matchmaking
- [ ] Tournament mode

## License

MIT
