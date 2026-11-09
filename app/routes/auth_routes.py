from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth_forms import LoginForm, RegistroForm, PerfilForm, AlterarSenhaForm
from app.services.usuario_service import UsuarioService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para autenticação de usuários existentes."""
    if current_user.is_authenticated:
        return redirect(url_for('jogos.index'))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = UsuarioService.autenticar(form.identificador.data, form.senha.data)
        if usuario:
            login_user(usuario, remember=form.lembrar_me.data)
            flash(f'Bem-vindo(a) de volta, {usuario.nome}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('jogos.index'))
        else:
            flash('Usuário, e-mail ou senha incorretos. Verifique suas credenciais.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Rota para criação de uma nova conta de usuário."""
    if current_user.is_authenticated:
        return redirect(url_for('jogos.index'))

    form = RegistroForm()
    if form.validate_on_submit():
        try:
            novo_usuario = UsuarioService.criar_usuario(form.data)
            login_user(novo_usuario)
            flash(f'Conta criada com sucesso! Seja bem-vindo(a) ao Gamelog, {novo_usuario.nome}!', 'success')
            return redirect(url_for('jogos.index'))
        except Exception as e:
            flash(f'Erro ao criar conta no banco JOGOSSALVOS: {str(e)}', 'danger')

    return render_template('auth/registro.html', form=form)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Encerra a sessão do usuário conectado."""
    logout_user()
    flash('Você encerrou sua sessão com sucesso. Até breve!', 'info')
    return redirect(url_for('jogos.index'))


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Visualização e atualização do perfil do usuário autenticado."""
    form = PerfilForm(obj=current_user)
    form_senha = AlterarSenhaForm()

    if form.validate_on_submit():
        try:
            UsuarioService.atualizar_perfil(current_user, form.data)
            flash('Seu perfil foi atualizado com sucesso!', 'success')
            return redirect(url_for('auth.perfil'))
        except ValueError as e:
            flash(str(e), 'warning')
        except Exception as e:
            flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')

    return render_template('auth/perfil.html', form=form, form_senha=form_senha, usuario=current_user)


@auth_bp.route('/perfil/senha', methods=['POST'])
@login_required
def alterar_senha():
    """Processa a alteração de senha autenticada."""
    form_senha = AlterarSenhaForm()

    if form_senha.validate_on_submit():
        try:
            UsuarioService.alterar_senha(
                current_user,
                form_senha.senha_atual.data,
                form_senha.nova_senha.data
            )
            flash('Sua senha foi alterada com sucesso!', 'success')
            return redirect(url_for('auth.perfil'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Erro ao atualizar senha: {str(e)}', 'danger')
    else:
        for field, errors in form_senha.errors.items():
            for error in errors:
                flash(f'Erro na alteração de senha: {error}', 'danger')

    return redirect(url_for('auth.perfil'))

