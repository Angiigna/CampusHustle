from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Configure Socket.IO with CORS allowed for local dev
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.rider import rider_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(rider_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Register Socket.IO Event Handlers
    from app.sockets import events

    return app
