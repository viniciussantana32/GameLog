from sqlalchemy import and_, case, func, or_
from app.extensions import db
from app.models.jogos import Jogo


def _nulos_por_ultimo(coluna, descendente=False):
    ordem_coluna = coluna.desc() if descendente else coluna.asc()
    return case((coluna.is_(None), 1), else_=0).asc(), ordem_coluna


class JogoService:
    """Camada de serviços responsável pelas regras de negócio e operações de banco da entidade Jogo."""

    @staticmethod
    def listar_jogos(busca=None, plataforma=None, ordenacao='recente', usuario_id=None):
        """Retorna a lista de jogos com filtros de busca, plataforma, ordenação e usuário."""
        query = Jogo.query

        if usuario_id is not None:
            query = query.filter(Jogo.usuario_id == usuario_id)

        if busca:
            termo = f"%{busca.strip()}%"
            query = query.filter(
                (Jogo.titulo.ilike(termo)) |
                (Jogo.genero.ilike(termo)) |
                (Jogo.observacoes.ilike(termo))
            )

        if plataforma and plataforma.strip():
            query = query.filter(Jogo.plataforma == plataforma.strip())

        if ordenacao == 'nota_desc':
            query = query.order_by(*_nulos_por_ultimo(Jogo.nota, descendente=True), Jogo.id.desc())
        elif ordenacao == 'nota_asc':
            query = query.order_by(*_nulos_por_ultimo(Jogo.nota), Jogo.id.desc())
        elif ordenacao == 'titulo':
            query = query.order_by(Jogo.titulo.asc())
        elif ordenacao == 'tempo_desc':
            query = query.order_by(*_nulos_por_ultimo(Jogo.tempo_jogado_horas, descendente=True))
        elif ordenacao == 'antigo':
            query = query.order_by(*_nulos_por_ultimo(Jogo.data_zeramento), Jogo.id.asc())
        else:  # recente por padrão
            query = query.order_by(*_nulos_por_ultimo(Jogo.data_zeramento, descendente=True), Jogo.id.desc())

        return query.all()

    @staticmethod
    def obter_por_id(jogo_id):
        """Busca um jogo pelo ID ou retorna None se não encontrado."""
        return Jogo.query.get(jogo_id)

    @staticmethod
    def obter_por_id_ou_404(jogo_id):
        """Busca um jogo pelo ID ou dispara 404."""
        return Jogo.query.get_or_404(jogo_id)

    @staticmethod
    def obter_por_usuario_e_titulo(usuario_id, titulo):
        """Busca a avaliação mais recente do usuário para um título exato."""
        titulo_normalizado = (titulo or '').strip().lower()
        if not usuario_id or not titulo_normalizado:
            return None
        return (
            Jogo.query
            .filter(
                Jogo.usuario_id == usuario_id,
                func.lower(func.trim(Jogo.titulo)) == titulo_normalizado
            )
            .order_by(Jogo.data_atualizacao.desc(), Jogo.id.desc())
            .first()
        )

    @staticmethod
    def obter_avaliacao_global(titulo, minimo_avaliacoes=3):
        """Retorna média comunitária apenas quando há avaliações suficientes."""
        titulo_normalizado = (titulo or '').strip().lower()
        if not titulo_normalizado:
            return None

        ultimas_avaliacoes = (
            db.session.query(func.max(Jogo.id).label('jogo_id'))
            .filter(
                func.lower(func.trim(Jogo.titulo)) == titulo_normalizado,
                Jogo.nota.isnot(None),
                Jogo.usuario_id.isnot(None)
            )
            .group_by(Jogo.usuario_id)
            .subquery()
        )
        ultimas = Jogo.query.join(ultimas_avaliacoes, Jogo.id == ultimas_avaliacoes.c.jogo_id)
        quantidade = ultimas.count()
        if quantidade < minimo_avaliacoes:
            return None

        media = ultimas.with_entities(func.avg(Jogo.nota)).scalar()
        return {
            'rating': round(float(media), 1),
            'count': quantidade
        }

    @staticmethod
    def criar_jogo(dados, usuario_id=None):
        """Cria e persiste um novo jogo zerado vinculado ao usuário."""
        novo_jogo = Jogo(
            usuario_id=usuario_id,
            titulo=dados.get('titulo'),
            plataforma=dados.get('plataforma'),
            genero=dados.get('genero') or None,
            ano_lancamento=dados.get('ano_lancamento') or None,
            status=dados.get('status') or None,
            data_zeramento=dados.get('data_zeramento') or None,
            tempo_jogado_horas=dados.get('tempo_jogado_horas') or None,
            nota=dados.get('nota') if dados.get('nota') is not None else None,
            dificuldade=dados.get('dificuldade') or None,
            observacoes=dados.get('observacoes') or None
        )
        db.session.add(novo_jogo)
        db.session.commit()
        return novo_jogo

    @staticmethod
    def atualizar_jogo(jogo, dados):
        """Atualiza os dados de um jogo existente."""
        jogo.titulo = dados.get('titulo', jogo.titulo)
        jogo.plataforma = dados.get('plataforma', jogo.plataforma)
        jogo.genero = dados.get('genero') or None
        jogo.ano_lancamento = dados.get('ano_lancamento') or None
        jogo.status = dados.get('status') or None
        jogo.data_zeramento = dados.get('data_zeramento') or None
        jogo.tempo_jogado_horas = dados.get('tempo_jogado_horas') or None
        jogo.nota = dados.get('nota') if dados.get('nota') is not None else None
        jogo.dificuldade = dados.get('dificuldade') or None
        jogo.observacoes = dados.get('observacoes') or None

        db.session.commit()
        return jogo

    @staticmethod
    def excluir_jogo(jogo):
        """Remove o registro de um jogo do banco de dados."""
        db.session.delete(jogo)
        db.session.commit()

    @staticmethod
    def usuario_pode_modificar(jogo, usuario):
        """Verifica se o usuário possui permissão para editar ou excluir o jogo."""
        return bool(
            jogo
            and usuario
            and usuario.is_authenticated
            and jogo.usuario_id is not None
            and jogo.usuario_id == usuario.id
        )

    @staticmethod
    def obter_estatisticas(usuario_id=None):
        """Calcula métricas e estatísticas gerais (ou filtradas por usuário) para o dashboard."""
        query = Jogo.query
        if usuario_id is not None:
            query = query.filter(Jogo.usuario_id == usuario_id)

        total_jogos = query.count()

        if total_jogos == 0:
            return {
                'total_jogos': 0,
                'media_nota': 0.0,
                'total_horas': 0.0,
                'plataforma_favorita': 'Nenhuma',
                'jogo_mais_bem_avaliado': None,
                'ultimos_jogos': []
            }

        avg_query = db.session.query(func.avg(Jogo.nota))
        sum_query = db.session.query(func.sum(Jogo.tempo_jogado_horas))
        top_plat_query = db.session.query(Jogo.plataforma, func.count(Jogo.id).label('qtd'))

        if usuario_id is not None:
            avg_query = avg_query.filter(Jogo.usuario_id == usuario_id)
            sum_query = sum_query.filter(Jogo.usuario_id == usuario_id)
            top_plat_query = top_plat_query.filter(Jogo.usuario_id == usuario_id)

        media_nota = avg_query.scalar() or 0.0
        total_horas = sum_query.scalar() or 0.0

        plataforma_top = (
            top_plat_query
            .group_by(Jogo.plataforma)
            .order_by(func.count(Jogo.id).desc())
            .first()
        )
        plataforma_favorita = plataforma_top[0] if plataforma_top else 'Nenhuma'

        jogo_mais_bem_avaliado_query = query.filter(Jogo.nota.isnot(None)).order_by(Jogo.nota.desc(), Jogo.id.desc())
        jogo_mais_bem_avaliado = jogo_mais_bem_avaliado_query.first()

        ultimos_jogos = (
            query
            .order_by(*_nulos_por_ultimo(Jogo.data_zeramento, descendente=True), Jogo.id.desc())
            .limit(4)
            .all()
        )

        return {
            'total_jogos': total_jogos,
            'media_nota': round(float(media_nota), 1),
            'total_horas': round(float(total_horas), 1),
            'plataforma_favorita': plataforma_favorita,
            'jogo_mais_bem_avaliado': jogo_mais_bem_avaliado,
            'ultimos_jogos': ultimos_jogos
        }

    @staticmethod
    def obter_dados_dashboard(usuario_id):
        """Retorna métricas e listas da biblioteca exclusivamente do usuário informado."""
        query = Jogo.query.filter(Jogo.usuario_id == usuario_id)
        total_jogos = query.count()
        jogos_zerados = query.filter(
            or_(
                Jogo.status == 'zerado',
                and_(Jogo.status.is_(None), Jogo.data_zeramento.isnot(None))
            )
        ).count()
        jogos_em_andamento = query.filter(Jogo.status == 'jogando').count()
        total_horas = (
            db.session.query(func.sum(Jogo.tempo_jogado_horas))
            .filter(Jogo.usuario_id == usuario_id)
            .scalar()
            or 0
        )
        media_nota = (
            db.session.query(func.avg(Jogo.nota))
            .filter(Jogo.usuario_id == usuario_id, Jogo.nota.isnot(None))
            .scalar()
            or 0
        )
        recentemente_adicionados = (
            query
            .order_by(Jogo.data_criacao.desc(), Jogo.id.desc())
            .limit(10)
            .all()
        )
        jogando = (
            query
            .filter(Jogo.status == 'jogando')
            .order_by(Jogo.data_atualizacao.desc(), Jogo.id.desc())
            .limit(6)
            .all()
        )
        melhores_avaliacoes = (
            query
            .filter(Jogo.nota.isnot(None))
            .order_by(Jogo.nota.desc(), Jogo.id.desc())
            .limit(6)
            .all()
        )
        titulos_biblioteca = [
            titulo
            for (titulo,) in query.with_entities(Jogo.titulo).all()
        ]

        return {
            'total_jogos': total_jogos,
            'jogos_zerados': jogos_zerados,
            'jogos_em_andamento': jogos_em_andamento,
            'total_horas': round(float(total_horas), 1),
            'media_nota': round(float(media_nota), 1),
            'recentemente_adicionados': recentemente_adicionados,
            'ultimo_jogo': recentemente_adicionados[0] if recentemente_adicionados else None,
            'jogando': jogando,
            'melhores_avaliacoes': melhores_avaliacoes,
            'titulos_biblioteca': titulos_biblioteca
        }
