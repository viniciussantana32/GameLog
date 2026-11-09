from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Usuario(UserMixin, db.Model):
    """
    Model representativo de Usuários e Perfis da aplicação Meus Jogos.
    Permite autenticação, controle de perfis e vínculo aos jogos zerados.
    """
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamento com os jogos cadastrados pelo usuário
    jogos = db.relationship(
        'Jogo',
        backref='autor',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_senha(self, senha):
        """Gera e armazena o hash criptografado da senha."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """Compara a senha informada com o hash criptografado."""
        return check_password_hash(self.senha_hash, senha)

    @property
    def total_jogos_zerados(self):
        """Retorna o total de jogos cadastrados pelo usuário."""
        return self.jogos.count()

    def __repr__(self):
        return f"<Usuario {self.id} - @{self.username} ({self.nome})>"

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'username': self.username,
            'email': self.email,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_admin': self.is_admin,
            'total_jogos': self.total_jogos_zerados,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }

