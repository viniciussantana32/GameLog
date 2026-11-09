from datetime import datetime
from app.extensions import db


class Jogo(db.Model):
    """
    Model representativo da entidade Meus Jogos (jogos cadastrados e zerados).
    Armazena os registros no banco JOGOSSALVOS vinculado ao usuário proprietário.
    """
    __tablename__ = 'jogos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True, index=True)
    titulo = db.Column(db.String(150), nullable=False, index=True)
    plataforma = db.Column(db.String(80), nullable=False, index=True)
    genero = db.Column(db.String(80), nullable=True)
    ano_lancamento = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=True, index=True)
    data_zeramento = db.Column(db.Date, nullable=True)
    tempo_jogado_horas = db.Column(db.Float, nullable=True)
    nota = db.Column(db.Float, nullable=True)
    dificuldade = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Jogo {self.id} - {self.titulo} ({self.plataforma})>"

    def to_dict(self):
        """Serializa o modelo para dicionário."""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'autor': self.autor.username if self.autor else None,
            'titulo': self.titulo,
            'plataforma': self.plataforma,
            'genero': self.genero,
            'ano_lancamento': self.ano_lancamento,
            'data_zeramento': self.data_zeramento.isoformat() if self.data_zeramento else None,
            'tempo_jogado_horas': self.tempo_jogado_horas,
            'nota': self.nota,
            'dificuldade': self.dificuldade,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
