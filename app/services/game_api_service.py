import os
import time
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import unicodedata

logger = logging.getLogger(__name__)

# Fallback com dados oficiais da base do IGDB para exibição imediata
IGDB_GAMES_FALLBACK = [
    {
        "id": 1942,
        "title": "The Witcher 3: Wild Hunt",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1r7f.jpg",
        "short_description": "RPG de ação em mundo aberto focado em narrativa, onde você assume o papel de Geralt de Rívia, um caçador de monstros em busca da Criança da Profecia.",
        "game_url": "https://www.igdb.com/games/the-witcher-3-wild-hunt",
        "genre": "Role-playing (RPG)",
        "platform": "PC, PlayStation, Xbox",
        "release_date": "2015-05-19",
        "rating": 93.0
    },
    {
        "id": 119133,
        "title": "Elden Ring",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg",
        "short_description": "Um RPG de ação e fantasia das mentes de Hidetaka Miyazaki e George R. R. Martin pelas Terras Intermédias.",
        "game_url": "https://www.igdb.com/games/elden-ring",
        "genre": "RPG / Ação",
        "platform": "PC, PlayStation, Xbox",
        "release_date": "2022-02-25",
        "rating": 95.0
    },
    {
        "id": 112875,
        "title": "God of War Ragnarök",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co5s5v.jpg",
        "short_description": "Kratos e Atreus embarcam em uma jornada mítica pelos Nove Reinos nórdicos em busca de respostas antes da batalha final profetizada.",
        "game_url": "https://www.igdb.com/games/god-of-war-ragnarok",
        "genre": "Aventura / Hack and slash",
        "platform": "PlayStation, PC",
        "release_date": "2022-11-09",
        "rating": 94.0
    },
    {
        "id": 1020,
        "title": "Grand Theft Auto V",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1qcw.jpg",
        "short_description": "Quando um jovem malandro de rua, um ladrão de bancos aposentado e um psicopata aterrorizante entram em cena, eles devem realizar golpes perigosos em Los Santos.",
        "game_url": "https://www.igdb.com/games/grand-theft-auto-v",
        "genre": "Mundo Aberto / Ação",
        "platform": "PC, PlayStation, Xbox",
        "release_date": "2013-09-17",
        "rating": 91.0
    },
    {
        "id": 25076,
        "title": "Red Dead Redemption 2",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1q1f.jpg",
        "short_description": "América, 1899. Arthur Morgan e a gangue Van der Linde são forçados a fugir pelo vasto e acidentado coração dos Estados Unidos.",
        "game_url": "https://www.igdb.com/games/red-dead-redemption-2",
        "genre": "Mundo Aberto / Tiro",
        "platform": "PC, PlayStation, Xbox",
        "release_date": "2018-10-26",
        "rating": 96.0
    },
    {
        "id": 125174,
        "title": "Baldur's Gate 3",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co670h.jpg",
        "short_description": "RPG de última geração ambientado no universo de Dungeons & Dragons, onde suas escolhas moldam a narrativa e o destino dos Reinos Esquecidos.",
        "game_url": "https://www.igdb.com/games/baldurs-gate-3",
        "genre": "RPG Tático",
        "platform": "PC, PlayStation, Xbox",
        "release_date": "2023-08-03",
        "rating": 96.0
    },
    {
        "id": 1877,
        "title": "Cyberpunk 2077",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co2mdf.jpg",
        "short_description": "RPG de ação e aventura em mundo aberto ambientado na megalópole futurista de Night City, obcecada por poder, glamour e biomodificações.",
        "game_url": "https://www.igdb.com/games/cyberpunk-2077",
        "genre": "RPG / Sci-Fi",
        "platform": "PC, PlayStation, Xbox",
        "release_date": "2020-12-10",
        "rating": 86.0
    },
    {
        "id": 119277,
        "title": "The Legend of Zelda: Tears of the Kingdom",
        "thumbnail": "https://images.igdb.com/igdb/image/upload/t_cover_big/co5vmg.jpg",
        "short_description": "Uma aventura épica pelas terras e céus de Hyrule, onde a imaginação do jogador guia a exploração.",
        "game_url": "https://www.igdb.com/games/the-legend-of-zelda-tears-of-the-kingdom",
        "genre": "Aventura / RPG",
        "platform": "Nintendo Switch",
        "release_date": "2023-05-12",
        "rating": 95.0
    }
]


class GameApiService:
    """
    Serviço de integração oficial com a API do IGDB (Internet Game Database via Twitch Developer).
    Permite busca, listagem de jogos mais jogados, lançamentos e importação direta para o banco JOGOSSALVOS.
    """
    IGDB_URL = "https://api.igdb.com/v4/games"
    TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"

    _cached_token = None
    _token_expires_at = 0
    _game_details_cache = {}
    _game_details_cache_ttl = 300
    _game_images_cache = {}

    @staticmethod
    def _normalizar_titulo(titulo):
        return unicodedata.normalize('NFKC', titulo or '').strip().casefold()

    @staticmethod
    def _escapar_busca(busca):
        return busca.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')

    @staticmethod
    def _url_imagem(image_id, tamanho):
        if not image_id:
            return None
        return f"https://images.igdb.com/igdb/image/upload/t_{tamanho}/{image_id}.jpg"

    @classmethod
    def _obter_cache_detalhes(cls, cache_key, exige_completo=False):
        cached = cls._game_details_cache.get(cache_key)
        if (
            cached
            and time.time() - cached['cached_at'] < cls._game_details_cache_ttl
            and (not exige_completo or cached['complete'])
        ):
            return cached['game']
        if cached and time.time() - cached['cached_at'] >= cls._game_details_cache_ttl:
            del cls._game_details_cache[cache_key]
        return None

    @classmethod
    def _guardar_cache_detalhes(cls, cache_key, game, completo=True):
        if len(cls._game_details_cache) >= 128:
            oldest_key = min(
                cls._game_details_cache,
                key=lambda key: cls._game_details_cache[key]['cached_at']
            )
            del cls._game_details_cache[oldest_key]
        cls._game_details_cache[cache_key] = {
            'cached_at': time.time(),
            'game': game,
            'complete': completo
        }

    @classmethod
    def _cachear_resultados_resumidos(cls, resultados, jogos):
        for item, jogo in zip(resultados, jogos):
            cache_key = ('id', jogo.get('id'))
            if not jogo.get('id') or cls._obter_cache_detalhes(cache_key):
                continue
            resumo = dict(jogo)
            resumo.update({
                'cover': jogo.get('thumbnail'),
                'artworks': [],
                'screenshots': [],
                'developer': None,
                'publisher': None,
                'rating_count': item.get('total_rating_count') or None
            })
            cls._guardar_cache_detalhes(cache_key, resumo, completo=False)

    @classmethod
    def _obter_token(cls):
        """Obtém ou reutiliza o Bearer Token OAuth2 da Twitch Developer."""
        agora = time.time()
        if cls._cached_token and agora < (cls._token_expires_at - 60):
            return cls._cached_token

        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()

        if not client_id or not client_secret:
            return None

        try:
            import requests
            resp = requests.post(
                cls.TWITCH_TOKEN_URL,
                params={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'grant_type': 'client_credentials'
                },
                timeout=5
            )
            if resp.status_code == 200:
                dados = resp.json()
                cls._cached_token = dados.get('access_token')
                cls._token_expires_at = agora + dados.get('expires_in', 3600)
                return cls._cached_token
        except ImportError:
            # Fallback nativo urllib
            try:
                data = urllib.parse.urlencode({
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'grant_type': 'client_credentials'
                }).encode('utf-8')
                req = urllib.request.Request(cls.TWITCH_TOKEN_URL, data=data, method='POST')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        dados = json.loads(resp.read().decode('utf-8'))
                        cls._cached_token = dados.get('access_token')
                        cls._token_expires_at = agora + dados.get('expires_in', 3600)
                        return cls._cached_token
            except Exception as e:
                logger.warning(f"Erro ao obter token IGDB via urllib: {e}")
        except Exception as e:
            logger.warning(f"Erro ao obter token IGDB via requests: {e}")

        return None

    @classmethod
    def _executar_query_igdb(cls, query_text):
        """Executa uma query no endpoint da IGDB no formato Apicalypse."""
        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        token = cls._obter_token()

        if not client_id or not token:
            return None

        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

        try:
            import requests
            resp = requests.post(cls.IGDB_URL, headers=headers, data=query_text.encode('utf-8'), timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except ImportError:
            try:
                req = urllib.request.Request(cls.IGDB_URL, data=query_text.encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                logger.warning(f"Falha na query IGDB via urllib: {e}")
        except Exception as e:
            logger.warning(f"Falha na query IGDB via requests: {e}")

        return None

    @classmethod
    def _formatar_jogo(cls, item):
        """Formata um objeto de jogo retornado pela API da IGDB para o padrão do Meus Jogos."""
        image_id = None
        if item.get('cover') and isinstance(item['cover'], dict):
            image_id = item['cover'].get('image_id')

        thumbnail = cls._url_imagem(image_id, 'cover_big')

        genres = item.get('genres') or []
        genero = genres[0]['name'] if genres and isinstance(genres[0], dict) else 'Gamer'

        platforms = item.get('platforms') or []
        if platforms and isinstance(platforms[0], dict):
            plataformas_str = ", ".join([p.get('name', '') for p in platforms[:2]])
        else:
            plataformas_str = "Multiplataforma"

        data_lancamento = None
        if item.get('first_release_date'):
            try:
                data_lancamento = datetime.fromtimestamp(
                    item['first_release_date'],
                    timezone.utc
                ).strftime('%Y-%m-%d')
            except Exception:
                pass

        return {
            "id": item.get('id'),
            "title": item.get('name'),
            "thumbnail": thumbnail,
            "short_description": item.get('summary', 'Sem descrição detalhada cadastrada no IGDB.'),
            "game_url": item.get('url', f"https://www.igdb.com/games/{item.get('id')}"),
            "genre": genero,
            "platform": plataformas_str,
            "release_date": data_lancamento,
            "rating": round(float(item.get('total_rating', 0)), 1) if item.get('total_rating') else None,
            "rating_count": item.get('total_rating_count') or None
        }

    @classmethod
    def _formatar_detalhes_jogo(cls, item):
        jogo = cls._formatar_jogo(item)
        cover = item.get('cover') if isinstance(item.get('cover'), dict) else {}
        genres = [
            entry.get('name')
            for entry in item.get('genres') or []
            if isinstance(entry, dict) and entry.get('name')
        ]
        platforms = [
            entry.get('name')
            for entry in item.get('platforms') or []
            if isinstance(entry, dict) and entry.get('name')
        ]
        companies = item.get('involved_companies') or []
        developers = [
            entry.get('company', {}).get('name')
            for entry in companies
            if isinstance(entry, dict)
            and entry.get('developer')
            and isinstance(entry.get('company'), dict)
        ]
        publishers = [
            entry.get('company', {}).get('name')
            for entry in companies
            if isinstance(entry, dict)
            and entry.get('publisher')
            and isinstance(entry.get('company'), dict)
        ]
        horizontal_artworks = [
            entry
            for entry in item.get('artworks') or []
            if (
                isinstance(entry, dict)
                and entry.get('image_id')
                and isinstance(entry.get('width'), int)
                and isinstance(entry.get('height'), int)
                and entry['width'] > entry['height']
            )
        ]
        horizontal_artworks.sort(
            key=lambda entry: entry['width'] * entry['height'],
            reverse=True
        )
        artworks = [
            cls._url_imagem(entry['image_id'], '1080p')
            for entry in horizontal_artworks[:5]
        ]
        screenshots = [
            cls._url_imagem(entry.get('image_id'), 'screenshot_big')
            for entry in item.get('screenshots') or []
            if isinstance(entry, dict) and entry.get('image_id')
        ][:12]
        similar_games = cls._formatar_jogos_relacionados(
            item.get('similar_games'),
            jogo.get('id'),
            jogo.get('title')
        )
        franchise = item.get('franchise')
        if isinstance(franchise, list):
            franchise = franchise[0] if franchise else {}
        franchise_games = []
        if isinstance(franchise, dict):
            franchise_games.extend(franchise.get('games') or [])
        collections = item.get('collections') or []
        if isinstance(collections, dict):
            collections = [collections]
        for collection in collections:
            if isinstance(collection, dict):
                franchise_games.extend(collection.get('games') or [])

        franchise_games = cls._formatar_jogos_relacionados(
            franchise_games,
            jogo.get('id'),
            jogo.get('title'),
            excluded_ids={game['id'] for game in similar_games},
            excluded_titles={game['title'] for game in similar_games}
        )
        total_rating = item.get('total_rating')
        total_rating_count = item.get('total_rating_count')

        jogo.update({
            'cover': cls._url_imagem(cover.get('image_id'), 'cover_big'),
            'artworks': artworks,
            'screenshots': screenshots,
            'genre': ', '.join(dict.fromkeys(genres)) or jogo['genre'],
            'platform': ', '.join(dict.fromkeys(platforms)) or jogo['platform'],
            'developer': ', '.join(dict.fromkeys(developers)) or None,
            'publisher': ', '.join(dict.fromkeys(publishers)) or None,
            'rating': round(float(total_rating), 1) if total_rating is not None else None,
            'rating_count': total_rating_count if total_rating_count else None,
            'similar_games': similar_games,
            'franchise_games': franchise_games
        })
        if not jogo['thumbnail']:
            jogo['thumbnail'] = jogo['cover']
        return jogo

    @classmethod
    def _formatar_jogos_relacionados(
        cls,
        entries,
        jogo_atual_id=None,
        jogo_atual_titulo=None,
        excluded_ids=None,
        excluded_titles=None,
        limite=12
    ):
        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            return []

        jogos = []
        seen_ids = set(excluded_ids or ())
        seen_titles = {
            cls._normalizar_titulo(title)
            for title in (excluded_titles or ())
        }
        if jogo_atual_titulo:
            seen_titles.add(cls._normalizar_titulo(jogo_atual_titulo))
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            game_id = entry.get('id')
            title = entry.get('name') or entry.get('title')
            cover = entry.get('cover') if isinstance(entry.get('cover'), dict) else {}
            image_url = cls._url_imagem(cover.get('image_id'), 'cover_big')
            normalized_title = cls._normalizar_titulo(title)
            if (
                not isinstance(game_id, int)
                or game_id == jogo_atual_id
                or not title
                or not image_url
                or game_id in seen_ids
                or normalized_title in seen_titles
            ):
                continue

            release_date = entry.get('first_release_date')
            try:
                year = datetime.fromtimestamp(release_date, timezone.utc).year if release_date else None
            except (OverflowError, OSError, TypeError, ValueError):
                year = None

            jogos.append({
                'id': game_id,
                'title': title,
                'cover': image_url,
                'year': year
            })
            seen_ids.add(game_id)
            seen_titles.add(normalized_title)
            if len(jogos) >= limite:
                break
        return jogos

    @classmethod
    def _formatar_detalhes_fallback(cls, jogo):
        details = dict(jogo)
        details.update({
            'cover': jogo.get('thumbnail'),
            'artworks': [],
            'screenshots': [],
            'developer': None,
            'publisher': None,
            'rating_count': None,
            'similar_games': [],
            'franchise_games': []
        })
        return details

    @classmethod
    def listar_jogos(cls, categoria=None, plataforma=None, busca=None, ordenacao=None, limite=24, offset=0):
        """
        Consulta jogos no IGDB. Caso as credenciais não estejam configuradas,
        usa a seleção com capas e títulos do IGDB como fallback seguro.
        """
        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()

        # Se o usuário configurou as chaves do IGDB, faz a busca online
        if client_id and client_secret:
            timestamp_agora = int(time.time())

            if busca and busca.strip():
                # Busca textual na IGDB
                busca_segura = cls._escapar_busca(busca.strip())
                query = f'''
                    search "{busca_segura}";
                    fields id, name, summary, cover.image_id, genres.name, platforms.name, first_release_date, total_rating, total_rating_count, url;
                    where cover != null;
                    limit {limite};
                    offset {offset};
                '''
            elif ordenacao == 'release-date':
                # Recém lançados
                query = f'''
                    fields id, name, summary, cover.image_id, genres.name, platforms.name, first_release_date, total_rating, total_rating_count, url;
                    where cover != null & first_release_date != null & first_release_date <= {timestamp_agora};
                    sort first_release_date desc;
                    limit {limite};
                    offset {offset};
                '''
            else:
                # Mais populares / mais bem avaliados (Padrão)
                query = f'''
                    fields id, name, summary, cover.image_id, genres.name, platforms.name, first_release_date, total_rating, total_rating_count, url;
                    where cover != null & total_rating_count != null;
                    sort total_rating_count desc;
                    limit {limite};
                    offset {offset};
                '''

            resultados = cls._executar_query_igdb(query)
            if isinstance(resultados, list) and (resultados or offset > 0):
                jogos = [cls._formatar_jogo(item) for item in resultados]
                cls._cachear_resultados_resumidos(resultados, jogos)
                return jogos

        # Fallback local se chaves não preenchidas ou erro de rede
        dados = IGDB_GAMES_FALLBACK

        if busca and busca.strip():
            termo = busca.strip().lower()
            dados = [
                j for j in dados
                if termo in j.get("title", "").lower()
                or termo in j.get("genre", "").lower()
                or termo in j.get("short_description", "").lower()
            ]

        return dados[offset:offset + limite]

    @classmethod
    def obter_capas_por_titulo(cls, titulos):
        """Obtém capas IGDB para um conjunto de títulos sem fazer uma chamada por jogo."""
        titulos_unicos = list(dict.fromkeys(titulo.strip() for titulo in titulos if titulo and titulo.strip()))
        if not titulos_unicos:
            return {}

        capas = {}
        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()
        if client_id and client_secret:
            clausulas = [
                f'name = "{cls._escapar_busca(titulo)}"'
                for titulo in titulos_unicos[:100]
            ]
            query = f'''
                fields name, cover.image_id;
                where (cover != null | artworks != null) & ({' | '.join(clausulas)});
                limit {len(clausulas)};
            '''
            resultados = cls._executar_query_igdb(query)
            if isinstance(resultados, list):
                for item in resultados:
                    cover = item.get('cover') if isinstance(item.get('cover'), dict) else {}
                    image_url = cls._url_imagem(cover.get('image_id'), 'cover_big')
                    if item.get('name') and image_url:
                        capas[cls._normalizar_titulo(item['name'])] = image_url

        for jogo in IGDB_GAMES_FALLBACK:
            titulo_normalizado = cls._normalizar_titulo(jogo.get('title'))
            if titulo_normalizado in {
                cls._normalizar_titulo(titulo)
                for titulo in titulos_unicos
            }:
                capas.setdefault(titulo_normalizado, jogo.get('thumbnail'))

        return {
            titulo: capas[cls._normalizar_titulo(titulo)]
            for titulo in titulos_unicos
            if cls._normalizar_titulo(titulo) in capas
        }

    @classmethod
    def obter_imagens_por_titulo(cls, titulos):
        """Consulta capas e artworks em lote para os títulos do dashboard."""
        titulos_unicos = list(dict.fromkeys(
            titulo.strip() for titulo in titulos if titulo and titulo.strip()
        ))
        if not titulos_unicos:
            return {}

        imagens = {}
        uncached_titles = []
        now = time.time()
        for title in titulos_unicos:
            normalized_title = cls._normalizar_titulo(title)
            cached = cls._game_images_cache.get(normalized_title)
            if cached and now - cached['cached_at'] < cls._game_details_cache_ttl:
                imagens[normalized_title] = cached['images']
            else:
                if cached:
                    del cls._game_images_cache[normalized_title]
                uncached_titles.append(title)

        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()
        titulos_consultados = uncached_titles[:100]
        consulta_concluida = False
        if client_id and client_secret and titulos_consultados:
            clausulas = [
                f'name = "{cls._escapar_busca(titulo)}"'
                for titulo in titulos_consultados
            ]
            query = f'''
                fields name, cover.image_id, artworks.image_id,
                    artworks.width, artworks.height;
                where cover != null & ({' | '.join(clausulas)});
                limit {len(clausulas)};
            '''
            resultados = cls._executar_query_igdb(query)
            if isinstance(resultados, list):
                consulta_concluida = True
                requested_titles = {
                    cls._normalizar_titulo(title)
                    for title in titulos_consultados
                }
                for item in resultados:
                    if not isinstance(item, dict):
                        continue
                    title = item.get('name')
                    normalized_title = cls._normalizar_titulo(title)
                    if not title or normalized_title not in requested_titles:
                        continue

                    cover = item.get('cover') if isinstance(item.get('cover'), dict) else {}
                    artwork_entries = [
                        entry for entry in item.get('artworks') or []
                        if (
                            isinstance(entry, dict)
                            and entry.get('image_id')
                            and isinstance(entry.get('width'), int)
                            and isinstance(entry.get('height'), int)
                            and entry['width'] > entry['height']
                        )
                    ]
                    artwork_entries.sort(
                        key=lambda entry: entry['width'] * entry['height'],
                        reverse=True
                    )
                    imagens[normalized_title] = {
                        'cover': cls._url_imagem(cover.get('image_id'), 'cover_big'),
                        'artwork': (
                            cls._url_imagem(artwork_entries[0]['image_id'], '1080p')
                            if artwork_entries else None
                        )
                    }

        requested_titles = {
            cls._normalizar_titulo(title)
            for title in titulos_consultados
        }
        for fallback_game in IGDB_GAMES_FALLBACK:
            normalized_title = cls._normalizar_titulo(fallback_game.get('title'))
            if normalized_title in requested_titles:
                imagens.setdefault(normalized_title, {
                    'cover': fallback_game.get('thumbnail'),
                    'artwork': None
                })

        if consulta_concluida:
            for title in titulos_consultados:
                normalized_title = cls._normalizar_titulo(title)
                imagens.setdefault(normalized_title, {'cover': None, 'artwork': None})
                if len(cls._game_images_cache) >= 128:
                    oldest_title = min(
                        cls._game_images_cache,
                        key=lambda key: cls._game_images_cache[key]['cached_at']
                    )
                    del cls._game_images_cache[oldest_title]
                cls._game_images_cache[normalized_title] = {
                    'cached_at': now,
                    'images': imagens[normalized_title]
                }

        return {
            title: imagens[cls._normalizar_titulo(title)]
            for title in titulos_unicos
            if cls._normalizar_titulo(title) in imagens
        }

    @classmethod
    def filtrar_jogos_nao_cadastrados(cls, jogos, titulos_biblioteca, limite=8):
        """Remove recomendações já cadastradas e títulos duplicados, mantendo a ordem recebida."""
        titulos_vistos = {
            cls._normalizar_titulo(title)
            for title in titulos_biblioteca
            if title
        }
        jogos_filtrados = []
        for jogo in jogos:
            title = jogo.get('title')
            normalized_title = cls._normalizar_titulo(title)
            if (
                not title
                or not jogo.get('id')
                or not jogo.get('thumbnail')
                or normalized_title in titulos_vistos
            ):
                continue
            jogos_filtrados.append(jogo)
            titulos_vistos.add(normalized_title)
            if len(jogos_filtrados) >= limite:
                break
        return jogos_filtrados

    @classmethod
    def obter_detalhes_por_id(cls, game_id):
        """Retorna informações de um jogo, incluindo galeria e empresas, pelo ID IGDB."""
        cache_key = ('id', int(game_id))
        cached = cls._obter_cache_detalhes(cache_key, exige_completo=True)
        if cached:
            return cached

        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()
        if client_id and client_secret:
            query = f'''
                fields id, name, summary, cover.image_id, genres.name, platforms.name,
                    first_release_date, total_rating, total_rating_count, url,
                    involved_companies.company.name, involved_companies.developer,
                    involved_companies.publisher, artworks.image_id, artworks.width,
                    artworks.height, screenshots.image_id, similar_games.id,
                    similar_games.name,
                    similar_games.cover.image_id, similar_games.first_release_date,
                    franchise.name, franchise.games.id, franchise.games.name,
                    franchise.games.cover.image_id, franchise.games.first_release_date,
                    collections.games.id, collections.games.name,
                    collections.games.cover.image_id, collections.games.first_release_date;
                where id = {int(game_id)};
                limit 1;
            '''
            resultados = cls._executar_query_igdb(query)
            if resultados and isinstance(resultados, list):
                game = cls._formatar_detalhes_jogo(resultados[0])
                cls._guardar_cache_detalhes(cache_key, game)
                return game

        cached = cls._obter_cache_detalhes(cache_key)
        if cached:
            return cached

        for fallback_game in IGDB_GAMES_FALLBACK:
            if fallback_game['id'] == int(game_id):
                game = cls._formatar_detalhes_fallback(fallback_game)
                cls._guardar_cache_detalhes(cache_key, game)
                return game
        return None

    @classmethod
    def obter_detalhes_por_titulo(cls, titulo):
        """Busca detalhes IGDB por título exato para jogos locais sem ID externo."""
        normalized_title = cls._normalizar_titulo(titulo)
        if not normalized_title:
            return None

        cache_key = ('title', normalized_title)
        cached = cls._obter_cache_detalhes(cache_key)
        if cached:
            return cached

        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()
        if client_id and client_secret:
            busca_segura = cls._escapar_busca(titulo.strip())
            query = f'''
                search "{busca_segura}";
                fields id, name, summary, cover.image_id, genres.name, platforms.name,
                    first_release_date, total_rating, total_rating_count, url,
                    involved_companies.company.name, involved_companies.developer,
                    involved_companies.publisher, artworks.image_id, artworks.width,
                    artworks.height, screenshots.image_id, similar_games.id,
                    similar_games.name,
                    similar_games.cover.image_id, similar_games.first_release_date,
                    franchise.name, franchise.games.id, franchise.games.name,
                    franchise.games.cover.image_id, franchise.games.first_release_date,
                    collections.games.id, collections.games.name,
                    collections.games.cover.image_id, collections.games.first_release_date;
                limit 10;
            '''
            resultados = cls._executar_query_igdb(query)
            if resultados and isinstance(resultados, list):
                for item in resultados:
                    result_title = item.get('name')
                    if result_title and cls._normalizar_titulo(result_title) == normalized_title:
                        game = cls._formatar_detalhes_jogo(item)
                        cls._guardar_cache_detalhes(cache_key, game)
                        return game

        for fallback_game in IGDB_GAMES_FALLBACK:
            if cls._normalizar_titulo(fallback_game['title']) == normalized_title:
                game = cls._formatar_detalhes_fallback(fallback_game)
                cls._guardar_cache_detalhes(cache_key, game)
                return game
        return None

    @classmethod
    def obter_jogo_por_id(cls, game_id):
        """Retorna os dados completos de um jogo pelo seu ID no IGDB."""
        cached = cls._obter_cache_detalhes(('id', int(game_id)))
        if cached:
            return cached

        client_id = os.environ.get('IGDB_CLIENT_ID', '').strip()
        client_secret = os.environ.get('IGDB_CLIENT_SECRET', '').strip()

        if client_id and client_secret:
            query = f'''
                fields id, name, summary, cover.image_id, genres.name, platforms.name, first_release_date, total_rating, url;
                where id = {game_id};
                limit 1;
            '''
            resultados = cls._executar_query_igdb(query)
            if resultados and isinstance(resultados, list) and len(resultados) > 0:
                return cls._formatar_jogo(resultados[0])

        # Procura no fallback
        for j in IGDB_GAMES_FALLBACK:
            if j["id"] == game_id:
                return j

        return None
