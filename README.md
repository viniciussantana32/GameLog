# 🎮 Meus Jogos

> Sistema web moderno e modular para gerenciamento e diário pessoal de jogos finalizados (jogos zerados), com **Autenticação**, **Controle de Usuários e Perfis**, desenvolvido com **Python**, **Flask**, **SQLAlchemy** e banco de dados **JOGOSSALVOS**.

---

## 1. Descrição do Projeto

O **Meus Jogos** é uma plataforma completa que combina o gerenciamento de jogos zerados (CRUD) com um sistema seguro de **autenticação e perfis de usuários**. Cada jogador possui sua própria conta, seu diário individual e controle sobre as suas postagens.

### Principais Módulos e Recursos:
- **Autenticação e Segurança:**
  - Registro de novos usuários com validação de unicidade de e-mail e username.
  - Login com identificação por nome de usuário ou e-mail.
  - Senhas criptografadas com hash seguro (`generate_password_hash` da Werkzeug).
  - Gerenciamento de sessão persistente com [Flask-Login](https://flask-login.readthedocs.io/).
  - Proteção de rotas com decorador `@login_required`.
  - Proteção total contra CSRF em todos os formulários.
- **Perfis de Jogador (Profile):**
  - Página de perfil customizável com Nome, Username, E-mail, Biografia e URL de Avatar.
  - Medidor de jogos zerados e data de criação da conta.
  - Troca segura de senha (exige confirmação da senha atual).
  - Níveis de permissão (Usuário Gamer comum e Administrador).
- **CRUD de Meus Jogos Vinculado ao Usuário:**
  - **Create:** Cadastrar novos jogos zerados vinculados à sua conta.
  - **Read:** Visualização dos próprios jogos ou alternância para explorar títulos compartilhados pela comunidade.
  - **Update:** Edição exclusiva permitida apenas ao autor do registro ou administradores.
  - **Delete:** Exclusão segura com modal de confirmação, restrita ao proprietário do registro.
- **Dashboard Estatístico:** Métricas individuais do usuário logado (total zerados, média de notas, horas jogadas e plataforma favorita).
- **Integração com API Oficial do IGDB (Twitch Developer):**
  - Catálogo integrado com a base do **IGDB (Internet Game Database)** com mais de 500.000 jogos cadastrados.
  - Carregamento de capas em alta resolução (`t_cover_big`), gêneros, plataformas, avaliações e resumos oficiais.
  - Importação com 1 clique para o banco de dados `JOGOSSALVOS`.
  - Fallback automático caso as chaves ainda não estejam configuradas.

---

## 2. Tecnologias Utilizadas

- **Linguagem Backend:** Python 3
- **Framework Web:** [Flask](https://flask.palletsprojects.com/) (Application Factory e Blueprints)
- **Autenticação e Sessão:** [Flask-Login](https://flask-login.readthedocs.io/)
- **Criptografia de Senhas:** Werkzeug Security (`scrypt`/`pbkdf2`)
- **ORM / Persistência:** [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- **Versionamento de Banco (Migrations):** [Flask-Migrate](https://flask-migrate.readthedocs.io/) / Alembic
- **Formulários e Segurança:** [Flask-WTF](https://flask-wtf.readthedocs.io/) com WTForms e `email-validator`
- **Variáveis de Ambiente:** [python-dotenv](https://pypi.org/project/python-dotenv/)
- **Drivers de Banco:** PyMySQL e SQLite nativo
- **Frontend:** HTML5 semântico, CSS3 moderno (tema escuro gamer, glassmorphism e responsivo) e JavaScript (ES6)
- **Testes Automatizados:** [pytest](https://docs.pytest.org/)

---

## 3. Estrutura de Diretórios

```text
Projeto/
│
├── app/
│   ├── __init__.py              # Application Factory (create_app), setup de login e extensões
│   ├── extensions.py            # Instâncias de db, migrate, csrf e login_manager
│   ├── config.py                # Configurações de ambientes (Dev, Test, Prod)
│   │
│   ├── models/                  # Camada de Entidades
│   │   ├── __init__.py
│   │   ├── usuario.py           # Model Usuario (UserMixin, hash de senha, perfil)
│   │   └── jogos.py             # Model Jogo (relacionado com Usuario)
│   │
│   ├── routes/                  # Blueprints e Rotas HTTP
│   │   ├── __init__.py
│   │   ├── auth_routes.py       # Rotas de Login, Registro, Logout, Perfil e Senha
│   │   └── jogos_routes.py      # Rotas de CRUD de Jogos com controle de permissão
│   │
│   ├── services/                # Camada de Negócio e Acesso aos Dados
│   │   ├── __init__.py
│   │   ├── usuario_service.py   # Lógica de autenticação, registro e perfil
│   │   └── jogos_service.py     # Lógica de persistência e cálculo de métricas
│   │
│   ├── forms/                   # Formulários e Validações
│   │   ├── __init__.py
│   │   ├── auth_forms.py        # LoginForm, RegistroForm, PerfilForm, AlterarSenhaForm
│   │   └── jogos_forms.py       # JogoForm, DeleteForm
│   │
│   ├── templates/               # Templates Jinja2
│   │   ├── base.html            # Layout com barra de navegação dinâmica (login/perfil)
│   │   ├── index.html           # Dashboard com dados do usuário logado
│   │   ├── 404.html             # Página 404
│   │   ├── 500.html             # Página 500
│   │   ├── auth/
│   │   │   ├── login.html       # Tela de login
│   │   │   ├── registro.html    # Tela de cadastro de conta
│   │   │   └── perfil.html      # Tela de visualização e edição de perfil e senha
│   │   └── JOGOSBASE/
│   │       ├── list.html        # Listagem com alternância (Meus Jogos / Comunidade)
│   │       ├── detail.html      # Detalhes e autoria do jogo
│   │       ├── create.html      # Cadastro de jogo
│   │       └── edit.html        # Edição de jogo
│   │
│   └── static/                  # Estilos e Scripts
│       ├── css/
│       │   ├── style.css        # Estilos globais
│       │   └── pagina.css       # Estilos dos jogos, perfil e dashboard
│       └── js/
│           ├── main.js          # Menu mobile e auto-dismiss de alertas
│           └── games.js         # Confirmação de exclusão dinâmica
│
├── migrations/                  # Histórico de Migrations Alembic
│   ├── versions/
│   │   └── 001_initial_jogos.py # Criação das tabelas 'usuarios' e 'jogos'
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
│
├── tests/                       # Testes Automatizados
│   ├── __init__.py
│   ├── conftest.py              # Fixtures de app, usuário de teste e cliente autenticado
│   ├── test_auth.py             # Testes de registro, login, logout, perfil e senha
│   └── test_games.py            # Testes do CRUD de jogos e permissões
│
├── .env.example                 # Modelo de variáveis de ambiente
├── .env                         # Variáveis de ambiente ativas
├── .gitignore                   # Arquivos ignorados pelo Git
├── config.py                    # Exportação de configurações
├── requirements.txt             # Dependências fixadas
├── run.py                       # Ponto de inicialização da aplicação
└── README.md                    # Documentação completa
```

---

## 4. Modelos e Banco de Dados (JOGOSSALVOS)

### Tabela `usuarios`
| Campo | Tipo | Descrição |
|---|---|---|
| `id` | Integer (PK) | Identificador único |
| `nome` | String(100) | Nome completo do usuário |
| `username` | String(50) | Nome de usuário único para login e arroba (`@`) |
| `email` | String(120) | E-mail único do usuário |
| `senha_hash` | String(255) | Hash criptografado da senha (não guarda texto puro) |
| `bio` | Text | Descrição / biografia do perfil |
| `avatar_url` | String(255) | URL opcional para foto de perfil |
| `is_admin` | Boolean | Define se o usuário é administrador |
| `data_criacao` | DateTime | Data do cadastro |

### Tabela `jogos`
| Campo | Tipo | Descrição |
|---|---|---|
| `id` | Integer (PK) | Identificador do jogo |
| `usuario_id` | Integer (FK) | Chave estrangeira para `usuarios.id` |
| `titulo` | String(150) | Título do jogo |
| `plataforma` | String(80) | Plataforma onde foi finalizado |
| `genero` | String(80) | Gênero do jogo |
| `ano_lancamento` | Integer | Ano de lançamento |
| `data_zeramento` | Date | Data em que zerou |
| `tempo_jogado_horas` | Float | Horas de campanha |
| `nota` | Float | Avaliação pessoal (0 a 10) |
| `dificuldade` | String(50) | Dificuldade da campanha |
| `observacoes` | Text | Análise pessoal e resenha |

---

## 5. Como Executar a Aplicação

Abra o terminal no diretório `Projeto`:

### Passo 1: Criar e ativar o ambiente virtual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Passo 2: Instalar as dependências
```bash
pip install -r requirements.txt
```

### Passo 3: Preparar o schema do banco
```bash
flask db upgrade
```

Se o banco já existia antes da criação das migrations e ainda não possui histórico Alembic, confirme que seu schema corresponde à migration inicial e execute uma única vez:

```bash
flask db stamp 001_initial_jogos
flask db upgrade
```

Ao atualizar a aplicação, execute `flask db upgrade` antes de iniciá-la. A inicialização da aplicação não altera o schema automaticamente.

### Passo 4: Iniciar a aplicação
```bash
python run.py
```
Acesse no seu navegador: **[http://localhost:5000](http://localhost:5000)**

---

## 6. Testes Automatizados

Para rodar todos os testes de autenticação e CRUD de jogos:

```bash
pytest -v
```
