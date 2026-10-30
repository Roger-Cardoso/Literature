-- Preserva mensagens existentes e separa a escolha enviada da classificação da moderação.
ALTER TABLE comments ADD COLUMN spoiler INTEGER NOT NULL DEFAULT 0 CHECK(spoiler IN (0,1));
ALTER TABLE comments ADD COLUMN submitted_spoiler INTEGER NOT NULL DEFAULT 0 CHECK(submitted_spoiler IN (0,1));
