-- G1-02 / ADR-018：source_activation_overlay（对齐 data_sources.md §5.2.1）
-- 问开关持久化；有效启用另由安检层合成，本表只承载管理员覆盖层。

CREATE TABLE IF NOT EXISTS source_activation_overlay (
    overlay_id          VARCHAR PRIMARY KEY,
    source_id           VARCHAR NOT NULL,
    data_domain         VARCHAR NOT NULL,
    operation           VARCHAR NOT NULL,
    enabled             BOOLEAN NOT NULL,
    reason              TEXT NOT NULL,
    changed_by          VARCHAR NOT NULL,
    changed_at          TIMESTAMP NOT NULL,
    revision            VARCHAR NOT NULL,
    revoked_at          TIMESTAMP,
    revoked_by          VARCHAR,
    revoke_reason       TEXT
);
