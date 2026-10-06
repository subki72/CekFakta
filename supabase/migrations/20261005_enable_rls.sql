-- Migration: Enable Row Level Security (RLS) and create security policies
-- Date: 2026-10-05

-- 1. Ensure required schema columns exist
ALTER TABLE IF EXISTS analyses ADD COLUMN IF NOT EXISTS highlighted_issues JSONB DEFAULT '[]'::jsonb;

-- 2. Enable RLS on all tables
ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS crawled_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;

-- 3. Drop existing policies if they already exist (idempotency)
DROP POLICY IF EXISTS "Public users read" ON users;
DROP POLICY IF EXISTS "Users insert own profile" ON users;
DROP POLICY IF EXISTS "Users update own profile" ON users;
DROP POLICY IF EXISTS "Public analyses read" ON analyses;
DROP POLICY IF EXISTS "Users delete own analyses" ON analyses;
DROP POLICY IF EXISTS "Public crawled_articles read" ON crawled_articles;
DROP POLICY IF EXISTS "Public votes read" ON votes;
DROP POLICY IF EXISTS "Auth users insert votes" ON votes;
DROP POLICY IF EXISTS "Auth users update votes" ON votes;
DROP POLICY IF EXISTS "Auth users delete votes" ON votes;
DROP POLICY IF EXISTS "Public comments read" ON comments;
DROP POLICY IF EXISTS "Auth users insert comments" ON comments;
DROP POLICY IF EXISTS "Auth users delete comments" ON comments;
DROP POLICY IF EXISTS "Users view own audit logs" ON audit_logs;

-- 3. Users policies
CREATE POLICY "Public users read" ON users
    FOR SELECT USING (true);

CREATE POLICY "Users insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = auth_id);

CREATE POLICY "Users update own profile" ON users
    FOR UPDATE USING (auth.uid() = auth_id) WITH CHECK (auth.uid() = auth_id);

-- 4. Analyses policies
CREATE POLICY "Public analyses read" ON analyses
    FOR SELECT USING (true);

CREATE POLICY "Users delete own analyses" ON analyses
    FOR DELETE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 5. Crawled articles policies
CREATE POLICY "Public crawled_articles read" ON crawled_articles
    FOR SELECT USING (true);

-- 6. Votes policies
CREATE POLICY "Public votes read" ON votes
    FOR SELECT USING (true);

CREATE POLICY "Auth users insert votes" ON votes
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY "Auth users update votes" ON votes
    FOR UPDATE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()))
    WITH CHECK (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY "Auth users delete votes" ON votes
    FOR DELETE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 7. Comments policies
CREATE POLICY "Public comments read" ON comments
    FOR SELECT USING (true);

CREATE POLICY "Auth users insert comments" ON comments
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

CREATE POLICY "Auth users delete comments" ON comments
    FOR DELETE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 8. Audit logs policies
CREATE POLICY "Users view own audit logs" ON audit_logs
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 9. Column-level privacy grant
REVOKE SELECT ON users FROM anon;
GRANT SELECT (id, name, created_at) ON users TO anon;
GRANT SELECT (id, name, created_at, auth_id) ON users TO authenticated;

-- Prevent public harvesting of user IP hashes while allowing reading analysis results (Critical Security Audit)
REVOKE SELECT ON analyses FROM anon;
GRANT SELECT (id, user_id, input_type, raw_input, extracted_text, detected_language, score, label, reasoning, highlighted_issues, buzzer_indicators, created_at) ON analyses TO anon, authenticated;

