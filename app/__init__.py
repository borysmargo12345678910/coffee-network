from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Будь ласка, увійдіть у систему'
    login_manager.login_message_category = 'warning'

    from app.auth import auth_bp
    from app.branches import branches_bp
    from app.menu import menu_bp
    from app.orders import orders_bp
    from app.inventory import inventory_bp
    from app.staff import staff_bp
    from app.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(branches_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(reports_bp)

    return app
