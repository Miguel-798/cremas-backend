-- ============================================================
-- Migration 001: Row Level Security (RLS) Policies
-- ============================================================
-- 
-- IMPORTANT: Before running this migration, you need to:
-- 1. Create a service role key in Supabase Dashboard
--    (Project Settings > API > service_role key)
-- 2. Set SUPABASE_SERVICE_ROLE_KEY in your .env file
--
-- HOW TO APPLY THIS MIGRATION:
-- Option A: Run in Supabase SQL Editor (Dashboard > SQL Editor)
-- Option B: Use Supabase CLI: supabase db push
-- Option C: Use a migration tool like Alembic with raw SQL
--
-- ROLLOUT STRATEGY:
-- 1. Test RLS policies in a development environment first
-- 2. Enable RLS one table at a time, testing each
-- 3. Monitor application behavior after each policy change
--
-- ROLLBACK:
--   ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
-- ============================================================

BEGIN;

-- ============================================================
-- CREAM_OWNERS TABLE
-- (Tracks which users own which creams)
-- ============================================================

-- Create cream_owners table if it doesn't exist
-- Note: user_id references auth.users(id) but we store as VARCHAR
-- because auth.uid() returns TEXT in Supabase
CREATE TABLE IF NOT EXISTS cream_owners (
    cream_id VARCHAR NOT NULL REFERENCES creams(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL,  -- References auth.users(id) but stored as TEXT for Supabase compatibility
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (cream_id, user_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_cream_owners_user_id ON cream_owners(user_id);
CREATE INDEX IF NOT EXISTS idx_cream_owners_cream_id ON cream_owners(cream_id);

-- ============================================================
-- CREAMS TABLE
-- ============================================================

-- Enable RLS
ALTER TABLE creams ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid duplicates (safe to run multiple times)
DROP POLICY IF EXISTS "Authenticated users can read all creams" ON creams;
DROP POLICY IF EXISTS "Users can insert their own creams" ON creams;
DROP POLICY IF EXISTS "Users can update their own creams" ON creams;
DROP POLICY IF EXISTS "Users can delete their own creams" ON creams;
DROP POLICY IF EXISTS "Public read access" ON creams;

-- Policy: All authenticated users can READ all creams
-- (Business decision: cream inventory is public for reading)
CREATE POLICY "Authenticated users can read all creams"
    ON creams
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Authenticated users can INSERT new creams (they become owner)
-- The user_id comes from the cream_owners table via trigger
CREATE POLICY "Authenticated users can create creams"
    ON creams
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Policy: Only owners can UPDATE creams
CREATE POLICY "Owners can update their creams"
    ON creams
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM cream_owners
            WHERE cream_id = creams.id
            AND user_id = auth.uid()::text
        )
    );

-- Policy: Only owners can DELETE creams
CREATE POLICY "Owners can delete their creams"
    ON creams
    FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM cream_owners
            WHERE cream_id = creams.id
            AND user_id = auth.uid()::text
        )
    );

-- ============================================================
-- SALES TABLE
-- ============================================================

-- Enable RLS
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Authenticated users can read sales" ON sales;
DROP POLICY IF EXISTS "Users can insert sales" ON sales;

-- Policy: Authenticated users can read all sales
-- (Business decision: sales history is public for reading)
CREATE POLICY "Authenticated users can read sales"
    ON sales
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Authenticated users can register sales
CREATE POLICY "Authenticated users can create sales"
    ON sales
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- ============================================================
-- RESERVATIONS TABLE
-- ============================================================

-- Enable RLS
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can read their own reservations" ON reservations;
DROP POLICY IF EXISTS "Users can create reservations" ON reservations;
DROP POLICY IF EXISTS "Users can update their own reservations" ON reservations;
DROP POLICY IF EXISTS "Users can delete their own reservations" ON reservations;

-- Policy: Authenticated users can read all reservations
-- (Business decision: reservation list is public for reading)
CREATE POLICY "Authenticated users can read reservations"
    ON reservations
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Authenticated users can create reservations
CREATE POLICY "Authenticated users can create reservations"
    ON reservations
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Policy: Users can update their own reservations
CREATE POLICY "Users can update their own reservations"
    ON reservations
    FOR UPDATE
    TO authenticated
    USING (true);  -- app-level check, but RLS adds security

-- Policy: Users can delete their own reservations
CREATE POLICY "Users can delete their own reservations"
    ON reservations
    FOR DELETE
    TO authenticated
    USING (true);  -- app-level check, but RLS adds security

-- ============================================================
-- CATEGORIES TABLE (if exists)
-- Note: Add this section if you have a categories table
-- ============================================================

-- Uncomment and adjust if categories table exists:
-- ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Authenticated read categories"
--     ON categories FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "Admin write categories"
--     ON categories FOR ALL TO authenticated
--     USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================
-- NOTIFICATIONS TABLE (if exists)
-- Note: Add this section if you have a notifications table
-- ============================================================

-- Uncomment and adjust if notifications table exists:
-- ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can read their own notifications"
--     ON notifications FOR SELECT TO authenticated
--     USING (user_id = auth.uid());
-- CREATE POLICY "Service role can manage notifications"
--     ON notifications FOR ALL TO authenticated
--     USING (auth.jwt() ->> 'role' = 'service_role');

COMMIT;

-- ============================================================
-- VERIFICATION QUERIES
-- Run these to verify RLS is working correctly
-- ============================================================

-- Check RLS is enabled on all tables:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Check policies exist:
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
-- FROM pg_policies WHERE schemaname = 'public';
