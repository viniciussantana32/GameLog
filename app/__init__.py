import os
from datetime import datetime
from flask import Flask, render_template
from app.config import config_by_name
from app.extensions import db, migrate, csrf, login_manager
from app.models.usuario import Usuario
from app.routes.jogos_routes import jogos_bp
from app.routes.auth_routes import auth_bp


def create_app(config_name=None):
    """
    Application Factory para a aplicação Meus Jogos.
    Configura extensões, autenticação, Blueprints, handlers de erro e banco de dados.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', os.environ.get('FLASK_ENV', 'development'))

    app = Flask(__name__)
    
    # Carrega a configuração apropriada
    config_class = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_class)

    # Inicialização das extensões
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Carregador de usuário para o Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registro de Blueprints
    app.register_blueprint(jogos_bp)
    app.register_blueprint(auth_bp)

    # Injetor de contexto global para os templates Jinja2
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'Gamelog',
            'current_year': datetime.utcnow().year
        }

    # Handlers para páginas de erro personalizadas
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app
