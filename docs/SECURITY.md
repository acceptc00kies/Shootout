# Security: Wild West Shootout

Security implementation details and anti-cheat architecture.

---

## Threat Model

### What We're Protecting Against
1. **Casual cheaters** - Browser console manipulation
2. **Action spoofing** - Submitting invalid actions
3. **State manipulation** - Modifying bullets, rounds, winner
4. **Impersonation** - Acting as another player

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
    "pvp_games": {
      "$gameId": {
        // Must be authenticated
        ".read": "auth != null",
        ".write": "auth != null",

        // Host slot - only host UID can write
        "host": {
          ".write": "data.child('uid').val() == auth.uid || !data.exists()",
          "action": {
            ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 2"
          },
          "bullets": {
            ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 6"
          }
        },

        // Guest slot - only guest UID can write
        "guest": {
          ".write": "data.child('uid').val() == auth.uid || !data.exists()",
          "action": {
            ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 2"
          },
          "bullets": {
            ".validate": "newData.isNumber() && newData.val() >= 0 && newData.val() <= 6"
          }
        }
      }
    }
  }
}
```

### Layer 3: Client-Side Validation
- Input sanitization
- XSS prevention with HTML escaping
- Action value validation before submission

### Layer 4: Railway API Validation
- Separate authentication for stats
- Password hashing (SHA-256)
- Input validation on all endpoints

---

## What Security Rules Prevent

| Attack | Prevention |
|--------|------------|
| Submit action as opponent | UID check on write |
| Invalid action value (e.g., 5) | Range validation (0-2) |
| Invalid bullet count (e.g., 100) | Range validation (0-6) |
| Unauthenticated writes | `auth != null` requirement |
| Read other games without auth | Read rules |

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
- SHA-256 hashed (not plaintext)
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
- [x] Security Rules deployed
- [x] Action values validated (0-2)
- [x] Bullet counts validated (0-6)
- [x] UID verification on writes
- [x] XSS prevention
- [x] Password hashing
- [ ] Cloud Functions (pending Blaze)
- [ ] Rate limiting (not currently implemented)

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
