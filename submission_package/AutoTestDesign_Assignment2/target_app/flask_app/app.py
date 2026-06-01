"""任务管理平台 — Flask 应用工厂"""

from flask import Flask
from flask_app.config import SECRET_KEY
from flask_app.models.database import init_db, close_db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    app.teardown_appcontext(close_db)

    from flask_app.routes.auth import bp as auth_bp
    from flask_app.routes.projects import bp as projects_bp
    from flask_app.routes.tasks import bp as tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)

    @app.route("/health")
    def health():
        from datetime import datetime
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    with app.app_context():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
