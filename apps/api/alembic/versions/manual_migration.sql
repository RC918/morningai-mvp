-- 手動遷移腳本：新增 JWT 黑名單和審計日誌功能

-- 升級腳本
CREATE TABLE jwt_blacklist (
    id INTEGER NOT NULL,
    jti VARCHAR(36) NOT NULL,
    user_id INTEGER NOT NULL,
    revoked_at DATETIME NOT NULL,
    reason VARCHAR(255),
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_jwt_blacklist_jti ON jwt_blacklist (jti);

CREATE TABLE audit_logs (
    id INTEGER NOT NULL,
    user_id INTEGER,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255),
    resource_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    status VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

-- 新增 RLS 政策
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can view all audit logs" ON audit_logs FOR SELECT TO authenticated USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);

CREATE POLICY "Users can view own audit logs" ON audit_logs FOR SELECT TO authenticated USING (
    user_id = auth.uid()
);

CREATE POLICY "Service role can insert audit logs" ON audit_logs FOR INSERT TO service_role WITH CHECK (true);

-- 降級腳本
DROP TABLE audit_logs;
DROP TABLE jwt_blacklist;

