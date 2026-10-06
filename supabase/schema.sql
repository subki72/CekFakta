-- ============================================
-- AI Fake News Detection — Supabase Schema
-- Jalankan SQL ini di Supabase SQL Editor
-- ============================================

-- 1. Enable UUID extension (biasanya sudah enabled di Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Tabel Users (diisi otomatis saat login via Google OAuth)
-- Catatan: Supabase Auth sudah punya tabel auth.users bawaan.
-- Tabel ini adalah tabel profil tambahan di schema public.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id UUID UNIQUE NOT NULL,  -- referensi ke auth.users.id dari Supabase Auth
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabel Analyses (hasil analisis objektivitas)
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL jika guest
    input_type TEXT NOT NULL CHECK (input_type IN ('TEXT', 'URL', 'IMAGE')),
    raw_input TEXT NOT NULL,
    extracted_text TEXT NOT NULL,
    detected_language TEXT DEFAULT 'id',  -- 'id' atau 'en'
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    label TEXT NOT NULL CHECK (label IN ('OBJEKTIF', 'CENDERUNG_BIAS', 'SANGAT_MANIPULATIF')),
    reasoning TEXT NOT NULL,
    highlighted_issues JSONB DEFAULT '[]'::jsonb,
    buzzer_indicators JSONB DEFAULT '[]'::jsonb,
    ip_hash TEXT,  -- Hash dari IP address (untuk rate limiting & privasi)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_label ON analyses(label);

-- 4. Tabel Crawled Articles (artikel dari portal berita yang dicrawl otomatis)
CREATE TABLE IF NOT EXISTS crawled_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_portal TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content_text TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    label TEXT NOT NULL CHECK (label IN ('OBJEKTIF', 'CENDERUNG_BIAS', 'SANGAT_MANIPULATIF')),
    reasoning TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crawled_articles_created_at ON crawled_articles(created_at DESC);
CREATE INDEX idx_crawled_articles_source ON crawled_articles(source_portal);

-- 5. Tabel Votes (upvote/downvote komunitas)
CREATE TABLE IF NOT EXISTS votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_agree BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(analysis_id, user_id)  -- 1 user hanya boleh vote 1x per analisis
);

CREATE INDEX idx_votes_analysis_id ON votes(analysis_id);

-- 6. Tabel Comments (komentar komunitas)
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comments_analysis_id ON comments(analysis_id);

-- 7. Tabel Audit Logs (pencatatan aktivitas sistem untuk keamanan)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- Bisa NULL untuk aksi anonim/guest
    ip_hash TEXT,
    action_type TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_action ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================
-- 8. Row Level Security (RLS) Policies
-- ============================================

-- Enable RLS on all public tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawled_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- 8.1 Users policies
-- Anyone can read basic user profile info (needed to display comment authors)
CREATE POLICY "Public users read" ON users
    FOR SELECT USING (true);

-- Authenticated users can insert their own profile
CREATE POLICY "Users insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = auth_id);

-- Authenticated users can update their own profile
CREATE POLICY "Users update own profile" ON users
    FOR UPDATE USING (auth.uid() = auth_id) WITH CHECK (auth.uid() = auth_id);

-- 8.2 Analyses policies
-- Anyone can view public analyses
CREATE POLICY "Public analyses read" ON analyses
    FOR SELECT USING (true);

-- Authenticated users can delete their own analyses
CREATE POLICY "Users delete own analyses" ON analyses
    FOR DELETE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 8.3 Crawled articles policies
-- Anyone can view crawled articles
CREATE POLICY "Public crawled_articles read" ON crawled_articles
    FOR SELECT USING (true);

-- 8.4 Votes policies
-- Anyone can view vote counts and entries
CREATE POLICY "Public votes read" ON votes
    FOR SELECT USING (true);

-- Authenticated users can insert votes for themselves
CREATE POLICY "Auth users insert votes" ON votes
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- Authenticated users can update their own vote
CREATE POLICY "Auth users update votes" ON votes
    FOR UPDATE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()))
    WITH CHECK (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- Authenticated users can delete their own vote
CREATE POLICY "Auth users delete votes" ON votes
    FOR DELETE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 8.5 Comments policies
-- Anyone can view comments
CREATE POLICY "Public comments read" ON comments
    FOR SELECT USING (true);

-- Authenticated users can insert comments for themselves
CREATE POLICY "Auth users insert comments" ON comments
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- Authenticated users can delete their own comments
CREATE POLICY "Auth users delete comments" ON comments
    FOR DELETE USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 8.6 Audit logs policies
-- Authenticated users can only view their own audit logs
CREATE POLICY "Users view own audit logs" ON audit_logs
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth_id = auth.uid()));

-- 8.7 Column-level privacy grant
-- Prevent anonymous harvesting of user email addresses while allowing public comment author display
REVOKE SELECT ON users FROM anon;
GRANT SELECT (id, name, created_at) ON users TO anon;
GRANT SELECT (id, name, created_at, auth_id) ON users TO authenticated;

-- Prevent public harvesting of user IP hashes while allowing reading analysis results (Critical Security Audit)
REVOKE SELECT ON analyses FROM anon;
GRANT SELECT (id, user_id, input_type, raw_input, extracted_text, detected_language, score, label, reasoning, highlighted_issues, buzzer_indicators, created_at) ON analyses TO anon, authenticated;

-- Note: All backend service_role operations automatically bypass RLS.

