PRAGMA foreign_keys = ON;
CREATE TABLE generations (id TEXT PRIMARY KEY, created_at INTEGER NOT NULL);
CREATE TABLE site_state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE threads (
    generation TEXT NOT NULL REFERENCES generations(id) ON DELETE CASCADE,
    id TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL,
    PRIMARY KEY (generation, id)
);
CREATE TABLE comments (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL UNIQUE,
    thread_id TEXT NOT NULL,
    parent_id TEXT REFERENCES comments(id) ON DELETE CASCADE,
    author TEXT NOT NULL CHECK(length(author) BETWEEN 2 AND 60),
    body TEXT NOT NULL CHECK(length(body) BETWEEN 3 AND 2000),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','hidden')),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX comments_public ON comments(thread_id, status, seq);
CREATE INDEX comments_moderation ON comments(status, seq);
CREATE INDEX comments_parent ON comments(parent_id);
CREATE TABLE rate_limits (key TEXT PRIMARY KEY, hits INTEGER NOT NULL, expires_at INTEGER NOT NULL);
CREATE INDEX rate_limits_expiry ON rate_limits(expires_at);
