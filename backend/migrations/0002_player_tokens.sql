-- Keep existing logins working while allowing an operator to issue a recovery
-- code or reconnect a replacement browser to the same player and solve history.
CREATE TABLE player_tokens (
    token_hash TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX player_tokens_player_id ON player_tokens(player_id);

INSERT INTO player_tokens(token_hash, player_id)
SELECT token_hash, id FROM players;
