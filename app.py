"""Entry point. Start the application with ``python app.py``.

Environment variables:
  PORT      port to listen on          (default 8000)
  DATA_DIR  directory for habits.db    (default ./data)
"""

import os

from flask import Flask, Response, jsonify

from db import close_db, init_db
from habits.routes import bp as habits_bp
from insights.routes import bp as insights_bp


def create_app(data_dir: str | None = None) -> Flask:
    """Create the Flask application using the requested data directory."""
    app = Flask(__name__)
    data_dir = data_dir or os.environ.get("DATA_DIR") or "data"
    app.config["DB_PATH"] = os.path.join(data_dir, "habits.db")

    init_db(app.config["DB_PATH"])
    app.teardown_appcontext(close_db)

    app.register_blueprint(habits_bp)
    app.register_blueprint(insights_bp)

    @app.get("/health")
    def health() -> Response:
        """Return the app's liveness status."""
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    # 0.0.0.0 is required so the app is reachable from outside the container.
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
