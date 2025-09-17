import os, sys
from flask import Flask, jsonify


app = Flask(__name__)
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

# Register blueprints first


@app.route("/health")
def health_check():
    return jsonify({"ok": True}), 200



# uncomment if you need to use database


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)






@app.route("/debug/env")
def debug_env():
    visible_keys = ["PORT","CORS_ALLOW_ORIGIN","RENDER","RENDER_GIT_BRANCH","RENDER_GIT_COMMIT","RENDER_SERVICE_ID"]
    env = {k: os.getenv(k) for k in visible_keys}
    return jsonify({
        "env": env,
        "cwd": os.getcwd(),
        "pythonpath": sys.path,
        "workdir_listing": os.listdir("."),
    })


