# Build History: Wild West Shootout

Step-by-step documentation of how this project was built, with reasoning for every decision.

---

## Project Overview

**Purpose:** Strategic multiplayer duel game - Rock-Paper-Scissors with bullets, timing, and mind games
**Started:** January 2026
**Status:** Deployed and operational

---

## Phase 1: Core Game Design

### Step 1.1: Game Mechanics
**What:** Designed a 3-action combat system (Load, Defend, Shoot) with bullet economy
**Why:** RPS variants need asymmetry to create depth. Bullet management adds resource strategy.
**Alternatives considered:**
- Pure RPS (too simple)
- Card-based combat (too complex for quick duels)
**Tradeoffs:** Bullet system means games can stall (solved with High Noon round limit)

### Step 1.2: Single-File Architecture
**What:** Built entire frontend in one `index.html` file
**Why:**
- Zero build tools required
- Easy deployment anywhere (GitHub Pages, Vercel, etc.)
- Simple to understand and modify
**Alternatives considered:** React, Vue frameworks
**Tradeoffs:** No component reuse, but acceptable for game this size

### Step 1.3: Vanilla JavaScript
**What:** No frameworks, pure JS
**Why:**
- No build step
- Smaller payload
- Full control over behavior
**Alternatives considered:** React for state management
**Tradeoffs:** Manual state management, but game state is simple enough

---

## Phase 2: AI System

### Step 2.1: Six Difficulty Levels
**What:** Implemented AI with personality-based decision making
**Why:** Single-player practice before PvP, difficulty progression
**Approach:** Each AI has weighted probabilities for actions based on game state
**Tradeoffs:** Predictable at high skill levels (acceptable for practice mode)

---

## Phase 3: Firebase Integration

### Step 3.1: Realtime Database for PvP
**What:** Firebase Realtime Database for game state sync
**Why:**
- Realtime sync perfect for turn-based multiplayer
- Free tier sufficient for this scale
- Simple SDK integration
**Alternatives considered:**
- Supabase (realtime less mature at time)
- Custom WebSocket server (more work)
**Tradeoffs:** Vendor lock-in, but Firebase benefits outweigh

### Step 3.2: Anonymous Authentication
**What:** Firebase Anonymous Auth for player identification
**Why:**
- Zero-friction onboarding
- Can upgrade to full account later
- Required for security rules
**Alternatives considered:** Guest tokens (less secure)
**Tradeoffs:** Account loss if user clears browser data

### Step 3.3: Game State Structure
**What:** Designed `/pvp_games/{gameId}` structure with host/guest pattern
**Why:** Clear ownership, simple join flow, supports spectating
**Structure:**
```
pvp_games/{id}:
  host: {uid, action, bullets}
  guest: {uid, action, bullets}
  round, status, winner
```

---

## Phase 4: Anti-Cheat Implementation

### Step 4.1: Initial Approach - Client-Side Only
**What:** Basic validation in JavaScript
**Why:** Quick implementation for MVP
**Problem:** Completely bypassable via browser console

### Step 4.2: Cloud Functions (Blocked)
**What:** Attempted server-authoritative game logic via Cloud Functions
**Why:** 100% cheat-proof - server computes all results
**Problem:** Firebase Cloud Functions require Blaze (paid) plan
**Blocker:** Payment page was non-functional, couldn't upgrade

### Step 4.3: Security Rules Solution
**What:** Firebase Security Rules for data validation
**Why:**
- Works on free Spark plan
- Validates structure, auth, and ranges
- ~95% effective against casual cheating
**Implementation:**
- Require authentication
- Validate action values (0, 1, 2)
- Validate bullet counts (0-6)
- Validate game state transitions
**Tradeoffs:**
- Rules can't compute game logic, only validate structure
- Sophisticated cheaters could still exploit edge cases
- Cloud Functions kept ready in `functions/` for future upgrade

---

## Phase 5: Stats Backend (Railway)

### Step 5.1: Why Separate Backend
**What:** Flask API on Railway for stats/leaderboards
**Why:**
- Firebase Rules can't do complex aggregations
- Need persistent user accounts beyond anonymous auth
- Leaderboards require sorted queries
**Alternatives considered:**
- Firebase Cloud Functions (blocked by Blaze requirement)
- Vercel serverless (Python support is secondary)

### Step 5.2: Railway Deployment
**What:** Flask + Gunicorn on Railway
**Why:**
- Python-first platform
- Simple Procfile deployment
- Reliable uptime
**Files created:**
- `server.py` - Flask API
- `requirements.txt` - Dependencies
- `Procfile` - Start command
- `runtime.txt` - Python version
- `railway.json` - Build config

### Step 5.3: API Design
**What:** RESTful endpoints for auth, stats, leaderboards
**Endpoints:**
- `POST /api/register` - Create account
- `POST /api/login` - Authenticate
- `GET/POST /api/stats/:username` - User stats
- `GET /api/leaderboard/ai/wins` - AI leaderboard
- `GET /api/leaderboard/pvp/wins` - PvP leaderboard

---

## Phase 6: PvP Bug Fixes (Multi-Session Debugging)

### Context
Claude conversation ran out of context during debugging. Required context recovery and continuation across sessions using `.claude/plans/` files and BUILD_HISTORY.md for state persistence.

### Step 6.1: Game Freeze After Round 1
**Problem:** Both players calling `resolveRound()` caused race condition
**Root cause:** Firebase listener triggered for both players when actions submitted
**Solution:** Only P1 (host) resolves rounds + added `isResolving` flag to prevent double resolution
**Lesson:** Single source of truth for state mutations in realtime systems

### Step 6.2: Stale Games in Lobby
**Problem:** Games stuck in WAITING status after host leaves
**Solution:** Added `onDisconnect().remove()` for automatic cleanup + 10-minute age filter in lobby listing
**Lesson:** Always handle disconnect scenarios in realtime apps

### Step 6.3: P1 Not Updating When P2 Joins
**Problem:** Firebase drops null values (stores as undefined)
**Root cause:** `undefined !== null` is TRUE in JavaScript, so checks like `g.p2_uid !== null` returned TRUE for undefined
**Solution:** Changed all null checks to `typeof field === 'number'`
**Lesson:** Firebase null-dropping is a critical gotcha

### Step 6.4: Actions Not Submitting
**Problem:** Same null-dropping issue in `submitAction()` function
**Root cause:** After round resets, `p1_action` becomes undefined. Check `g[myActionField] !== null` returned TRUE, blocking new action submission
**Solution:** Changed to `typeof g[myActionField] === 'number'`
**Lesson:** Once you find a bug pattern, search entire codebase for same issue

### Step 6.5: Proactive Bug Prevention
**What:** After fixing immediate bugs, proactively searched codebase for related issues
**Found and fixed:**
- **Fix A:** Reset actions when game ends (prevent stale state on re-render)
- **Fix B:** Both players skip render during resolution (prevent race condition where P2 renders intermediate state)
- **Fix C:** Add validation to `resolveRound()` (defensive check that actions are valid numbers)
- **Fix D:** Loss color in log (was green for all outcomes, now red for losses)
- **Fix E:** Debug output for silent failures in `submitAction()` (log when game/auth missing)

**Key Decision:** Proactive bug hunting after pattern discovery
**Tradeoff:** Extra time upfront → fewer bugs in production

### Step 6.6: Bullet Limit UI Feedback
**Problem:** LOAD button had no visual feedback at max capacity (6 bullets)
**Root cause:** Unlike SHOOT (disabled at 0), LOAD had no disabled state
**Solution:**
- UI: LOAD button disabled at 6 bullets, shows "(Full!)"
- Validation: Server rejects LOAD at max with alert
- Safety: Added round > 12 check to prevent edge cases
**Lesson:** Action buttons should show state for ALL boundary conditions, not just some

---

## Phase 7: Security Audit & Hardening

### Context
Comprehensive security audit performed to identify vulnerabilities before scaling.

### Step 7.1: Security Audit
**What:** Full security and privacy review of frontend, backend, and Firebase configuration
**Found:** 26 vulnerabilities (9 CRITICAL, 7 HIGH, 6 MEDIUM, 4 LOW)
**Key Issues:**
- Firebase Security Rules too permissive (any auth user could modify any game)
- Plaintext password stored in localStorage
- SECURITY.md documented wrong database path (`pvp_games` vs actual `games`)
- Stats API had no authentication

### Step 7.2: Firebase Security Rules Tightening
**Problem:** Rules allowed any authenticated user to write to any game
**Solution:** Added participant checks to write rules:
```
auth.uid == p1_uid || auth.uid == p2_uid || joining game
```
**Also added:** Field validations for actions (0-2), bullets (0-6), rounds (1-13), status
**Lesson:** Always test security rules match actual database paths

### Step 7.3: Remove Plaintext Password Storage
**Problem:** localStorage stored `{un, pw}` in plaintext
**Risk:** XSS or physical access could expose passwords
**Solution:** Changed to store only `{un}` (username for convenience)
**Tradeoff:** Users must re-enter password each session
**Lesson:** Convenience vs security tradeoff - chose security

### Step 7.4: Documentation Sync
**Problem:** SECURITY.md documented `pvp_games` but game uses `games` path
**Solution:** Updated SECURITY.md with actual rules and paths
**Lesson:** Security documentation must match implementation exactly

---

## Problems Encountered

### Problem 1: Firebase Blaze Payment Page
**Cause:** Firebase Console payment page would not load (infinite spinner)
**Solution:** Pivoted to Security Rules approach instead of Cloud Functions
**Lesson:** Always have a free-tier fallback plan

### Problem 2: Railway API Crash After Force Push
**Cause:** Accidentally deleted backend files when force-pushing game updates
**Solution:** Recreated Flask API from scratch, added all required config files
**Lesson:** Be careful with force push, ensure all services are tracked

### Problem 3: GitHub Secrets Warning
**Cause:** GitHub detected Firebase API key in code
**Solution:** This is a false positive - Firebase client API keys are designed to be public. Security comes from Security Rules, not key secrecy.
**Lesson:** Understand which secrets are actually secret

### Problem 4: Firebase Null-Dropping
**Cause:** Firebase Realtime Database drops null values entirely (stores as undefined instead)
**Impact:** All checks like `field !== null` return TRUE for undefined, causing logic failures:
- P2 join detection failed (thought P2 already joined)
- Action submission blocked (thought action already submitted)
- Round resolution triggered incorrectly
**Solution:** Use `typeof field === 'number'` instead of `field !== null` for all Firebase value checks
**Lesson:** This is a critical Firebase gotcha that affects any realtime game state management

---

## Key Decisions Summary

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Frontend | Single HTML file | Zero build tools, deploy anywhere |
| Framework | Vanilla JS | No dependencies, full control |
| Realtime | Firebase Realtime DB | Free tier, excellent sync |
| Auth | Firebase Anonymous | Zero friction, upgradeable |
| Anti-cheat | Security Rules | Free tier solution, ~95% effective |
| Stats Backend | Railway + Flask | Python support, simple deploy |
| Cloud Functions | Prepared but unused | Ready for Blaze upgrade |

---

## Architecture Evolution

```
v1: Pure client-side → Insecure
v2: Cloud Functions attempt → Blocked by Blaze requirement
v3: Security Rules + Railway API → Production
v4: Security hardening → Current (participant checks, no password storage)
```

---

## Future Considerations

- Upgrade to Blaze plan when payment works → enable Cloud Functions
- Ranked matchmaking system
- Tournament mode
- More sophisticated anti-cheat if needed

---

## Standards

This project follows [acceptc00kies/master-guidance](https://github.com/acceptc00kies/master-guidance)
