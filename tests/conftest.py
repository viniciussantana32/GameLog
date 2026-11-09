import pytest
from datetime import date
from flask_login import login_user
from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from app.models.jogos import Jogo


@pytest.fixture
def app():
    """Cria e configura uma instância de aplicação para testes."""
    application = create_app(config_name='testing')

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste Flask para simular requisições HTTP."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Executor de linha de comando CLI do Flask."""
    return app.test_cli_runner()


@pytest.fixture
def usuario_padrao(app):
    """Cria um usuário padrão para testes com senha criptografada."""
    with app.app_context():
        usuario = Usuario(
            nome="Jogador Teste",
            username="jogadorteste",
            email="jogador@teste.com",
            bio="Gamer entusiasta de RPGs"
        )
        usuario.set_senha("senha123")
        db.session.add(usuario)
        db.session.commit()
        return usuario.id


@pytest.fixture
def auth_client(client, app, usuario_padrao):
    """Cliente autenticado logado com o usuario_padrao."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(usuario_padrao)
        sess['_fresh'] = True
    return client


@pytest.fixture
def jogo_exemplo(app, usuario_padrao):
    """Cria um registro de jogo padrão para testes vinculado ao usuário."""
    with app.app_context():
        jogo = Jogo(
            usuario_id=usuario_padrao,
            titulo="The Witcher 3: Wild Hunt",
            plataforma="PC",
            genero="RPG de Ação",
            ano_lancamento=2015,
            data_zeramento=date(2023, 5, 20),
            tempo_jogado_horas=120.5,
            nota=10.0,
            dificuldade="Difícil",
            observacoes="Uma das melhores narrativas e ambientações já criadas nos videogames."
        )
        db.session.add(jogo)
        db.session.commit()
        return jogo.id
