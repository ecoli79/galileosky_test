CREATE TABLE IF NOT EXISTS query_logs (id BIGSERIAL PRIMARY KEY, level TEXT, message TEXT, query TEXT, params JSONB, error TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
