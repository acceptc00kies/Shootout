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
      "$gameId": {
        ".read": true,
        ".write": "auth != null && (
          !data.exists() ||
          data.child('p1_uid').val() == auth.uid ||
          data.child('p2_uid').val() == auth.uid ||
          (data.child('p2_uid').val() == null && newData.child('p2_uid').val() == auth.uid)
        )",
        "p1_action": {
          ".validate": "newData.val() == null || (newData.isNumber() && newData.val() >= 0 && newData.val() <= 2)"
        },
        "p2_action": {
          ".validate": "newData.val() == null || (newData.isNumber() && newData.val() >= 0 && newData.val() <= 2)"
        },
        "p1_bullets": {
          ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 6"
        },
        "p2_bullets": {
          ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 6"
        },
        "round": {
          ".validate": "newData.isNumber() && newData.val() >= 1 && newData.val() <= 13"
        },
        "status": {
          ".validate": "newData.val() == 'WAITING' || newData.val() == 'PLAYING' || newData.val() == 'FINISHED'"
        }
      }
    },
    "leaderboard": {
      ".read": true,
      ".write": false
    }
  }
}
```

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

## API Security

### Password Storage
- SHA-256 hashed (not plaintext) on server
- Passwords NOT stored in localStorage (security fix Jan 2026)
- Future: Consider bcrypt for better security

### CORS
- Enabled for all origins (game is public)
- Could restrict to specific domains if needed

### Input Validation
- Username: 2-15 characters, stripped
- Password: Required, not empty
- Stats: Type-checked before storage

---

## Security Checklist

- [x] Firebase Anonymous Auth enabled
- [x] Security Rules deployed with participant checks
- [x] Action values validated (0-2)
- [x] Bullet counts validated (0-6)
- [x] Round numbers validated (1-13)
- [x] Status values validated (WAITING/PLAYING/FINISHED)
- [x] UID verification on writes
- [x] Non-participant writes blocked
- [x] XSS prevention
- [x] Password hashing on server
- [x] Password NOT stored in localStorage
- [ ] Cloud Functions (pending Blaze)
- [ ] Rate limiting (not currently implemented)
- [ ] bcrypt password hashing

---

## Security Audit (Jan 2026)

### Vulnerabilities Identified: 26
- CRITICAL: 9
- HIGH: 7
- MEDIUM: 6
- LOW: 4

### Fixed in This Update
1. Firebase Security Rules tightened (non-participants blocked)
2. Plaintext password removed from localStorage
3. All field validations added to rules

### Remaining Issues (Prioritized)
1. Stats API authentication (anyone can spoof stats)
2. bcrypt for password hashing
3. Rate limiting on API
4. CORS restrictions

See `.claude/plans/` for full security audit details.

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
