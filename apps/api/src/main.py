
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests # For Upstash Redis REST API
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

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

# Import models after db is initialized
from src.models import User, Tenant

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

