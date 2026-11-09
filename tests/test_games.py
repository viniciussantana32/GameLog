from datetime import date, datetime

from sqlalchemy.dialects.mysql import dialect as mysql_dialect

from app.extensions import db
from app.models.jogos import Jogo
from app.models.usuario import Usuario
from app.services.jogos_service import JogoService, _nulos_por_ultimo
from app.services.game_api_service import GameApiService


def test_home_page_status(client, monkeypatch):
    """Verifica se a página inicial carrega com status 200."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    response = client.get('/')
    assert response.status_code == 200
    assert b"Gamelog" in response.data


def test_listar_jogos_vazio(client):
    """Verifica se a página de listagem exibe o estado vazio quando não há registros."""
    response = client.get('/jogos')
    assert response.status_code == 200
    assert b"Nenhum jogo encontrado" in response.data or b"biblioteca" in response.data


def test_criar_jogo_valido(auth_client, app):
    """Testa o cadastro de um novo jogo com usuário autenticado."""
    dados = {
        'titulo': 'God of War Ragnarok',
        'plataforma': 'PlayStation 5',
        'genero': 'Ação e Aventura',
        'ano_lancamento': 2022,
        'data_zeramento': '2023-01-15',
        'tempo_jogado_horas': 45.0,
        'nota': 9.5,
        'dificuldade': 'Normal / Padrão',
        'observacoes': 'Continuação incrível com combate impecável.'
    }
    response = auth_client.post('/jogos/novo', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"God of War Ragnarok" in response.data

    with app.app_context():
        jogo = Jogo.query.filter_by(titulo='God of War Ragnarok').first()
        assert jogo is not None
        assert jogo.plataforma == 'PlayStation 5'
        assert jogo.nota == 9.5
        assert jogo.usuario_id is not None


def test_criar_jogo_em_andamento(auth_client, app):
    response = auth_client.post('/jogos/novo', data={
        'titulo': 'Jogo em andamento',
        'plataforma': 'PC',
        'status': 'jogando',
        'tempo_jogado_horas': '12.5',
        'nota': '8.5'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Jogo em andamento' in response.data
    with app.app_context():
        jogo = Jogo.query.filter_by(titulo='Jogo em andamento').first()
        assert jogo is not None
        assert jogo.status == 'jogando'
        assert jogo.tempo_jogado_horas == 12.5


def test_criar_jogo_invalido_sem_titulo(auth_client, app):
    """Testa validação de campo obrigatório (título ausente)."""
    dados = {
        'titulo': '',
        'plataforma': 'PC'
    }
    response = auth_client.post('/jogos/novo', data=dados, follow_redirects=True)
    assert response.status_code == 200
    assert b"O t\xc3\xadtulo do jogo \xc3\xa9 obrigat\xc3\xb3rio." in response.data


def test_detalhes_jogo(client, app, jogo_exemplo, monkeypatch):
    """Testa visualização detalhada de um jogo existente."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    GameApiService._game_details_cache.clear()
    response = client.get(f'/jogos/{jogo_exemplo}')
    assert response.status_code == 200
    assert b"The Witcher 3: Wild Hunt" in response.data
    assert b"RPG de A\xc3\xa7\xc3\xa3o" in response.data
    assert b"Minha experi\xc3\xaancia" in response.data
    assert b"Uma das melhores narrativas" not in response.data


def test_detalhes_jogo_exibe_avaliacao_do_proprietario(auth_client, jogo_exemplo, monkeypatch):
    """O proprietário visualiza a nota e as observações da própria avaliação."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    GameApiService._game_details_cache.clear()

    response = auth_client.get(f'/jogos/{jogo_exemplo}')

    assert response.status_code == 200
    assert b'10.0/10' in response.data
    assert b'Uma das melhores narrativas e ambienta\xc3\xa7\xc3\xb5es' in response.data
    assert b'Editar avalia\xc3\xa7\xc3\xa3o' in response.data


def test_detalhe_catalogo_com_dados_igdb_e_galeria(client, monkeypatch):
    """A ficha pública renderiza dados IGDB, avaliações e screenshots sem expor credenciais."""
    monkeypatch.setenv('IGDB_CLIENT_ID', 'test-client')
    monkeypatch.setenv('IGDB_CLIENT_SECRET', 'test-secret')
    GameApiService._game_details_cache.clear()

    def executar_query(query):
        assert 'artworks.image_id' in query
        assert 'screenshots.image_id' in query
        assert 'similar_games.cover.image_id' in query
        assert 'franchise.games.cover.image_id' in query
        assert 'collections.games.cover.image_id' in query
        return [{
            'id': 987654,
            'name': 'Jogo de Teste IGDB',
            'summary': 'Resumo público de teste.',
            'cover': {'image_id': 'cover-test'},
            'artworks': [
                {'image_id': 'portrait-art', 'width': 900, 'height': 1600},
                {'image_id': 'wide-small', 'width': 1280, 'height': 720},
                {'image_id': 'wide-large', 'width': 3840, 'height': 2160}
            ],
            'screenshots': [{'image_id': 'shot-test'}],
            'similar_games': [
                {
                    'id': 987654,
                    'name': 'Jogo de Teste IGDB',
                    'cover': {'image_id': 'current-cover'}
                },
                {
                    'id': 987655,
                    'name': 'Similar Teste',
                    'cover': {'image_id': 'similar-cover'},
                    'first_release_date': 1704067200
                },
                {
                    'id': 987655,
                    'name': 'Similar Teste',
                    'cover': {'image_id': 'duplicate-cover'}
                }
            ],
            'franchise': {
                'name': 'Franquia Teste',
                'games': [
                    {
                        'id': 987654,
                        'name': 'Jogo de Teste IGDB',
                        'cover': {'image_id': 'current-cover'}
                    },
                    {
                        'id': 987655,
                        'name': 'Similar Teste',
                        'cover': {'image_id': 'similar-cover'}
                    },
                    {
                        'id': 987656,
                        'name': 'Jogo da Franquia',
                        'cover': {'image_id': 'franchise-cover'},
                        'first_release_date': 1577836800
                    }
                ]
            },
            'collections': [{
                'name': 'Coleção Teste',
                'games': [
                    {
                        'id': 987656,
                        'name': 'Jogo da Franquia',
                        'cover': {'image_id': 'duplicate-franchise-cover'}
                    },
                    {
                        'id': 987657,
                        'name': 'Outro Jogo da Coleção',
                        'cover': {'image_id': 'collection-cover'},
                        'first_release_date': 1640995200
                    }
                ]
            }],
            'genres': [{'name': 'Aventura'}],
            'platforms': [{'name': 'PC'}],
            'involved_companies': [
                {'developer': True, 'publisher': False, 'company': {'name': 'Estúdio Teste'}},
                {'developer': False, 'publisher': True, 'company': {'name': 'Editora Teste'}}
            ],
            'first_release_date': 1704067200,
            'total_rating': 88.4,
            'total_rating_count': 123,
            'url': 'https://www.igdb.com/games/test'
        }]

    monkeypatch.setattr(GameApiService, '_executar_query_igdb', staticmethod(executar_query))
    response = client.get('/explorar/jogo/987654')

    assert response.status_code == 200
    assert b'Jogo de Teste IGDB' in response.data
    assert b'Est\xc3\xbadio Teste' in response.data
    assert b'Editora Teste' in response.data
    assert b'88.4' in response.data
    assert b'123 avalia\xc3\xa7\xc3\xb5es' in response.data
    assert b'2024-01-01' in response.data
    assert b'wide-large' in response.data
    assert b'portrait-art' not in response.data
    assert b'shot-test' in response.data
    assert b'gameGalleryDialog' in response.data
    assert b'Jogos semelhantes' in response.data
    assert b'Mais da franquia' in response.data
    assert b'Similar Teste' in response.data
    assert b'Jogo da Franquia' in response.data
    assert b'Outro Jogo da Cole\xc3\xa7\xc3\xa3o' in response.data
    assert b'href="/explorar/jogo/987655"' in response.data
    assert response.data.count(b'href="/explorar/jogo/987656"') == 1
    assert b'2024' in response.data
    assert b'test-secret' not in response.data


def test_detalhe_catalogo_fallback_sem_galeria(client, monkeypatch):
    """Jogos do fallback sem screenshots exibem uma ficha funcional sem capa quebrada."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    GameApiService._game_details_cache.clear()

    response = client.get('/explorar/jogo/1942')

    assert response.status_code == 200
    assert b'The Witcher 3: Wild Hunt' in response.data
    assert b'Ainda n\xc3\xa3o h\xc3\xa1 capturas de tela dispon\xc3\xadveis' in response.data
    assert b'gameGalleryDialog' not in response.data
    assert b'Jogos semelhantes' not in response.data
    assert b'Mais da franquia' not in response.data


def test_formatar_jogos_relacionados_limita_e_remove_repetidos():
    entries = [
        {
            'id': game_id,
            'name': f'Jogo relacionado {game_id}',
            'cover': {'image_id': f'cover-{game_id}'},
            'first_release_date': 1704067200
        }
        for game_id in range(1, 16)
    ]
    entries.extend([
        entries[0],
        {'id': 99, 'name': 'Sem capa'}
    ])

    games = GameApiService._formatar_jogos_relacionados(
        entries,
        jogo_atual_id=15,
        jogo_atual_titulo='Jogo relacionado 15',
        limite=12
    )

    assert len(games) == 12
    assert all(game['id'] != 15 for game in games)
    assert len({game['id'] for game in games}) == len(games)
    assert games[0]['year'] == 2024


def test_banner_seleciona_artwork_horizontal_de_maior_resolucao():
    """O banner IGDB ignora capas verticais e ordena artworks horizontais pela resolução."""
    details = GameApiService._formatar_detalhes_jogo({
        'id': 42,
        'name': 'Teste de Banner',
        'artworks': [
            {'image_id': 'portrait', 'width': 1200, 'height': 1800},
            {'image_id': 'landscape-hd', 'width': 1920, 'height': 1080},
            {'image_id': 'landscape-4k', 'width': 3840, 'height': 2160}
        ]
    })

    assert details['artworks'] == [
        'https://images.igdb.com/igdb/image/upload/t_1080p/landscape-4k.jpg',
        'https://images.igdb.com/igdb/image/upload/t_1080p/landscape-hd.jpg'
    ]


def test_detalhe_catalogo_inexistente_retorna_404(client, monkeypatch):
    """IDs sem dados IGDB nem fallback seguem a página 404 existente."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    GameApiService._game_details_cache.clear()

    response = client.get('/explorar/jogo/999999')

    assert response.status_code == 404


def test_detalhe_igdb_em_falha_usa_resumo_e_trata_imagens_ausentes(client, monkeypatch):
    """Falha na consulta de detalhes preserva dados da listagem e mostra placeholders."""
    monkeypatch.setenv('IGDB_CLIENT_ID', 'test-client')
    monkeypatch.setenv('IGDB_CLIENT_SECRET', 'test-secret')
    GameApiService._game_details_cache.clear()
    item = {
        'id': 987655,
        'name': 'Jogo sem imagens',
        'summary': 'Resumo da listagem.',
        'genres': [{'name': 'Aventura'}],
        'platforms': [{'name': 'PC'}],
        'total_rating': 81.5,
        'total_rating_count': 25,
        'url': 'https://www.igdb.com/games/no-images'
    }

    monkeypatch.setattr(
        GameApiService,
        '_executar_query_igdb',
        staticmethod(lambda query: [item])
    )
    assert GameApiService.listar_jogos(busca='Jogo sem imagens', limite=1)
    monkeypatch.setattr(
        GameApiService,
        '_executar_query_igdb',
        staticmethod(lambda query: None)
    )

    response = client.get('/explorar/jogo/987655')

    assert response.status_code == 200
    assert b'Jogo sem imagens' in response.data
    assert b'Resumo da listagem.' in response.data
    assert b'81.5' in response.data
    assert b'game-detail-cover-placeholder' in response.data
    assert b'Ainda n\xc3\xa3o h\xc3\xa1 capturas de tela dispon\xc3\xadveis' in response.data


def test_dados_pessoais_nao_sao_exibidos_ou_alterados_por_outro_usuario(
    app, auth_client, usuario_padrao
):
    """Outro usuário não pode visualizar, editar ou excluir a avaliação pessoal."""
    with app.app_context():
        outro_usuario = Usuario(
            nome='Outro Jogador',
            username='outrojogador',
            email='outro@teste.com'
        )
        outro_usuario.set_senha('senha123')
        db.session.add(outro_usuario)
        db.session.flush()
        jogo = Jogo(
            usuario_id=outro_usuario.id,
            titulo='Jogo Privado',
            plataforma='PC',
            nota=4.2,
            tempo_jogado_horas=18,
            observacoes='OBSERVACAO_PRIVADA'
        )
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    response = auth_client.get(f'/jogos/{jogo_id}')
    assert response.status_code == 200
    assert b'OBSERVACAO_PRIVADA' not in response.data
    assert b'4.2/10' not in response.data
    list_response = auth_client.get('/jogos?visao=todos')
    assert b'OBSERVACAO_PRIVADA' not in list_response.data

    auth_client.post(f'/jogos/{jogo_id}/excluir', follow_redirects=True)
    auth_client.post(f'/jogos/{jogo_id}/editar', data={
        'titulo': 'Tentativa de alteração',
        'plataforma': 'PC'
    }, follow_redirects=True)
    with app.app_context():
        registro = JogoService.obter_por_id(jogo_id)
        assert registro is not None
        assert registro.titulo == 'Jogo Privado'
        assert registro.observacoes == 'OBSERVACAO_PRIVADA'


def test_avaliar_jogo_local_reutiliza_formulario_existente(
    app, auth_client, usuario_padrao, monkeypatch
):
    """A ficha local preenche o formulário existente sem copiar dados pessoais de terceiros."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    with app.app_context():
        jogo_publico = Jogo(
            usuario_id=None,
            titulo='Jogo Local sem IGDB',
            plataforma='PC',
            genero='Aventura',
            ano_lancamento=2020,
            nota=8,
            observacoes='NOTA_DE_OUTRA_PESSOA'
        )
        db.session.add(jogo_publico)
        db.session.commit()
        jogo_id = jogo_publico.id

    detail_response = auth_client.get(f'/jogos/{jogo_id}')
    assert detail_response.status_code == 200
    assert b'NOTA_DE_OUTRA_PESSOA' not in detail_response.data
    assert b'Iniciar avalia\xc3\xa7\xc3\xa3o' in detail_response.data

    form_response = auth_client.get(f'/jogos/novo?origem={jogo_id}')
    assert form_response.status_code == 200
    assert b'value="Jogo Local sem IGDB"' in form_response.data
    assert b'origem=' in form_response.data

    save_response = auth_client.post(
        f'/jogos/novo?origem={jogo_id}',
        data={
            'titulo': 'Jogo Local sem IGDB',
            'plataforma': 'PC',
            'genero': 'Aventura',
            'ano_lancamento': '2020',
            'nota': '9',
            'observacoes': 'Minha própria avaliação.'
        },
        follow_redirects=True
    )
    assert save_response.status_code == 200
    assert b'Minha pr\xc3\xb3pria avalia\xc3\xa7\xc3\xa3o.' in save_response.data
    with app.app_context():
        minha_avaliacao = JogoService.obter_por_usuario_e_titulo(
            usuario_padrao,
            'Jogo Local sem IGDB'
        )
        assert minha_avaliacao is not None
        assert minha_avaliacao.observacoes == 'Minha própria avaliação.'
        assert minha_avaliacao.nota == 9


def test_media_gamelog_exige_tres_avaliacoes(app, usuario_padrao):
    """A média comunitária não aparece antes de atingir o mínimo de avaliações."""
    with app.app_context():
        outros_usuarios = [
            Usuario(nome=f'Jogador {index}', username=f'jogador{index}',
                    email=f'jogador{index}@teste.com')
            for index in (2, 3)
        ]
        for usuario in outros_usuarios:
            usuario.set_senha('senha123')
        db.session.add_all(outros_usuarios)
        db.session.flush()
        db.session.add_all([
            Jogo(usuario_id=usuario_padrao, titulo='Jogo da Comunidade', plataforma='PC', nota=8),
            Jogo(usuario_id=outros_usuarios[0].id, titulo='Jogo da Comunidade', plataforma='PC', nota=10)
        ])
        db.session.commit()
        assert JogoService.obter_avaliacao_global('Jogo da Comunidade') is None

        db.session.add(Jogo(usuario_id=outros_usuarios[1].id, titulo='Jogo da Comunidade', plataforma='PC', nota=9))
        db.session.commit()
        assert JogoService.obter_avaliacao_global('Jogo da Comunidade') == {
            'rating': 9.0,
            'count': 3
        }


def test_importar_catalogo_nao_duplica_avaliacao(auth_client, app, usuario_padrao, monkeypatch):
    """Ao iniciar uma avaliação já existente, retorna à ficha em vez de criar duplicata."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    with app.app_context():
        jogo = Jogo(
            usuario_id=usuario_padrao,
            titulo='The Witcher 3: Wild Hunt',
            plataforma='PC',
            nota=9
        )
        db.session.add(jogo)
        db.session.commit()
        jogo_id = jogo.id

    response = auth_client.get('/explorar/importar/1942')

    assert response.status_code == 302
    assert response.headers['Location'].endswith(f'/jogos/{jogo_id}')


def test_detalhes_jogo_inexistente(client):
    """Testa acesso a um ID inexistente retornando 404."""
    response = client.get('/jogos/99999')
    assert response.status_code == 404
    assert b"404" in response.data


def test_editar_jogo(auth_client, app, jogo_exemplo):
    """Testa atualização de dados de um jogo já cadastrado pelo usuário proprietário."""
    dados_atualizados = {
        'titulo': 'The Witcher 3: Complete Edition',
        'plataforma': 'PC',
        'genero': 'RPG',
        'ano_lancamento': 2015,
        'data_zeramento': '2023-05-20',
        'tempo_jogado_horas': 150.0,
        'nota': 10.0,
        'dificuldade': 'Extrema / Hardcore',
        'observacoes': 'Zerado novamente com as duas expansões fantásticas!'
    }
    response = auth_client.post(f'/jogos/{jogo_exemplo}/editar', data=dados_atualizados, follow_redirects=True)
    assert response.status_code == 200
    assert b"The Witcher 3: Complete Edition" in response.data

    with app.app_context():
        jogo = Jogo.query.get(jogo_exemplo)
        assert jogo.titulo == 'The Witcher 3: Complete Edition'
        assert jogo.tempo_jogado_horas == 150.0
        assert jogo.dificuldade == 'Extrema / Hardcore'


def test_excluir_jogo(auth_client, app, jogo_exemplo):
    """Testa exclusão de um registro no banco de dados por usuário com permissão."""
    response = auth_client.post(f'/jogos/{jogo_exemplo}/excluir', follow_redirects=True)
    assert response.status_code == 200
    assert b"exclu\xc3\xaddo com sucesso" in response.data

    with app.app_context():
        jogo = Jogo.query.get(jogo_exemplo)
        assert jogo is None


def test_busca_e_filtro(client, app, usuario_padrao):
    """Testa a funcionalidade de busca textual e filtragem por plataforma."""
    with app.app_context():
        j1 = Jogo(usuario_id=usuario_padrao, titulo='Cyberpunk 2077', plataforma='PC', genero='RPG', nota=9.0)
        j2 = Jogo(usuario_id=usuario_padrao, titulo='Super Mario Odyssey', plataforma='Nintendo Switch', genero='Plataforma', nota=10.0)
        j3 = Jogo(usuario_id=usuario_padrao, titulo='Halo Infinite', plataforma='Xbox Series X/S', genero='FPS', nota=8.0)
        from app.extensions import db
        db.session.add_all([j1, j2, j3])
        db.session.commit()

    # Busca textual
    resp_busca = client.get('/jogos?busca=Cyberpunk&visao=todos')
    assert b"Cyberpunk 2077" in resp_busca.data
    assert b"Super Mario Odyssey" not in resp_busca.data

    # Filtro por plataforma
    resp_filtro = client.get('/jogos?plataforma=Nintendo+Switch&visao=todos')
    assert b"Super Mario Odyssey" in resp_filtro.data
    assert b"Halo Infinite" not in resp_filtro.data


def test_service_estatisticas(app, jogo_exemplo, usuario_padrao):
    """Testa o cálculo de métricas estatísticas na camada de serviços filtrado por usuário."""
    with app.app_context():
        stats = JogoService.obter_estatisticas(usuario_id=usuario_padrao)
        assert stats['total_jogos'] == 1
        assert stats['media_nota'] == 10.0
        assert stats['total_horas'] == 120.5
        assert stats['plataforma_favorita'] == 'PC'


def test_dashboard_calcula_dados_apenas_do_usuario(app, usuario_padrao):
    with app.app_context():
        outro_usuario = Usuario(
            nome='Outro Jogador',
            username='outro-dashboard',
            email='outro-dashboard@teste.com'
        )
        outro_usuario.set_senha('senha123')
        db.session.add(outro_usuario)
        db.session.flush()
        db.session.add_all([
            Jogo(
                usuario_id=usuario_padrao,
                titulo='Aventura em andamento',
                plataforma='PC',
                status='jogando',
                tempo_jogado_horas=12.5,
                nota=8.0,
                data_criacao=datetime(2026, 1, 2)
            ),
            Jogo(
                usuario_id=usuario_padrao,
                titulo='Aventura concluída',
                plataforma='PC',
                status='zerado',
                data_zeramento=date(2025, 1, 1),
                tempo_jogado_horas=7.5,
                nota=10.0,
                data_criacao=datetime(2026, 1, 1)
            ),
            Jogo(
                usuario_id=usuario_padrao,
                titulo='Status ainda não informado',
                plataforma='PC',
                data_criacao=datetime(2025, 1, 1)
            ),
            Jogo(
                usuario_id=outro_usuario.id,
                titulo='Jogo privado de outra pessoa',
                plataforma='PC',
                status='jogando',
                tempo_jogado_horas=100,
                nota=10
            )
        ])
        db.session.commit()

        dashboard = JogoService.obter_dados_dashboard(usuario_padrao)

        assert dashboard['total_jogos'] == 3
        assert dashboard['jogos_zerados'] == 1
        assert dashboard['jogos_em_andamento'] == 1
        assert dashboard['total_horas'] == 20.0
        assert dashboard['media_nota'] == 9.0
        assert [jogo.titulo for jogo in dashboard['recentemente_adicionados']] == [
            'Aventura em andamento',
            'Aventura concluída',
            'Status ainda não informado'
        ]
        assert [jogo.titulo for jogo in dashboard['jogando']] == ['Aventura em andamento']
        assert [jogo.titulo for jogo in dashboard['melhores_avaliacoes']] == [
            'Aventura concluída',
            'Aventura em andamento'
        ]
        assert 'Jogo privado de outra pessoa' not in dashboard['titulos_biblioteca']


def test_home_renderiza_dashboard_pessoal_e_filtra_recomendacoes(
    app, auth_client, usuario_padrao, monkeypatch
):
    with app.app_context():
        db.session.add(Jogo(
            usuario_id=usuario_padrao,
            titulo='Jogo que já possuo',
            plataforma='PC',
            status='jogando',
            nota=9
        ))
        db.session.commit()

    monkeypatch.setattr(GameApiService, 'obter_imagens_por_titulo', lambda titulos: {})
    monkeypatch.setattr(GameApiService, 'listar_jogos', lambda **kwargs: [
        {'id': 100, 'title': 'Jogo que já possuo', 'thumbnail': 'owned.jpg'},
        {'id': 101, 'title': 'Descoberta IGDB', 'thumbnail': 'new.jpg',
         'genre': 'RPG', 'rating': 90, 'release_date': '2024-02-01'}
    ])
    response = auth_client.get('/')

    assert response.status_code == 200
    assert b'Continue jogando' in response.data
    assert b'Adicionados recentemente' in response.data
    assert b'Suas melhores avalia\xc3\xa7\xc3\xb5es' in response.data
    assert b'Descubra novos jogos' in response.data
    discovery_section = response.data.split(b'id="discoverGamesCarousel"')[-1]
    assert b'Jogo que j\xc3\xa1 possuo' not in discovery_section
    assert b'Descoberta IGDB' in discovery_section


def test_obter_imagens_por_titulo_consulta_artwork_em_lote(monkeypatch):
    monkeypatch.setenv('IGDB_CLIENT_ID', 'test-client')
    monkeypatch.setenv('IGDB_CLIENT_SECRET', 'test-secret')
    GameApiService._game_images_cache.clear()
    queries = []

    def executar_query(query):
        queries.append(query)
        return [{
            'name': 'Jogo com Arte',
            'cover': {'image_id': 'cover-id'},
            'artworks': [
                {'image_id': 'small-art', 'width': 1280, 'height': 720},
                {'image_id': 'large-art', 'width': 3840, 'height': 2160}
            ]
        }]

    monkeypatch.setattr(
        GameApiService,
        '_executar_query_igdb',
        staticmethod(executar_query)
    )
    images = GameApiService.obter_imagens_por_titulo([
        'Jogo com Arte',
        'Jogo com Arte'
    ])
    cached_images = GameApiService.obter_imagens_por_titulo(['Jogo com Arte'])

    assert len(queries) == 1
    assert 'artworks.image_id' in queries[0]
    assert images['Jogo com Arte']['cover'].endswith('/t_cover_big/cover-id.jpg')
    assert images['Jogo com Arte']['artwork'].endswith('/t_1080p/large-art.jpg')
    assert cached_images == images


def test_ultimos_jogos_coloca_datas_nulas_no_final(app, usuario_padrao):
    """O dashboard mantém jogos sem data depois dos que têm data de zeramento."""
    with app.app_context():
        db.session.add_all([
            Jogo(usuario_id=usuario_padrao, titulo='Sem data', plataforma='PC'),
            Jogo(usuario_id=usuario_padrao, titulo='Mais antigo', plataforma='PC',
                 data_zeramento=date(2023, 1, 1)),
            Jogo(usuario_id=usuario_padrao, titulo='Mais recente', plataforma='PC',
                 data_zeramento=date(2024, 1, 1)),
        ])
        db.session.commit()

        stats = JogoService.obter_estatisticas(usuario_id=usuario_padrao)

        assert [jogo.titulo for jogo in stats['ultimos_jogos']] == [
            'Mais recente', 'Mais antigo', 'Sem data'
        ]


def test_ordem_com_nulos_e_compativel_com_dialeto_mysql(app):
    """A ordenação sem valores não emite a sintaxe NULLS LAST."""
    with app.app_context():
        ordenacao = _nulos_por_ultimo(Jogo.data_zeramento, descendente=True)
        sql = str(
            Jogo.query.order_by(*ordenacao)
            .statement.compile(dialect=mysql_dialect())
        )

        assert 'NULLS LAST' not in sql.upper()
        assert 'CASE WHEN' in sql.upper()


def test_explorar_api_rota(client, monkeypatch):
    """Testa se a página de exploração da API pública/IGDB carrega com status 200."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    response = client.get('/explorar')
    assert response.status_code == 200
    assert b"IGDB" in response.data or b"Jogos" in response.data


def test_importar_da_api_get(auth_client, monkeypatch):
    """Testa se a rota de importar da API preenche os dados do jogo no formulário."""
    monkeypatch.delenv('IGDB_CLIENT_ID', raising=False)
    monkeypatch.delenv('IGDB_CLIENT_SECRET', raising=False)
    response = auth_client.get('/explorar/importar/1942')
    assert response.status_code == 200
    assert b"The Witcher 3" in response.data
