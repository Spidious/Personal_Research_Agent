-- Initial schema — matches §4 of the architecture doc exactly.
-- Generic from day one: no topic-specific tables.

CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS topics (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sources (
    id              BIGSERIAL PRIMARY KEY,
    topic_id        BIGINT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    type            VARCHAR(20) NOT NULL CHECK (type IN ('rss','youtube','reddit','html')),
    url             TEXT NOT NULL,
    name            VARCHAR(255) NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    last_fetched_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS items (
    id           BIGSERIAL PRIMARY KEY,
    source_id    BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    external_id  TEXT NOT NULL,
    url          TEXT NOT NULL,
    title        TEXT NOT NULL DEFAULT '',
    content      TEXT NOT NULL DEFAULT '',
    published_at TIMESTAMPTZ,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_id, external_id)
);

CREATE TABLE IF NOT EXISTS briefings (
    id               BIGSERIAL PRIMARY KEY,
    topic_id         BIGINT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    sent_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    item_count       INTEGER NOT NULL DEFAULT 0,
    model_used       VARCHAR(100) NOT NULL DEFAULT '',
    total_cost_cents INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS briefing_items (
    briefing_id BIGINT NOT NULL REFERENCES briefings(id) ON DELETE CASCADE,
    item_id     BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    rank        INTEGER NOT NULL,
    summary     TEXT NOT NULL DEFAULT '',
    reasoning   TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (briefing_id, item_id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    briefing_id  BIGINT NOT NULL,
    item_id      BIGINT NOT NULL,
    signal       VARCHAR(20) NOT NULL CHECK (signal IN ('more_like_this','less_like_this','not_interested','saved')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (briefing_id, item_id) REFERENCES briefing_items(briefing_id, item_id) ON DELETE CASCADE
);

-- Observability: every LLM call logged here from day one (§8)
CREATE TABLE IF NOT EXISTS llm_logs (
    id               BIGSERIAL PRIMARY KEY,
    called_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calling_function VARCHAR(255) NOT NULL DEFAULT '',
    model            VARCHAR(100) NOT NULL,
    input_tokens     INTEGER NOT NULL DEFAULT 0,
    output_tokens    INTEGER NOT NULL DEFAULT 0,
    cost_cents       INTEGER NOT NULL DEFAULT 0,
    latency_ms       INTEGER NOT NULL DEFAULT 0,
    prompt           TEXT NOT NULL DEFAULT '',
    response         TEXT NOT NULL DEFAULT '',
    error            TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_source_id     ON items(source_id);
CREATE INDEX IF NOT EXISTS idx_topics_user_id      ON topics(user_id);
CREATE INDEX IF NOT EXISTS idx_briefings_topic_id  ON briefings(topic_id);
CREATE INDEX IF NOT EXISTS idx_llm_logs_called_at  ON llm_logs(called_at);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id    ON feedback(user_id);
