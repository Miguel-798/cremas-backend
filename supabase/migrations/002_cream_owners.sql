-- ============================================================
-- Migration 002: Cream Owners Table
-- ============================================================
-- 
-- This table tracks which users own which creams.
-- It's used by RLS policies to enforce ownership-based access.
--
-- HOW TO APPLY:
-- Run this AFTER 001_rls_policies.sql
-- ============================================================

BEGIN;

-- ============================================================
-- CREAM_OWNERS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS cream_owners (
    cream_id VARCHAR NOT NULL REFERENCES creams(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL,  -- References auth.users(id) but stored as TEXT for Supabase compatibility
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (cream_id, user_id),
    
    -- Ensure each user can only have one ownership record per cream
    CONSTRAINT unique_cream_ownership UNIQUE (cream_id, user_id)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_cream_owners_user_id ON cream_owners(user_id);
CREATE INDEX IF NOT EXISTS idx_cream_owners_cream_id ON cream_owners(cream_id);

-- ============================================================
-- AUTO-ASSIGN OWNERSHIP TRIGGER
-- ============================================================
-- When a new cream is created, automatically assign ownership
-- to the user who created it (from JWT token).

CREATE OR REPLACE FUNCTION assign_cream_ownership()
RETURNS TRIGGER AS $$
BEGIN
    -- Get the user ID from the JWT token
    -- Note: In the actual INSERT, you need to pass user_id
    -- This trigger is for reference - actual implementation
    -- should be done at the application layer
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Note: The actual ownership assignment should happen in the
-- application layer when creating a cream, since we need to
-- insert into cream_owners alongside the cream INSERT.

-- ============================================================
-- GRANT PERMISSIONS
-- ============================================================

-- Grant full access to authenticated users and service_role
GRANT ALL ON cream_owners TO authenticated;
GRANT ALL ON cream_owners TO service_role;

-- Grant on sequences if needed
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

COMMIT;

-- ============================================================
-- SERVICE ROLE KEY SETUP INSTRUCTIONS
-- ============================================================
-- 
-- To set up the service role key:
--
-- 1. Go to Supabase Dashboard: https://app.supabase.com
-- 2. Select your project
-- 3. Go to: Project Settings > API
-- 4. Under "Service Role Key", copy the key
-- 5. Add it to your .env file:
--    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
--
-- IMPORTANT: Never commit the service role key to version control.
-- The .env file is already in .gitignore.
--
-- The service role key bypasses RLS and should ONLY be used for:
-- - Server-side admin operations
-- - Background jobs
-- - Operations that legitimately need elevated privileges
-- ============================================================
