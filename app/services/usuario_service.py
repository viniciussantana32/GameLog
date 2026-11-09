from app.extensions import db
from app.models.usuario import Usuario


class UsuarioService:
    """Camada de serviços responsável pela regra de negócio de usuários e autenticação."""

    @staticmethod
    def obter_por_id(usuario_id):
        """Busca usuário pelo identificador numérico."""
        return Usuario.query.get(int(usuario_id))

    @staticmethod
    def obter_por_username(username):
        """Busca usuário pelo username."""
        return Usuario.query.filter_by(username=username.strip().lower()).first()

    @staticmethod
    def obter_por_email(email):
        """Busca usuário pelo e-mail."""
        return Usuario.query.filter_by(email=email.strip().lower()).first()

    @staticmethod
    def autenticar(identificador, senha):
        """
        Autentica o usuário pelo username ou e-mail com conferência de hash da senha.
        Retorna a instância do Usuario se credenciais forem válidas, ou None.
        """
        termo = identificador.strip().lower()
        usuario = Usuario.query.filter(
            (Usuario.username == termo) | (Usuario.email == termo)
        ).first()

        if usuario and usuario.verificar_senha(senha):
            return usuario
        return None

    @staticmethod
    def criar_usuario(dados):
        """Cadastra um novo usuário no banco de dados JOGOSSALVOS com senha criptografada."""
        username = dados.get('username').strip().lower()
        email = dados.get('email').strip().lower()

        novo_usuario = Usuario(
            nome=dados.get('nome').strip(),
            username=username,
            email=email,
            bio=dados.get('bio', '').strip() if dados.get('bio') else None,
            avatar_url=dados.get('avatar_url', '').strip() if dados.get('avatar_url') else None,
            is_admin=dados.get('is_admin', False)
        )
        novo_usuario.set_senha(dados.get('senha'))

        db.session.add(novo_usuario)
        db.session.commit()
        return novo_usuario

    @staticmethod
    def atualizar_perfil(usuario, dados):
        """Atualiza os dados de perfil de um usuário existente."""
        novo_username = dados.get('username').strip().lower()
        novo_email = dados.get('email').strip().lower()

        # Checa duplicidade caso tenha alterado o username
        if novo_username != usuario.username:
            existente = Usuario.query.filter_by(username=novo_username).first()
            if existente:
                raise ValueError("Este nome de usuário já está em uso por outra conta.")
            usuario.username = novo_username

        # Checa duplicidade caso tenha alterado o email
        if novo_email != usuario.email:
            existente = Usuario.query.filter_by(email=novo_email).first()
            if existente:
                raise ValueError("Este e-mail já está em uso por outra conta.")
            usuario.email = novo_email

        usuario.nome = dados.get('nome').strip()
        usuario.bio = dados.get('bio', '').strip() if dados.get('bio') else None
        usuario.avatar_url = dados.get('avatar_url', '').strip() if dados.get('avatar_url') else None

        db.session.commit()
        return usuario

    @staticmethod
    def alterar_senha(usuario, senha_atual, nova_senha):
        """Valida a senha atual e define a nova senha com hash criptografado."""
        if not usuario.verificar_senha(senha_atual):
            raise ValueError("A senha atual informada está incorreta.")

        usuario.set_senha(nova_senha)
        db.session.commit()
        return True

