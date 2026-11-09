from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.services.jogos_service import JogoService
from app.services.game_api_service import GameApiService
from app.forms.jogos_forms import JogoForm, DeleteForm, PLATAFORMAS_CHOICES

jogos_bp = Blueprint('jogos', __name__)


@jogos_bp.route('/')
def index():
    """Página inicial com o dashboard pessoal e recomendações IGDB."""
    dashboard = {
        'total_jogos': 0,
        'jogos_zerados': 0,
        'jogos_em_andamento': 0,
        'total_horas': 0.0,
        'media_nota': 0.0,
        'recentemente_adicionados': [],
        'ultimo_jogo': None,
        'jogando': [],
        'melhores_avaliacoes': [],
        'titulos_biblioteca': []
    }
    try:
        usuario_id = current_user.id if current_user.is_authenticated else -1
        dashboard = JogoService.obter_dados_dashboard(usuario_id)
        titulos_imagens = [
            jogo.titulo
            for jogo in (
                dashboard['recentemente_adicionados']
                + dashboard['jogando']
                + dashboard['melhores_avaliacoes']
            )
        ]
        imagens_jogos = GameApiService.obter_imagens_por_titulo(titulos_imagens)
        recomendacoes_igdb = GameApiService.listar_jogos(
            ordenacao='popularity',
            limite=20
        )
        jogos_para_descobrir = GameApiService.filtrar_jogos_nao_cadastrados(
            recomendacoes_igdb,
            dashboard['titulos_biblioteca'],
            limite=8
        )
        delete_form = DeleteForm()
        return render_template(
            'index.html',
            dashboard=dashboard,
            imagens_jogos=imagens_jogos,
            jogos_para_descobrir=jogos_para_descobrir,
            delete_form=delete_form
        )
    except Exception as e:
        flash(f'Erro ao carregar dados do dashboard: {str(e)}', 'danger')
        return render_template(
            'index.html',
            dashboard=dashboard,
            imagens_jogos={},
            jogos_para_descobrir=[],
            delete_form=DeleteForm()
        )


@jogos_bp.route('/jogos')
def listar():
    """Listagem completa dos jogos zerados com busca e filtros."""
    busca = request.args.get('busca', '').strip()
    plataforma = request.args.get('plataforma', '').strip()
    ordenacao = request.args.get('ordenacao', 'recente').strip()
    visao = request.args.get('visao', 'meus' if current_user.is_authenticated else 'todos')

    usuario_id = current_user.id if (current_user.is_authenticated and visao == 'meus') else None

    try:
        jogos = JogoService.listar_jogos(
            busca=busca,
            plataforma=plataforma,
            ordenacao=ordenacao,
            usuario_id=usuario_id
        )
    except Exception as e:
        flash(f'Falha ao consultar banco de dados JOGOSSALVOS: {str(e)}', 'danger')
        jogos = []

    delete_form = DeleteForm()
    capas_jogos = GameApiService.obter_capas_por_titulo([jogo.titulo for jogo in jogos])
    return render_template(
        'JOGOSBASE/list.html',
        jogos=jogos,
        busca=busca,
        plataforma_selecionada=plataforma,
        ordenacao_selecionada=ordenacao,
        plataformas_opcoes=PLATAFORMAS_CHOICES,
        delete_form=delete_form,
        visao=visao,
        capas_jogos=capas_jogos
    )


@jogos_bp.route('/jogos/novo', methods=['GET', 'POST'])
@login_required
def criar():
    """Cadastro de um novo jogo zerado vinculado ao usuário autenticado."""
    form = JogoForm()
    origem_id = request.args.get('origem', type=int)
    jogo_origem = JogoService.obter_por_id_ou_404(origem_id) if origem_id else None

    if jogo_origem and request.method == 'GET':
        jogo_existente = JogoService.obter_por_usuario_e_titulo(current_user.id, jogo_origem.titulo)
        if jogo_existente:
            return redirect(url_for('jogos.detalhe', id=jogo_existente.id))
        form.titulo.data = jogo_origem.titulo
        form.plataforma.data = jogo_origem.plataforma
        form.genero.data = jogo_origem.genero or ''
        form.ano_lancamento.data = jogo_origem.ano_lancamento

    if form.validate_on_submit():
        try:
            jogo_existente = JogoService.obter_por_usuario_e_titulo(current_user.id, form.titulo.data)
            if jogo_existente:
                flash('Você já possui uma avaliação para esse jogo.', 'info')
                return redirect(url_for('jogos.detalhe', id=jogo_existente.id))
            novo_jogo = JogoService.criar_jogo(form.data, usuario_id=current_user.id)
            flash(f'O jogo "{novo_jogo.titulo}" foi cadastrado com sucesso!', 'success')
            return redirect(url_for('jogos.detalhe', id=novo_jogo.id))
        except Exception as e:
            flash(f'Erro ao salvar no banco de dados JOGOSSALVOS: {str(e)}', 'danger')

    return render_template('JOGOSBASE/create.html', form=form)


@jogos_bp.route('/jogos/<int:id>')
def detalhe(id):
    """Ficha pública do jogo, com dados pessoais visíveis apenas ao proprietário."""
    jogo = JogoService.obter_por_id_ou_404(id)
    dados_jogo = GameApiService.obter_detalhes_por_titulo(jogo.titulo) or {
        'id': None,
        'title': jogo.titulo,
        'short_description': None,
        'thumbnail': None,
        'cover': None,
        'artworks': [],
        'screenshots': [],
        'game_url': None,
        'genre': jogo.genero,
        'platform': jogo.plataforma,
        'release_date': None,
        'rating': None,
        'rating_count': None,
        'developer': None,
        'publisher': None,
        'similar_games': [],
        'franchise_games': []
    }
    genero_igdb = dados_jogo.get('genre')
    dados_jogo['genre'] = jogo.genero or genero_igdb
    if genero_igdb and genero_igdb != dados_jogo['genre']:
        dados_jogo['igdb_genre'] = genero_igdb
    dados_jogo['platform'] = dados_jogo.get('platform') or jogo.plataforma
    ano_lancamento = jogo.ano_lancamento
    if dados_jogo.get('release_date'):
        ano_lancamento = int(dados_jogo['release_date'][:4])

    avaliacao_pessoal = None
    if current_user.is_authenticated:
        avaliacao_pessoal = JogoService.obter_por_usuario_e_titulo(
            current_user.id,
            dados_jogo.get('title') or jogo.titulo
        )

    titulo_jogo = dados_jogo.get('title') or jogo.titulo
    avaliacao_comunidade = JogoService.obter_avaliacao_global(titulo_jogo)
    if dados_jogo.get('id'):
        iniciar_avaliacao_url = url_for('jogos.importar_da_api', game_id=dados_jogo['id'])
    else:
        iniciar_avaliacao_url = url_for('jogos.criar', origem=jogo.id)
    if not current_user.is_authenticated:
        iniciar_avaliacao_url = url_for('auth.login', next=iniciar_avaliacao_url)

    delete_form = DeleteForm()
    return render_template(
        'JOGOSBASE/detail.html',
        jogo=jogo,
        dados_jogo=dados_jogo,
        ano_lancamento=ano_lancamento,
        avaliacao_pessoal=avaliacao_pessoal,
        avaliacao_comunidade=avaliacao_comunidade,
        pode_editar=JogoService.usuario_pode_modificar(avaliacao_pessoal, current_user),
        iniciar_avaliacao_url=iniciar_avaliacao_url,
        voltar_url=url_for('jogos.listar'),
        delete_form=delete_form,
        jogos_semelhantes=dados_jogo.get('similar_games') or [],
        jogos_franquia=dados_jogo.get('franchise_games') or []
    )


@jogos_bp.route('/explorar/jogo/<int:game_id>')
def detalhe_catalogo(game_id):
    """Ficha de um jogo IGDB encontrado no catálogo, com experiência pessoal opcional."""
    dados_jogo = GameApiService.obter_detalhes_por_id(game_id)
    if not dados_jogo:
        abort(404)

    avaliacao_pessoal = None
    if current_user.is_authenticated:
        avaliacao_pessoal = JogoService.obter_por_usuario_e_titulo(
            current_user.id,
            dados_jogo['title']
        )

    avaliacao_comunidade = JogoService.obter_avaliacao_global(dados_jogo['title'])
    iniciar_avaliacao_url = url_for('jogos.importar_da_api', game_id=game_id)
    if not current_user.is_authenticated:
        iniciar_avaliacao_url = url_for('auth.login', next=iniciar_avaliacao_url)

    return render_template(
        'JOGOSBASE/detail.html',
        jogo=None,
        dados_jogo=dados_jogo,
        ano_lancamento=(int(dados_jogo['release_date'][:4]) if dados_jogo.get('release_date') else None),
        avaliacao_pessoal=avaliacao_pessoal,
        avaliacao_comunidade=avaliacao_comunidade,
        pode_editar=JogoService.usuario_pode_modificar(avaliacao_pessoal, current_user),
        iniciar_avaliacao_url=iniciar_avaliacao_url,
        voltar_url=url_for('jogos.explorar_api'),
        delete_form=DeleteForm(),
        jogos_semelhantes=dados_jogo.get('similar_games') or [],
        jogos_franquia=dados_jogo.get('franchise_games') or []
    )


@jogos_bp.route('/jogos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edição da avaliação pessoal apenas pelo usuário proprietário."""
    jogo = JogoService.obter_por_id_ou_404(id)

    if not JogoService.usuario_pode_modificar(jogo, current_user):
        flash('Você não tem permissão para editar este jogo.', 'danger')
        return redirect(url_for('jogos.detalhe', id=jogo.id))

    form = JogoForm(obj=jogo)

    if form.validate_on_submit():
        try:
            JogoService.atualizar_jogo(jogo, form.data)
            flash(f'As informações de "{jogo.titulo}" foram atualizadas com sucesso!', 'success')
            return redirect(url_for('jogos.detalhe', id=jogo.id))
        except Exception as e:
            flash(f'Erro ao atualizar o registro: {str(e)}', 'danger')

    return render_template('JOGOSBASE/edit.html', form=form, jogo=jogo)


@jogos_bp.route('/jogos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Exclusão de um registro com proteção CSRF e validação de permissão."""
    form = DeleteForm()

    if form.validate_on_submit():
        jogo = JogoService.obter_por_id(id)
        if not jogo:
            flash('Jogo não encontrado ou já foi excluído.', 'warning')
            return redirect(url_for('jogos.listar'))

        if not JogoService.usuario_pode_modificar(jogo, current_user):
            flash('Você não tem permissão para excluir este jogo.', 'danger')
            return redirect(url_for('jogos.detalhe', id=jogo.id))

        titulo = jogo.titulo
        try:
            JogoService.excluir_jogo(jogo)
            flash(f'O jogo "{titulo}" foi excluído com sucesso do banco de dados.', 'success')
        except Exception as e:
            flash(f'Erro ao excluir registro: {str(e)}', 'danger')
    else:
        flash('Falha na validação de segurança (CSRF) para exclusão.', 'danger')

    return redirect(url_for('jogos.listar'))


# ==============================================================================
# Rotas da API Pública de Jogos (FreeToGame)
# ==============================================================================

@jogos_bp.route('/explorar')
def explorar_api():
    """Catálogo de jogos alimentado automaticamente pela API pública."""
    busca = request.args.get('busca', '').strip()
    categoria = request.args.get('categoria', '').strip()
    plataforma = request.args.get('plataforma', '').strip()
    ordenacao = request.args.get('ordenacao', '').strip()
    limite = 30
    offset = max(request.args.get('offset', 0, type=int), 0)

    jogos_api = GameApiService.listar_jogos(
        categoria=categoria,
        plataforma=plataforma,
        busca=busca,
        ordenacao=ordenacao,
        limite=limite,
        offset=offset
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(
            html=render_template('api/_game_cards.html', jogos_api=jogos_api),
            count=len(jogos_api),
            has_more=len(jogos_api) == limite
        )

    categorias_disponiveis = [
        ('shooter', 'Shooter / Tiro'),
        ('action-rpg', 'RPG de Ação'),
        ('mmorpg', 'MMORPG'),
        ('battle-royale', 'Battle Royale'),
        ('strategy', 'Estratégia'),
        ('moba', 'MOBA'),
        ('sports', 'Esportes'),
        ('racing', 'Corrida'),
        ('fighting', 'Luta')
    ]

    return render_template(
        'api/explorar.html',
        jogos_api=jogos_api,
        busca=busca,
        categoria_selecionada=categoria,
        plataforma_selecionada=plataforma,
        ordenacao_selecionada=ordenacao,
        offset=offset,
        categorias_disponiveis=categorias_disponiveis
    )


@jogos_bp.route('/explorar/importar/<int:game_id>', methods=['GET', 'POST'])
@login_required
def importar_da_api(game_id):
    """Inicia a avaliação de um jogo IGDB pelo formulário de cadastro existente."""
    info_jogo = GameApiService.obter_jogo_por_id(game_id)
    if not info_jogo:
        flash('Jogo não encontrado na API pública.', 'warning')
        return redirect(url_for('jogos.explorar_api'))

    jogo_existente = JogoService.obter_por_usuario_e_titulo(current_user.id, info_jogo.get('title'))
    if jogo_existente:
        flash('Você já possui uma avaliação para esse jogo.', 'info')
        return redirect(url_for('jogos.detalhe', id=jogo_existente.id))

    form = JogoForm()

    if request.method == 'GET':
        form.titulo.data = info_jogo.get('title', '')
        
        # Mapeia a plataforma
        plat = info_jogo.get('platform', '').lower()
        if 'pc' in plat:
            form.plataforma.data = 'PC'
        elif 'playstation' in plat or 'ps5' in plat or 'ps4' in plat:
            form.plataforma.data = 'PlayStation 5'
        elif 'xbox' in plat:
            form.plataforma.data = 'Xbox Series X/S'
        elif 'switch' in plat or 'nintendo' in plat:
            form.plataforma.data = 'Nintendo Switch'
        else:
            form.plataforma.data = 'Outra'

        form.genero.data = info_jogo.get('genre', '')
        
        # Extrai o ano da data de lançamento
        release_date = info_jogo.get('release_date')
        if release_date:
            try:
                ano = int(release_date.split('-')[0])
                form.ano_lancamento.data = ano
            except Exception:
                pass

    if form.validate_on_submit():
        try:
            jogo_existente = JogoService.obter_por_usuario_e_titulo(current_user.id, form.titulo.data)
            if jogo_existente:
                flash('Você já possui uma avaliação para esse jogo.', 'info')
                return redirect(url_for('jogos.detalhe', id=jogo_existente.id))
            novo_jogo = JogoService.criar_jogo(form.data, usuario_id=current_user.id)
            flash(f'O jogo "{novo_jogo.titulo}" foi importado da API e salvo com sucesso!', 'success')
            return redirect(url_for('jogos.detalhe', id=novo_jogo.id))
        except Exception as e:
            flash(f'Erro ao salvar no banco de dados JOGOSSALVOS: {str(e)}', 'danger')

    return render_template('JOGOSBASE/create.html', form=form, jogo_importado=info_jogo)
