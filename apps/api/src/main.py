
import os
from flask import Flask, request, jsonify
import requests # For Upstash Redis REST API
from dotenv import load_dotenv
from models import db, User, Tenant
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from src.auth import hash_password, verify_password, create_tokens, authenticate_user, register_user

load_dotenv()

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # We'll handle expiration manually

db.init_app(app)
jwt = JWTManager(app)

# Redis Configuration for Upstash (REST API based)
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

# Helper function to interact with Upstash Redis REST API
def upstash_redis_command(command, *args):
    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        return None
    headers = {"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}
    try:
        response = requests.post(
            f"{UPSTASH_REDIS_REST_URL}/{command}",
            headers=headers,
            json=list(args)
        )
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Upstash Redis command failed: {e}")
        return None

# Models are already imported at the top

# Multi-tenancy Middleware (simplified for demonstration)
@app.before_request
def before_request():
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        # In a real application, you\'d validate the tenant_id
        # and set it in a global context or session for the request.
        # For now, we\'ll just store it in g (Flask\'s global request object).
        from flask import g
        g.tenant_id = tenant_id
    else:
        # Handle cases where tenant_id is not provided (e.g., public endpoints, login)
        pass

@app.route("/")
def hello_world():
    return "Hello, MorningAI API!"

@app.route("/readiness")
def readiness_check():
    # Check database connection
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "OK"
    except Exception as e:
        db_status = f"Error: {e}"

    # Check Redis connection (using Upstash REST API ping)
    redis_status = "OK"
    if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
        try:
            ping_response = upstash_redis_command("ping")
            if ping_response and ping_response[0] == "PONG":
                redis_status = "OK"
            else:
                redis_status = f"Error: Redis ping failed: {ping_response}"
        except Exception as e:
            redis_status = f"Error: {e}"
    else:
        redis_status = "Error: Redis not configured"

    if db_status == "OK" and redis_status == "OK":
        return jsonify({"status": "ready", "database": db_status, "redis": redis_status}), 200
    else:
        return jsonify({"status": "not ready", "database": db_status, "redis": redis_status}), 500

@app.route("/users", methods=["GET", "POST"])
def users():
    from flask import g
    current_tenant_id = getattr(g, "tenant_id", None)

    if not current_tenant_id:
        return jsonify({"message": "Tenant ID required"}), 400

    if request.method == "POST":
        data = request.get_json()
        new_user = User(username=data["username"], email=data["email"], password_hash="hashed_password", tenant_id=current_tenant_id)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created", "user_id": new_user.id}), 201
    else:
        users = User.query.filter_by(tenant_id=current_tenant_id).all()
        return jsonify([{"id": user.id, "username": user.username, "email": user.email} for user in users])

@app.route("/tenants", methods=["GET", "POST"])
def tenants():
    if request.method == "POST":
        data = request.get_json()
        new_tenant = Tenant(name=data["name"], schema_name=data["schema_name"])
        db.session.add(new_tenant)
        db.session.commit()
        return jsonify({"message": "Tenant created", "tenant_id": new_tenant.id}), 201
    else:
        tenants = Tenant.query.all()
        return jsonify([{"id": tenant.id, "name": tenant.name, "schema_name": tenant.schema_name} for tenant in tenants])

# Authentication Routes
@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["username", "email", "password", "tenant_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    user, error = register_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
        tenant_id=data["tenant_id"]
    )
    
    if error:
        return jsonify({"message": error}), 400
    
    # Create tokens for the new user
    access_token, refresh_token = create_tokens(user.id, user.tenant_id)
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 201

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    
    # Validate required fields
    if "username" not in data or "password" not in data:
        return jsonify({"message": "Username and password are required"}), 400
    
    user = authenticate_user(data["username"], data["password"])
    
    if not user:
        return jsonify({"message": "Invalid username or password"}), 401
    
    # Create tokens
    access_token, refresh_token = create_tokens(user.id, user.tenant_id)
    
    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200

@app.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = int(get_jwt_identity())  # Convert back to int
    claims = get_jwt()
    tenant_id = claims.get("tenant_id")
    
    # Create new access token
    access_token, _ = create_tokens(current_user_id, tenant_id)
    
    return jsonify({
        "access_token": access_token
    }), 200

@app.route("/auth/profile", methods=["GET"])
@jwt_required()
def profile():
    current_user_id = int(get_jwt_identity())  # Convert back to int
    claims = get_jwt()
    tenant_id = claims.get("tenant_id")
    
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    return jsonify({
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }), 200

@app.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    # In a production environment, you would typically add the JWT to a blacklist
    # For now, we'll just return a success message
    return jsonify({"message": "Logout successful"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

