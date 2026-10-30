-- Mantém as discussões e os comentários existentes. Reações antigas começam desativadas.
ALTER TABLE threads ADD COLUMN comments_enabled INTEGER NOT NULL DEFAULT 1 CHECK(comments_enabled IN (0,1));
ALTER TABLE threads ADD COLUMN reactions_enabled INTEGER NOT NULL DEFAULT 0 CHECK(reactions_enabled IN (0,1));
CREATE TABLE reactions (
 thread_id TEXT NOT NULL, voter_hash TEXT NOT NULL,
 value INTEGER NOT NULL CHECK(value IN (-1,1)), updated_at INTEGER NOT NULL,
 PRIMARY KEY(thread_id,voter_hash)
);
CREATE TABLE reaction_totals (
 thread_id TEXT PRIMARY KEY, likes INTEGER NOT NULL DEFAULT 0 CHECK(likes>=0),
 dislikes INTEGER NOT NULL DEFAULT 0 CHECK(dislikes>=0)
);
CREATE TABLE reaction_controls (thread_id TEXT PRIMARY KEY,paused INTEGER NOT NULL CHECK(paused IN (0,1)));
CREATE TABLE reaction_verifications (
 voter_hash TEXT NOT NULL, network_hash TEXT NOT NULL, expires_at INTEGER NOT NULL,
 PRIMARY KEY(voter_hash,network_hash)
);
CREATE INDEX reaction_verifications_expiry ON reaction_verifications(expires_at);
CREATE TRIGGER reaction_insert AFTER INSERT ON reactions BEGIN
 INSERT INTO reaction_totals(thread_id,likes,dislikes) VALUES (NEW.thread_id,NEW.value=1,NEW.value=-1)
 ON CONFLICT(thread_id) DO UPDATE SET likes=likes+(NEW.value=1),dislikes=dislikes+(NEW.value=-1);
END;
CREATE TRIGGER reaction_update AFTER UPDATE OF value ON reactions WHEN OLD.value!=NEW.value BEGIN
 UPDATE reaction_totals SET likes=likes-(OLD.value=1)+(NEW.value=1),dislikes=dislikes-(OLD.value=-1)+(NEW.value=-1) WHERE thread_id=NEW.thread_id;
END;
CREATE TRIGGER reaction_delete AFTER DELETE ON reactions BEGIN
 UPDATE reaction_totals SET likes=likes-(OLD.value=1),dislikes=dislikes-(OLD.value=-1) WHERE thread_id=OLD.thread_id;
END;
