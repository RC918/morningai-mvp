# JWT Blacklist Feature Rollback Guide

## Overview
This guide provides instructions for rolling back the JWT Blacklist feature if issues arise in production.

## Rollback Steps

### 1. Database Rollback

#### Option A: Drop the blacklist table (Complete removal)
```sql
-- Remove indexes first
DROP INDEX IF EXISTS idx_jwt_blacklist_jti;
DROP INDEX IF EXISTS idx_jwt_blacklist_expires_at;
DROP INDEX IF EXISTS idx_jwt_blacklist_user_id;

-- Drop the table
DROP TABLE IF EXISTS jwt_blacklist;
```

#### Option B: Disable blacklist checking (Preserve data)
```sql
-- Rename table to disable without data loss
ALTER TABLE jwt_blacklist RENAME TO jwt_blacklist_disabled;
```

### 2. Code Rollback

#### Files to revert:
1. `src/models/jwt_blacklist.py` - Remove file
2. `src/routes/jwt_blacklist.py` - Remove file
3. `src/decorators.py` - Remove blacklist checking from token_required
4. `src/routes/auth.py` - Remove JTI from JWT payload
5. `src/main.py` - Remove blacklist imports and blueprint registration

#### Specific code changes to revert:

**src/decorators.py:**
```python
# Remove these lines from token_required function:
# Check JWT blacklist
jti = payload.get('jti')
if jti:
    from src.models.jwt_blacklist import JWTBlacklist
    if JWTBlacklist.is_blacklisted(jti):
        return jsonify({'error': 'Token has been revoked'}), 401
```

**src/routes/auth.py:**
```python
# Remove JTI from JWT payload in login function:
payload = {
    "user_id": user.id,
    "sub": user.id,
    "username": user.username,
    "role": user.role,
    # Remove this line: "jti": jti,
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
}
```

**src/main.py:**
```python
# Remove these imports:
from src.models.jwt_blacklist import JWTBlacklist
from src.routes.jwt_blacklist import jwt_blacklist_bp

# Remove this blueprint registration:
app.register_blueprint(jwt_blacklist_bp, url_prefix="/api")
```

### 3. Environment Variables
No environment variables need to be removed for this rollback.

### 4. Testing After Rollback

#### Verify the rollback:
```bash
# Test login still works
curl -X POST $API_URL/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@morningai.com","password":"admin123"}'

# Test that JWT tokens work normally
TOKEN="<token_from_login>"
curl -H "Authorization: Bearer $TOKEN" $API_URL/api/admin/users

# Verify blacklist endpoints are gone (should return 404)
curl -X POST -H "Authorization: Bearer $TOKEN" $API_URL/api/auth/logout
curl -H "Authorization: Bearer $TOKEN" $API_URL/api/admin/blacklist
```

### 5. Monitoring After Rollback

Monitor the following after rollback:
- Login functionality
- JWT token validation
- Protected endpoint access
- No 500 errors related to missing blacklist functionality

## Recovery (Re-enable)

If you need to re-enable the feature:

1. Restore the database table:
```sql
-- If you used Option B above
ALTER TABLE jwt_blacklist_disabled RENAME TO jwt_blacklist;

-- If you used Option A, re-run the migration
-- Run migrations/001_create_jwt_blacklist.sql
```

2. Restore the code files from this commit
3. Restart the application

## Emergency Contacts

- Development Team: [Contact Information]
- DevOps Team: [Contact Information]
- On-call Engineer: [Contact Information]

## Notes

- This rollback removes JWT revocation capability
- Users will need to wait for natural token expiration
- Consider the security implications before rolling back
- Test thoroughly in staging before applying to production

