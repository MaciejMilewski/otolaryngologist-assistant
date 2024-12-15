from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# from app.models import User
from config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            from app.models import User
            return User.query.get(int(user_id))

    # TODO: dodaj blueprinty dla reszty routes
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.start import start_bp
    app.register_blueprint(start_bp)

    from app.routes.visit import visit_bp
    app.register_blueprint(visit_bp)

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    return app

