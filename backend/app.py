import logging

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import get_config
from models import db
from routes.auth import auth_bp
from routes.expenses import expenses_bp
from routes.imports import imports_bp


def create_app() -> Flask:
    """Minimal app factory to keep setup easy to follow."""
    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Simple table creation for dev; swap to migrations in production.
    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(imports_bp)

    @app.get("/healthz")
    def health():
        return jsonify({"status": "ok"})

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="0.0.0.0", port=5000, debug=True)
