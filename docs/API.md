# API Documentation: Wild West Shootout

Railway-hosted Stats API endpoints.

---

## Base URL

Production: `https://shootout-production-XXXX.up.railway.app`

---

## Authentication

The API uses simple username/password authentication. Passwords are hashed with SHA-256.

---

## Endpoints

### Health Check

#### `GET /`
Returns API status.

**Response:**
```json
{
  "status": "ok",
  "service": "Wild West Shootout API",
  "version": "1.0.0"
}
```

#### `GET /api`
Returns available endpoints.

**Response:**
```json
{
  "status": "ok",
  "endpoints": [
    "POST /api/register",
    "POST /api/login",
    "GET /api/stats/:username",
    "POST /api/stats/:username",
    "GET /api/leaderboard/ai/wins",
    "GET /api/leaderboard/pvp/wins"
  ]
}
```

---

### User Registration

#### `POST /api/register`

Create a new user account.

**Request Body:**
```json
{
  "username": "string (2-15 chars)",
  "password": "string (required)"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Account created"
}
```

**Error Responses:**
- `400`: Username/password required, invalid length, or username exists
- `500`: Server error

---

### User Login

#### `POST /api/login`

Authenticate existing user.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "username": "ActualUsername"
}
```

**Error Responses:**
- `400`: Missing credentials
- `401`: Invalid password
- `404`: User not found
- `500`: Server error

---

### User Stats

#### `GET /api/stats/:username`

Get stats for a user.

**Response (200):**
```json
{
  "username": "Player1",
  "ai_stats": {
    "Tenderfoot": { "w": 5, "l": 2, "d": 1 },
    "Outlaw": { "w": 3, "l": 4, "d": 0 }
  },
  "pvp_wins": 10,
  "pvp_losses": 5,
  "pvp_draws": 2,
  "pvp_games": 17,
  "pvp_streak": 3,
  "pvp_best_streak": 5,
  "total_wagered": 1000,
  "achievements": ["first_blood", "streak_5"],
  "total_wins": 18,
  "total_draws": 3
}
```

#### `POST /api/stats/:username`

Update stats for a user.

**Request Body (all fields optional):**
```json
{
  "ai_stats": { "Tenderfoot": { "w": 6, "l": 2, "d": 1 } },
  "pvp_wins": 11,
  "pvp_losses": 5,
  "pvp_draws": 2,
  "pvp_games": 18,
  "pvp_streak": 4,
  "pvp_best_streak": 5,
  "total_wagered": 1100,
  "achievements": ["first_blood", "streak_5", "hot_hand"],
  "total_wins": 19,
  "total_draws": 3
}
```

**Success Response (200):**
```json
{
  "success": true
}
```

---

### Leaderboards

#### `GET /api/leaderboard/ai/wins`

Get top players by AI wins.

**Query Parameters:**
- `limit` (optional, default 10): Number of results

**Response (200):**
```json
{
  "leaderboard": [
    { "username": "TopPlayer", "value": 150 },
    { "username": "SecondPlace", "value": 120 }
  ]
}
```

#### `GET /api/leaderboard/pvp/wins`

Get top players by PvP wins.

**Query Parameters:**
- `limit` (optional, default 10): Number of results

**Response (200):**
```json
{
  "leaderboard": [
    { "username": "PvPKing", "value": 50 },
    { "username": "Duelist", "value": 45 }
  ]
}
```

---

## Data Storage

Stats are stored in `data.json` on the Railway server. Structure:

```json
{
  "users": {
    "Username1": {
      "password": "sha256_hash",
      "created": "2026-01-24T12:00:00Z",
      "ai_stats": {},
      "pvp_wins": 0,
      "pvp_losses": 0,
      "last_updated": "2026-01-24T13:00:00Z"
    }
  },
  "created": "2026-01-24T12:00:00Z"
}
```

---

## Error Handling

All errors return JSON with an `error` field:

```json
{
  "error": "Description of what went wrong"
}
```

---

## CORS

CORS is enabled for all origins. The API can be called from any domain.

---

## Rate Limiting

Currently no rate limiting is implemented. May be added if abuse is detected.
