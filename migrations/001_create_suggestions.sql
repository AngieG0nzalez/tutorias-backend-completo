-- Migración 001: buzón de sugerencias. Idempotente y no destructiva.
-- Solo crea la tabla `suggestions` (no toca las demás tablas).
-- users.id es BIGINT en el modelo (PK de `users`); verifica antes de aplicar.

BEGIN;

CREATE TABLE IF NOT EXISTS suggestions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category    VARCHAR(20)  NOT NULL
                CHECK (category IN ('content', 'usability', 'bug', 'other')),
    subject     VARCHAR(150) NOT NULL,
    message     TEXT         NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'new'
                CHECK (status IN ('new', 'in_review', 'resolved', 'rejected')),
    admin_note  TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_suggestions_user_created
    ON suggestions (user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_suggestions_status_created
    ON suggestions (status, created_at);

COMMIT;
