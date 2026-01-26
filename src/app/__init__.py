import os
from flask import Flask, send_from_directory


def create_app(config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(config or {})

    # simple config defaults
    app.config.setdefault("TOPICS_DIR", None)
    # prefer an explicit TOPICS_DB env var, otherwise default to data/data.db
    app.config.setdefault("TOPICS_DB", os.environ.get("TOPICS_DB", "data/data.db"))
    # user DB and password manager for auth
    app.config.setdefault("USERS_DB", os.environ.get("USERS_DB", "data/users.db"))
    app.config.setdefault("SECRET_KEY", "dev")
    # ensure the Flask app.secret_key attribute is set (prefer env var)
    app.secret_key = os.environ.get("SECRET_KEY", app.config.get("SECRET_KEY"))

    # instantiate password manager and user repository
    from .utils.password_manager import PasswordManager
    from .repositories.user_repo_sqlite import SQLiteUserRepository

    app.pwm = PasswordManager()
    app.user_repo = SQLiteUserRepository(
        db_path=app.config.get("USERS_DB"), password_manager=app.pwm
    )

    # register blueprints lazily to avoid import cycles
    from .controllers.topics import bp as topics_bp

    app.register_blueprint(topics_bp)
    # register auth blueprint
    from .controllers.auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    # serve a favicon at /favicon.ico (return a static SVG as favicon)
    @app.route("/favicon.ico")
    def favicon():
        # Prefer a real favicon.ico if present in static, otherwise fall back to favicon.svg
        ico_path = app.static_folder + "/favicon.ico"
        try:
            # use send_from_directory which will raise if file missing
            return send_from_directory(
                app.static_folder, "favicon.ico", mimetype="image/x-icon"
            )
        except Exception:
            return send_from_directory(
                app.static_folder, "favicon.svg", mimetype="image/svg+xml"
            )

    return app
