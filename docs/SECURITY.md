# Security: Wild West Shootout

Security implementation details and anti-cheat architecture.

---

## Threat Model

### What We're Protecting Against
1. **Casual cheaters** - Browser console manipulation
2. **Action spoofing** - Submitting invalid actions
3. **State manipulation** - Modifying bullets, rounds, winner
4. **Impersonation** - Acting as another player
5. **Non-participants** - Modifying games they're not in

### What We Accept (Current Architecture)
- Sophisticated attackers with deep Firebase knowledge
- Client-side game logic can be inspected
- ~5% edge cases in complex timing scenarios

---

## Defense Layers

### Layer 1: Firebase Anonymous Authentication
- Every player has unique UID
- Security Rules verify UID matches claimed player
- Cannot impersonate another player's slot

### Layer 2: Firebase Security Rules
Location: `database.rules.json`

```json
{
  "rules": {
    "games": {
      ".read": true,
      ".indexOn": ["status", "created"],
      "$gameId": {
        ".write": "auth != null && (!data.exists() || data.child('p1_uid').val() == auth.uid || data.child('p2_uid').val() == auth.uid || (data.child('p2_uid').val() == null && newData.child('p2_uid').val() == auth.uid))",
        "p1": { ".validate": "newData.isString()" },
        "p2": { ".validate": "newData.val() == null || newData.isString()" },
        "p1_uid": { ".validate": "newData.isString()" },
        "p2_uid": { ".validate": "newData.val() == null || newData.isString()" },
        "p1_action": { ".validate": "newData.val() == null || (newData.isNumber() && newData.val() >= 0 && newData.val() <= 2)" },
        "p2_action": { ".validate": "newData.val() == null || (newData.isNumber() && newData.val() >= 0 && newData.val() <= 2)" },
        "p1_bullets": { ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 6" },
        "p2_bullets": { ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 6" },
        "round": { ".validate": "newData.isNumber() && newData.val() >= 1 && newData.val() <= 13" },
        "status": { ".validate": "newData.val() == 'WAITING' || newData.val() == 'PLAYING' || newData.val() == 'FINISHED'" },
        "winner": { ".validate": "newData.val() == null || newData.isString()" },
        "winner_uid": { ".validate": "newData.val() == null || newData.isString()" },
        "bet": { ".validate": "newData.isNumber() && newData.val() >= 0" },
        "created": { ".validate": "newData.isNumber()" },
        "id": { ".validate": "newData.isString()" },
        "last_round": {
          "round": { ".validate": "newData.isNumber()" },
          "p1_action": { ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 2" },
          "p2_action": { ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 2" },
          "winner": { ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 2" }
        },
        "$other": { ".validate": false }
      }
    },
    "leaderboard": {
      ".read": true,
      ".write": false
    }
  }
}
```

**Key Design Notes:**
- `.read: true` at `games` level (not `$gameId`) - enables `orderByChild()` queries
- `.indexOn` for query performance on status and created fields
- All fields explicitly listed due to `$other: { ".validate": false }`
- `last_round` object stores round history for UI feedback

**Write Rules Explained:**
- `!data.exists()` - Anyone authenticated can create a new game
- `data.child('p1_uid').val() == auth.uid` - Host can modify their game
- `data.child('p2_uid').val() == auth.uid` - Guest can modify their game
- `data.child('p2_uid').val() == null && newData.child('p2_uid').val() == auth.uid` - Anyone can join an open game

### Layer 3: Client-Side Validation
- Input sanitization
- XSS prevention with HTML escaping
- Action value validation before submission

### Layer 4: Railway API Validation
- Separate authentication for stats
- Password hashing (SHA-256)
- Input validation on all endpoints

### Layer 5: localStorage Security
- Only username stored for convenience (not password)
- Password must be entered on each session

---

## What Security Rules Prevent

| Attack | Prevention |
|--------|------------|
| Submit action as opponent | UID check on write |
| Modify someone else's game | Participant check on write |
| Invalid action value (e.g., 5) | Range validation (0-2) |
| Invalid bullet count (e.g., 100) | Range validation (0-6) |
| Invalid round number | Range validation (1-13) |
| Invalid status value | Enum validation |
| Unauthenticated writes | `auth != null` requirement |

## What Security Rules Cannot Prevent

| Attack | Reason |
|--------|--------|
| Pre-computing opponent action | Rules validate structure, not timing |
| Inconsistent bullet tracking | Complex state logic exceeds rule capability |
| Replay attacks (timing) | Would require Cloud Functions |

---

## Future: Cloud Functions (Blaze Plan)

When Blaze plan is available, `functions/index.js` enables:
- Server-authoritative game logic
- Actions submitted, server computes result
- 100% cheat-proof (client never sees opponent's action)

Current status: Code ready, blocked by payment processing.

---

## API Security (v2.4.0)

### Password Storage
- **bcrypt** hashed (upgraded from SHA-256)
- Automatic migration: legacy SHA-256 hashes upgraded on login
- Passwords NOT stored in localStorage

### Authentication & Sessions
- Token-based authentication (Bearer tokens)
- **Single-session enforcement**: New login invalidates all previous sessions
- Session validation required before starting games
- 24-hour session expiry

### Rate Limiting (All Endpoints)
| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `/api/register` | 3/min | Prevent account spam |
| `/api/login` | 5/min | Prevent brute force |
| `/api/logout` | 10/min | Low priority |
| `/api/session/validate` | 60/min | Allow rapid gameplay |
| `/api/stats` GET | 30/min | Profile loading |
| `/api/stats` POST | 30/min | Stats sync |
| `/api/leaderboard/*` | 20/min | Leaderboard views |
| Health endpoints | Exempt | Monitoring |
| **Global default** | 200/day, 50/hr | Catch-all |

### CORS
- Restricted to specific origins:
  - `https://wild-west-shootout.vercel.app`
  - `localhost:3000`, `localhost:5500` (dev)
- Credentials supported
- Authorization header allowed

### Input Validation
- Username: 2-15 characters, stripped
- Password: Required, not empty
- Stats: Type-checked, auth-verified before storage
- User can only modify own stats

---

## Security Checklist

### Firebase Security
- [x] Firebase Anonymous Auth enabled
- [x] Security Rules deployed with participant checks
- [x] Action values validated (0-2)
- [x] Bullet counts validated (0-6)
- [x] Round numbers validated (1-13)
- [x] Status values validated (WAITING/PLAYING/FINISHED)
- [x] UID verification on writes
- [x] Non-participant writes blocked
- [x] All fields explicitly listed (`$other: false`)

### Stats API Security
- [x] bcrypt password hashing
- [x] Token-based authentication
- [x] Single-session enforcement
- [x] Session validation before games
- [x] Rate limiting (all endpoints)
- [x] CORS restricted to known origins
- [x] Stats modification requires auth + own user
- [x] Delta sync (prevents overwrite attacks)

### Client-Side
- [x] XSS prevention
- [x] Password NOT stored in localStorage
- [x] Self-play prevention (UID + username check)
- [x] Graceful failure handling

### Pending
- [ ] Cloud Functions (pending Blaze plan)
- [ ] Persistent sessions (currently in-memory)

---

## Security Audit (Jan 2026)

### Vulnerabilities Identified: 26
- CRITICAL: 9 → **0 remaining**
- HIGH: 7 → **0 remaining**
- MEDIUM: 6 → **1 remaining** (in-memory sessions)
- LOW: 4 → **1 remaining** (session expiry on restart)

### Fixed (Phase 7)
1. Firebase Security Rules tightened (non-participants blocked)
2. Plaintext password removed from localStorage
3. All field validations added to rules

### Fixed (Phase 8)
1. Stats API authentication (token-based)
2. bcrypt password hashing (with SHA-256 migration)
3. Rate limiting on ALL endpoints
4. CORS restricted to known origins
5. Single-session enforcement (anti-botting)
6. Session validation before games
7. Self-play prevention
8. Graceful stats sync failure handling

### Remaining (Low Priority)
- In-memory sessions cleared on server restart (users re-login)
- Rate limit storage in-memory (resets on restart)

**Mitigation:** Both are acceptable for current scale. Can add Redis/persistent storage if needed.

---

## Incident Response

If cheating is detected:
1. Check Security Rules are deployed: `firebase deploy --only database`
2. Review Firebase Console for suspicious writes
3. Consider upgrading to Blaze for Cloud Functions
4. Add rate limiting if needed

---

## Standards

This project follows security patterns from [acceptc00kies/master-guidance](https://github.com/acceptc00kies/master-guidance)
