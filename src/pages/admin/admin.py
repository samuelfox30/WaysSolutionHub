from flask import Blueprint, render_template, session, redirect, url_for, request, flash


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():

    if 'user_email' in session and session.get('user_role') == 'admin':
        from models.user_manager import UserManager
        user_manager = UserManager()
        users = user_manager.get_all_users()
        return render_template('admin/admin.html', users=users)

    else:

        return redirect(url_for('index.login'))


@admin_bp.route('/logout')
def logout():
    # Remove as informações do usuário da sessão
    session.pop('user_email', None)
    session.pop('user_role', None)

    # Redireciona o usuário para a página inicial (ou de login)
    return redirect(url_for('index.login'))


@admin_bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_usuario():
    # Se a requisição não for POST, redireciona para a dashboard
    if request.method != 'POST':
        return redirect(url_for('admin.admin_dashboard'))

    # Verificação de autenticação de administrador (melhor usar um decorador como discutido antes)
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    empresa = request.form.get('empresa')
    seguimento = request.form.get('seguimento')
    senha = request.form.get('senha')
    perfil = request.form.get('perfil')

    # ----------------------------- Validações de dados -----------------------------
    from controllers.auth.validation import (
        validar_email, 
        validar_senha_cadastro, 
        validar_tipo_usuario, 
        validar_nome_empresa, 
        validar_telefone, 
        validar_seguimento
    )

    # Verificações sequenciais com flash e redirect
    if not validar_email(email):
        flash('Email inválido. Por favor, verifique o formato.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    if not validar_senha_cadastro(senha):
        flash('A senha precisa conter ao menos 8 caracteres, uma letra maiúscula, uma letra minúscula, um número e um caractere especial.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    if not validar_tipo_usuario(perfil):
        flash('Tipo de usuário inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_nome_empresa(empresa):
        flash('Nome de empresa inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_telefone(telefone):
        flash('Por favor, digite um número de telefone válido. Use o formato: (XX) XXXXX-XXXX ou XXXXXXXXXXX.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_seguimento(seguimento):
        flash('Seguimento inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    # ----------------------------- Validação e Cadastro no banco de dados -----------------------------
    from models.user_manager import UserManager
    user_manager = UserManager()
    
    # A função register_user agora retorna uma tupla (True/False, mensagem)
    success, message = user_manager.register_user(
        nome, 
        email, 
        telefone, 
        empresa, 
        seguimento, 
        senha, 
        perfil
    )

    # Verifica o resultado e define a mensagem flash
    if success:
        flash(message, "success")
    else:
        # A mensagem já vem formatada para o usuário (e-mail já em uso, etc.)
        flash(message, "danger") 

    # Fecha a conexão do banco de dados (boa prática)
    user_manager.close()
    
    # Redireciona para a página principal, onde a mensagem será exibida
    return redirect(url_for('admin.admin_dashboard'))

