"""Initial schema migration - consolidates existing SQL migrations

Revision ID: 20250920_001
Revises: 
Create Date: 2025-09-20 12:30:00.000000

This migration consolidates the existing SQL migrations:
- 001_create_jwt_blacklist.sql
- 002_enable_rls_security.sql

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250920_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the consolidated schema changes."""
    
    # Create JWT blacklist table (from 001_create_jwt_blacklist.sql)
    op.execute("""
        CREATE TABLE IF NOT EXISTS jwt_blacklist (
            id SERIAL PRIMARY KEY,
            token_jti VARCHAR(255) UNIQUE NOT NULL,
            user_id INTEGER,
            blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            reason VARCHAR(255) DEFAULT 'logout'
        );
        
        CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_token_jti ON jwt_blacklist(token_jti);
        CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);
    """)
    
    # Enable RLS and create security policies (from 002_enable_rls_security.sql)
    op.execute("""
        -- Enable RLS on critical tables
        ALTER TABLE IF EXISTS "user" ENABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS audit_log ENABLE ROW LEVEL SECURITY;
        ALTER TABLE jwt_blacklist ENABLE ROW LEVEL SECURITY;
        
        -- Create security helper functions
        CREATE OR REPLACE FUNCTION is_admin()
        RETURNS BOOLEAN AS $$
        BEGIN
            RETURN current_setting('request.jwt.claims', true)::json->>'role' = 'admin'
                OR auth.role() = 'service_role';
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        CREATE OR REPLACE FUNCTION log_security_event(event_type TEXT, details JSONB DEFAULT '{}')
        RETURNS VOID AS $$
        BEGIN
            INSERT INTO audit_log (user_id, action, resource, details, created_at)
            VALUES (
                COALESCE((current_setting('request.jwt.claims', true)::json->>'sub')::INTEGER, 0),
                event_type,
                'security',
                details,
                NOW()
            );
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        
        -- User table policies
        DROP POLICY IF EXISTS "Users can view own data" ON "user";
        CREATE POLICY "Users can view own data" ON "user"
            FOR SELECT USING (
                auth.uid()::text = id::text OR is_admin()
            );
        
        DROP POLICY IF EXISTS "Users can update own data" ON "user";
        CREATE POLICY "Users can update own data" ON "user"
            FOR UPDATE USING (
                auth.uid()::text = id::text OR is_admin()
            );
        
        DROP POLICY IF EXISTS "Admins can insert users" ON "user";
        CREATE POLICY "Admins can insert users" ON "user"
            FOR INSERT WITH CHECK (is_admin());
        
        -- Audit log policies
        DROP POLICY IF EXISTS "Users can view own audit logs" ON audit_log;
        CREATE POLICY "Users can view own audit logs" ON audit_log
            FOR SELECT USING (
                user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::INTEGER
                OR is_admin()
            );
        
        DROP POLICY IF EXISTS "System can insert audit logs" ON audit_log;
        CREATE POLICY "System can insert audit logs" ON audit_log
            FOR INSERT WITH CHECK (true);
        
        -- JWT blacklist policies
        DROP POLICY IF EXISTS "Users can view own blacklisted tokens" ON jwt_blacklist;
        CREATE POLICY "Users can view own blacklisted tokens" ON jwt_blacklist
            FOR SELECT USING (
                user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::INTEGER
                OR is_admin()
            );
        
        DROP POLICY IF EXISTS "Users can blacklist own tokens" ON jwt_blacklist;
        CREATE POLICY "Users can blacklist own tokens" ON jwt_blacklist
            FOR INSERT WITH CHECK (
                user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::INTEGER
                OR is_admin()
            );
        
        -- Grant necessary permissions
        GRANT SELECT, INSERT ON jwt_blacklist TO authenticated;
        GRANT SELECT ON audit_log TO authenticated;
        GRANT ALL ON jwt_blacklist TO service_role;
        GRANT ALL ON audit_log TO service_role;
        GRANT ALL ON "user" TO service_role;
    """)


def downgrade() -> None:
    """Revert the schema changes."""
    
    # Drop RLS policies and functions
    op.execute("""
        -- Drop policies
        DROP POLICY IF EXISTS "Users can view own data" ON "user";
        DROP POLICY IF EXISTS "Users can update own data" ON "user";
        DROP POLICY IF EXISTS "Admins can insert users" ON "user";
        DROP POLICY IF EXISTS "Users can view own audit logs" ON audit_log;
        DROP POLICY IF EXISTS "System can insert audit logs" ON audit_log;
        DROP POLICY IF EXISTS "Users can view own blacklisted tokens" ON jwt_blacklist;
        DROP POLICY IF EXISTS "Users can blacklist own tokens" ON jwt_blacklist;
        
        -- Disable RLS
        ALTER TABLE IF EXISTS "user" DISABLE ROW LEVEL SECURITY;
        ALTER TABLE IF EXISTS audit_log DISABLE ROW LEVEL SECURITY;
        ALTER TABLE jwt_blacklist DISABLE ROW LEVEL SECURITY;
        
        -- Drop helper functions
        DROP FUNCTION IF EXISTS is_admin();
        DROP FUNCTION IF EXISTS log_security_event(TEXT, JSONB);
    """)
    
    # Drop JWT blacklist table
    op.execute("""
        DROP TABLE IF EXISTS jwt_blacklist;
    """)
