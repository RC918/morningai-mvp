-- Migration: Create JWT Blacklist table
-- Version: 001
-- Description: Add JWT blacklist functionality for token revocation
-- Author: System
-- Date: 2025-09-18

-- Create jwt_blacklist table
CREATE TABLE IF NOT EXISTS jwt_blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jti VARCHAR(36) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    token_type VARCHAR(20) NOT NULL DEFAULT 'access',
    expires_at DATETIME NOT NULL,
    blacklisted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_jti ON jwt_blacklist(jti);
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_user_id ON jwt_blacklist(user_id);

-- Insert initial data or configuration if needed
-- (None required for this migration)

-- Migration complete
-- This migration adds JWT blacklist functionality to support:
-- 1. Token revocation on logout
-- 2. Security-based token invalidation
-- 3. Cleanup of expired blacklisted tokens
-- 4. Admin management of blacklisted tokens

