import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError, Regexp
from app.models.usuario import Usuario


class LoginForm(FlaskForm):
    """Formulário de autenticação de usuários."""
    identificador = StringField(
        'E-mail ou Usuário *',
        validators=[DataRequired(message='Informe seu e-mail ou nome de usuário.')],
        render_kw={'placeholder': 'seu_usuario ou email@exemplo.com'}
    )
    senha = PasswordField(
        'Senha *',
        validators=[DataRequired(message='Informe sua senha.')],
        render_kw={'placeholder': 'Digite sua senha'}
    )
    lembrar_me = BooleanField('Lembrar-me neste dispositivo')
    submit = SubmitField('Entrar na Conta')


class RegistroForm(FlaskForm):
    """Formulário para cadastro de novos usuários."""
    nome = StringField(
        'Nome Completo *',
        validators=[
            DataRequired(message='O nome é obrigatório.'),
            Length(min=2, max=100, message='O nome deve ter entre 2 e 100 caracteres.')
        ],
        render_kw={'placeholder': 'Ex: Vinicius Santana'}
    )
    username = StringField(
        'Nome de Usuário (Username) *',
        validators=[
            DataRequired(message='O username é obrigatório.'),
            Length(min=3, max=50, message='O username deve ter entre 3 e 50 caracteres.'),
            Regexp(r'^[a-zA-Z0-9_]+$', message='O username deve conter apenas letras, números e underline (_).')
        ],
        render_kw={'placeholder': 'Ex: vinicius_gamer'}
    )
    email = StringField(
        'E-mail *',
        validators=[
            DataRequired(message='O e-mail é obrigatório.'),
            Email(message='Informe um e-mail válido.'),
            Length(max=120, message='E-mail muito longo.')
        ],
        render_kw={'placeholder': 'seuemail@exemplo.com'}
    )
    senha = PasswordField(
        'Senha *',
        validators=[
            DataRequired(message='A senha é obrigatória.'),
            Length(min=6, message='A senha deve possuir pelo menos 6 caracteres.')
        ],
        render_kw={'placeholder': 'Mínimo de 6 caracteres'}
    )
    confirmar_senha = PasswordField(
        'Confirmar Senha *',
        validators=[
            DataRequired(message='Confirme sua senha.'),
            EqualTo('senha', message='As senhas informadas não coincidem.')
        ],
        render_kw={'placeholder': 'Repita a mesma senha'}
    )
    submit = SubmitField('Criar Conta')

    def validate_username(self, username):
        usuario = Usuario.query.filter_by(username=username.data.strip().lower()).first()
        if usuario:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data.strip().lower()).first()
        if usuario:
            raise ValidationError('Este e-mail já está cadastrado no sistema. Tente fazer login.')


class PerfilForm(FlaskForm):
    """Formulário para edição dos dados do perfil de usuário."""
    nome = StringField(
        'Nome Completo *',
        validators=[
            DataRequired(message='O nome é obrigatório.'),
            Length(min=2, max=100, message='O nome deve ter entre 2 e 100 caracteres.')
        ]
    )
    username = StringField(
        'Nome de Usuário *',
        validators=[
            DataRequired(message='O username é obrigatório.'),
            Length(min=3, max=50, message='O username deve ter entre 3 e 50 caracteres.'),
            Regexp(r'^[a-zA-Z0-9_]+$', message='Apenas letras, números e underline (_).')
        ]
    )
    email = StringField(
        'E-mail *',
        validators=[
            DataRequired(message='O e-mail é obrigatório.'),
            Email(message='Informe um e-mail válido.')
        ]
    )
    bio = TextAreaField(
        'Biografia / Sobre Mim',
        validators=[Optional(), Length(max=500, message='A bio pode ter no máximo 500 caracteres.')],
        render_kw={'placeholder': 'Conte um pouco sobre seu gosto por jogos, franquias favoritas...', 'rows': 3}
    )
    avatar_url = StringField(
        'URL da Imagem de Perfil (Avatar)',
        validators=[Optional(), Length(max=255, message='URL muito longa.')],
        render_kw={'placeholder': 'https://exemplo.com/avatar.jpg'}
    )
    submit = SubmitField('Salvar Alterações')


class AlterarSenhaForm(FlaskForm):
    """Formulário para alteração de senha autenticada."""
    senha_atual = PasswordField(
        'Senha Atual *',
        validators=[DataRequired(message='Informe sua senha atual.')]
    )
    nova_senha = PasswordField(
        'Nova Senha *',
        validators=[
            DataRequired(message='Informe a nova senha.'),
            Length(min=6, message='A nova senha deve possuir pelo menos 6 caracteres.')
        ]
    )
    confirmar_nova_senha = PasswordField(
        'Confirmar Nova Senha *',
        validators=[
            DataRequired(message='Confirme a nova senha.'),
            EqualTo('nova_senha', message='A confirmação não coincide com a nova senha.')
        ]
    )
    submit = SubmitField('Atualizar Senha')

