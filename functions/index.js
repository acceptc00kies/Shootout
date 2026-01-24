/**
 * Wild West Shootout - Anti-Cheat Cloud Functions
 * All game logic runs server-side to prevent cheating
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');

admin.initializeApp();
const db = admin.database();

// ============================================================================
// GAME LOGIC (same as client, but server-authoritative)
// ============================================================================

function calcWinner(p1Action, p1Bullets, p2Action, p2Bullets) {
    // SHOOT with bullets vs LOAD = shooter wins
    if (p1Action === 2 && p1Bullets > 0 && p2Action === 0) return 1;
    if (p2Action === 2 && p2Bullets > 0 && p1Action === 0) return 2;
    // SHOOT with no bullets = opponent wins (misfire)
    if (p1Action === 2 && p1Bullets === 0) return 2;
    if (p2Action === 2 && p2Bullets === 0) return 1;
    // All other cases = tie (both survive)
    return 0;
}

function calculateNewBullets(action, currentBullets) {
    if (action === 0) return Math.min(6, currentBullets + 1); // LOAD
    if (action === 2 && currentBullets > 0) return currentBullets - 1; // SHOOT
    return currentBullets; // DEFEND or invalid
}

function generateGameId() {
    return Math.random().toString(36).substr(2, 8).toUpperCase();
}

// ============================================================================
// CALLABLE FUNCTIONS
// ============================================================================

/**
 * Create a new game
 * @param {number} bet - Wager amount
 * @param {string} username - Player's display name
 */
exports.createGame = functions.https.onCall(async (data, context) => {
    // Verify authentication
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const { bet, username } = data;

    // Validate inputs
    if (typeof bet !== 'number' || bet < 0.01 || bet > 1000) {
        throw new functions.https.HttpsError('invalid-argument', 'Invalid bet amount');
    }
    if (!username || typeof username !== 'string' || !/^[a-zA-Z0-9_]{2,15}$/.test(username)) {
        throw new functions.https.HttpsError('invalid-argument', 'Invalid username');
    }

    const gameId = generateGameId();
    const gameData = {
        id: gameId,
        p1: username,
        p1_uid: context.auth.uid,
        p2: null,
        p2_uid: null,
        bet: bet,
        round: 1,
        p1_bullets: 0,
        p2_bullets: 0,
        p1_action: null,
        p2_action: null,
        status: 'WAITING',
        created: admin.database.ServerValue.TIMESTAMP
    };

    await db.ref(`games/${gameId}`).set(gameData);

    return { gameId, success: true };
});

/**
 * Join an existing game
 * @param {string} gameId - Game to join
 * @param {string} username - Player's display name
 */
exports.joinGame = functions.https.onCall(async (data, context) => {
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const { gameId, username } = data;

    if (!gameId || typeof gameId !== 'string') {
        throw new functions.https.HttpsError('invalid-argument', 'Invalid game ID');
    }
    if (!username || typeof username !== 'string' || !/^[a-zA-Z0-9_]{2,15}$/.test(username)) {
        throw new functions.https.HttpsError('invalid-argument', 'Invalid username');
    }

    const gameRef = db.ref(`games/${gameId}`);

    // Use transaction to prevent race conditions
    const result = await gameRef.transaction((game) => {
        if (!game) {
            return; // Game doesn't exist, abort
        }
        if (game.status !== 'WAITING') {
            return; // Game already started, abort
        }
        if (game.p1_uid === context.auth.uid) {
            return; // Can't join own game, abort
        }

        // Join the game
        game.p2 = username;
        game.p2_uid = context.auth.uid;
        game.status = 'PLAYING';
        return game;
    });

    if (!result.committed) {
        throw new functions.https.HttpsError('failed-precondition', 'Could not join game');
    }

    return { success: true };
});

/**
 * Submit an action for the current round
 * @param {string} gameId - Game ID
 * @param {number} action - 0=LOAD, 1=DEFEND, 2=SHOOT
 */
exports.submitAction = functions.https.onCall(async (data, context) => {
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const { gameId, action } = data;

    if (!gameId || typeof gameId !== 'string') {
        throw new functions.https.HttpsError('invalid-argument', 'Invalid game ID');
    }
    if (typeof action !== 'number' || action < 0 || action > 2) {
        throw new functions.https.HttpsError('invalid-argument', 'Invalid action');
    }

    const gameRef = db.ref(`games/${gameId}`);

    const result = await gameRef.transaction((game) => {
        if (!game) return;
        if (game.status !== 'PLAYING') return;

        const isP1 = game.p1_uid === context.auth.uid;
        const isP2 = game.p2_uid === context.auth.uid;

        if (!isP1 && !isP2) {
            return; // Not a player in this game
        }

        // Validate action
        if (action === 2) { // SHOOT
            const bullets = isP1 ? game.p1_bullets : game.p2_bullets;
            if (bullets === 0) {
                return; // Can't shoot with no bullets
            }
        }

        // Record action
        if (isP1) {
            if (game.p1_action !== null) return; // Already submitted
            game.p1_action = action;
        } else {
            if (game.p2_action !== null) return; // Already submitted
            game.p2_action = action;
        }

        // Check if both actions are in - resolve round
        if (game.p1_action !== null && game.p2_action !== null) {
            const winner = calcWinner(game.p1_action, game.p1_bullets, game.p2_action, game.p2_bullets);

            // Update bullets based on actions
            game.p1_bullets = calculateNewBullets(game.p1_action, game.p1_bullets);
            game.p2_bullets = calculateNewBullets(game.p2_action, game.p2_bullets);

            // Store last round result for client display
            game.last_round = {
                round: game.round,
                p1_action: game.p1_action,
                p2_action: game.p2_action,
                winner: winner
            };

            // Check for game end
            if (winner === 1) {
                game.status = 'FINISHED';
                game.winner = game.p1;
                game.winner_uid = game.p1_uid;
            } else if (winner === 2) {
                game.status = 'FINISHED';
                game.winner = game.p2;
                game.winner_uid = game.p2_uid;
            } else if (game.round >= 12) {
                // High noon reached, no winner
                game.status = 'FINISHED';
                game.winner = 'draw';
                game.winner_uid = null;
            } else {
                // Next round
                game.round += 1;
                game.p1_action = null;
                game.p2_action = null;
            }
        }

        return game;
    });

    if (!result.committed) {
        throw new functions.https.HttpsError('failed-precondition', 'Could not submit action');
    }

    return { success: true };
});

/**
 * Get list of open games
 */
exports.getOpenGames = functions.https.onCall(async (data, context) => {
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const snapshot = await db.ref('games')
        .orderByChild('status')
        .equalTo('WAITING')
        .limitToFirst(20)
        .once('value');

    const games = [];
    snapshot.forEach((child) => {
        const game = child.val();
        // Don't show own games
        if (game.p1_uid !== context.auth.uid) {
            games.push({
                id: game.id,
                p1: game.p1,
                bet: game.bet
            });
        }
    });

    return { games };
});

/**
 * Leave/abandon a game (only if waiting)
 */
exports.leaveGame = functions.https.onCall(async (data, context) => {
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const { gameId } = data;
    const gameRef = db.ref(`games/${gameId}`);

    const result = await gameRef.transaction((game) => {
        if (!game) return;

        // Only creator can delete waiting games
        if (game.status === 'WAITING' && game.p1_uid === context.auth.uid) {
            return null; // Delete the game
        }

        return; // Don't modify
    });

    return { success: result.committed };
});

// ============================================================================
// CLEANUP FUNCTION (scheduled)
// ============================================================================

/**
 * Clean up stale games older than 24 hours
 */
exports.cleanupStaleGames = functions.pubsub.schedule('every 24 hours').onRun(async (context) => {
    const cutoff = Date.now() - (24 * 60 * 60 * 1000); // 24 hours ago

    const snapshot = await db.ref('games').once('value');
    const updates = {};

    snapshot.forEach((child) => {
        const game = child.val();
        if (game.created && game.created < cutoff) {
            updates[child.key] = null; // Mark for deletion
        }
    });

    if (Object.keys(updates).length > 0) {
        await db.ref('games').update(updates);
        console.log(`Cleaned up ${Object.keys(updates).length} stale games`);
    }

    return null;
});
