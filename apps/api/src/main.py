import os
import sys
# DON\"T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from src.models.user import db
from src.routes.user import user_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), \"static\"))
app.config[\"SECRET_KEY\"] = \"asdf#FGSgvasgf$5$WGT\"

app.register_blueprint(user_bp, url_prefix=\"/api\")

# uncomment if you need to use database
app.config[\"SQLALCHEMY_DATABASE_URI\"] = f\"sqlite:///{os.path.join(os.path.dirname(__file__), \"database\", \"app.db\")}\"
app.config[\"SQLALCHEMY_TRACK_MODIFICATIONS\"] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route(\"/health\")
def health_check():
    return jsonify({\"ok\": True}), 200

@app.route(\"/debug/env\")
def debug_env():
    visible_keys = [\"PORT\",\"CORS_ALLOW_ORIGIN\",\"RENDER\",\"RENDER_GIT_BRANCH\",\"RENDER_GIT_COMMIT\",\"RENDER_SERVICE_ID\"]
    env = {k: os.getenv(k) for k in visible_keys}
    return jsonify({
        \"env\": env,
        \"cwd\": os.getcwd(),
        \"pythonpath\": sys.path,
        \"workdir_listing\": os.listdir("."),
    })

# This route should be after all other routes
@app.route(\"/\")
def serve_root():
    return send_from_directory(app.static_folder, \"index.html\")

@app.route(\"/<path:path>\")
def serve_static(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return \"Static folder not configured\", 404

    if os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return send_from_directory(static_folder_path, \"index.html\")


if __name__ == \"__main__\":
    app.run(host=\"0.0.0.0\", port=5000, debug=True)


