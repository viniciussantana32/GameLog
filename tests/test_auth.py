from app.models.usuario import Usuario
from app.services.usuario_service import UsuarioService


def test_registro_usuario_sucesso(client, app):
    """Testa cadastro de novo usuário com dados válidos."""
    dados = {
        'nome': 'Novo Jogador',
        'username': 'novojogador',
        'email': 'novo@jogador.com',
        'senha': 'segredo123',
        'confirmar_senha': 'segredo123'
    }
    response = client.post('/registro', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"Conta criada com sucesso" in response.data

    with app.app_context():
        usuario = Usuario.query.filter_by(username='novojogador').first()
        assert usuario is not None
        assert usuario.nome == 'Novo Jogador'
        assert usuario.verificar_senha('segredo123') is True
        assert usuario.verificar_senha('senhaerrada') is False


def test_registro_usuario_duplicado(client, app, usuario_padrao):
    """Testa validação ao tentar registrar com e-mail ou username já existente."""
    dados = {
        'nome': 'Outro Jogador',
        'username': 'jogadorteste',  # Duplicado
        'email': 'outro@jogador.com',
        'senha': 'senha123',
        'confirmar_senha': 'senha123'
    }
    response = client.post('/registro', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"Este nome de usu\xc3\xa1rio j\xc3\xa1 est\xc3\xa1 em uso" in response.data


def test_login_sucesso(client, app, usuario_padrao):
    """Testa autenticação com credenciais corretas."""
    dados = {
        'identificador': 'jogadorteste',
        'senha': 'senha123'
    }
    response = client.post('/login', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"Bem-vindo(a) de volta" in response.data


def test_login_senha_incorreta(client, app, usuario_padrao):
    """Testa tentativa de login com senha incorreta."""
    dados = {
        'identificador': 'jogadorteste',
        'senha': 'senhainvalida'
    }
    response = client.post('/login', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"incorretos" in response.data


def test_logout(auth_client):
    """Testa encerramento de sessão."""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"encerrou sua sess\xc3\xa3o" in response.data


def test_atualizar_perfil(auth_client, app, usuario_padrao):
    """Testa atualização de dados cadastrais no perfil."""
    dados = {
        'nome': 'Jogador Atualizado',
        'username': 'jogador_atualizado',
        'email': 'jogador_atualizado@teste.com',
        'bio': 'Nova bio atualizada!',
        'avatar_url': 'https://exemplo.com/avatar.png'
    }
    response = auth_client.post('/perfil', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"atualizado com sucesso" in response.data

    with app.app_context():
        usuario = Usuario.query.get(usuario_padrao)
        assert usuario.nome == 'Jogador Atualizado'
        assert usuario.username == 'jogador_atualizado'
        assert usuario.bio == 'Nova bio atualizada!'


def test_alterar_senha(auth_client, app, usuario_padrao):
    """Testa alteração segura de senha."""
    dados = {
        'senha_atual': 'senha123',
        'nova_senha': 'novasenha456',
        'confirmar_nova_senha': 'novasenha456'
    }
    response = auth_client.post('/perfil/senha', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"alterada com sucesso" in response.data

    with app.app_context():
        usuario = Usuario.query.get(usuario_padrao)
        assert usuario.verificar_senha('novasenha456') is True
        assert usuario.verificar_senha('senha123') is False

