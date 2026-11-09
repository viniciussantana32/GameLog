from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


PLATAFORMAS_CHOICES = [
    ('', 'Selecione a plataforma...'),
    ('PC', 'PC (Steam, Epic, GOG, etc.)'),
    ('PlayStation 5', 'PlayStation 5'),
    ('PlayStation 4', 'PlayStation 4'),
    ('Xbox Series X/S', 'Xbox Series X/S'),
    ('Xbox One', 'Xbox One'),
    ('Nintendo Switch', 'Nintendo Switch'),
    ('Mobile', 'Mobile (Android / iOS)'),
    ('Retro / Clássico', 'Retro / Clássico'),
    ('Outra', 'Outra Plataforma')
]

DIFICULDADE_CHOICES = [
    ('', 'Selecione a dificuldade...'),
    ('Muito Fácil', 'Muito Fácil'),
    ('Fácil', 'Fácil'),
    ('Normal / Padrão', 'Normal / Padrão'),
    ('Difícil', 'Difícil'),
    ('Extrema / Hardcore', 'Extrema / Hardcore')
]

STATUS_CHOICES = [
    ('', 'Sem status'),
    ('jogando', 'Jogando'),
    ('zerado', 'Zerado')
]


class JogoForm(FlaskForm):
    """Formulário para cadastro e edição de jogos da biblioteca."""
    titulo = StringField(
        'Título do Jogo *',
        validators=[
            DataRequired(message='O título do jogo é obrigatório.'),
            Length(max=150, message='O título deve ter no máximo 150 caracteres.')
        ],
        render_kw={'placeholder': 'Ex: The Witcher 3, Elden Ring, God of War...'}
    )

    plataforma = SelectField(
        'Plataforma *',
        choices=PLATAFORMAS_CHOICES,
        validators=[
            DataRequired(message='Selecione a plataforma em que o jogo foi finalizado.')
        ]
    )

    genero = StringField(
        'Gênero',
        validators=[
            Optional(),
            Length(max=80, message='O gênero deve ter no máximo 80 caracteres.')
        ],
        render_kw={'placeholder': 'Ex: RPG de Ação, Aventura, Soulslike, FPS...'}
    )

    status = SelectField(
        'Status',
        choices=STATUS_CHOICES,
        validators=[Optional()],
        default='zerado'
    )

    ano_lancamento = IntegerField(
        'Ano de Lançamento',
        validators=[
            Optional(),
            NumberRange(min=1970, max=2100, message='Informe um ano de lançamento válido.')
        ],
        render_kw={'placeholder': 'Ex: 2023'}
    )

    data_zeramento = DateField(
        'Data em que Zerou',
        format='%Y-%m-%d',
        validators=[Optional()]
    )

    tempo_jogado_horas = FloatField(
        'Tempo Jogado (Horas)',
        validators=[
            Optional(),
            NumberRange(min=0, message='As horas jogadas não podem ser negativas.')
        ],
        render_kw={'placeholder': 'Ex: 45.5', 'step': '0.5'}
    )

    nota = FloatField(
        'Nota Pessoal (0 a 10)',
        validators=[
            Optional(),
            NumberRange(min=0.0, max=10.0, message='A nota deve estar entre 0 e 10.')
        ],
        render_kw={'placeholder': 'Ex: 9.5', 'step': '0.5', 'min': '0', 'max': '10'}
    )

    dificuldade = SelectField(
        'Dificuldade Finalizada',
        choices=DIFICULDADE_CHOICES,
        validators=[Optional()]
    )

    observacoes = TextAreaField(
        'Análise / Comentários Pessoais',
        validators=[
            Optional(),
            Length(max=2000, message='A análise deve ter no máximo 2000 caracteres.')
        ],
        render_kw={'placeholder': 'O que achou da história, gameplay, gráficos, trilha sonora...', 'rows': 4}
    )

    submit = SubmitField('Salvar Jogo')


class DeleteForm(FlaskForm):
    """Formulário exclusivo para exclusão segura com proteção CSRF."""
    submit = SubmitField('Confirmar Exclusão')
