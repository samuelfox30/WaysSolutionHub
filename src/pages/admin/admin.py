from flask import Blueprint, render_template, session, redirect, url_for


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():

    if 'user_email' in session and session.get('user_role') == 'admin':

        return render_template('admin/admin.html')

    else:

        return redirect(url_for('index.login'))



@admin_bp.route('/logout')
def logout():
    # Remove as informações do usuário da sessão
    session.pop('user_email', None)
    session.pop('user_role', None)

    # Redireciona o usuário para a página inicial (ou de login)
    return redirect(url_for('index.login'))


@admin_bp.route('/cadastrar', methods=['POST'])
def cadastrar_usuario():
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        return redirect(url_for('index.login'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    empresa = request.form.get('empresa')
    senha = request.form.get('senha')   
    perfil = request.form.get('perfil')

    erro_externo = []
    # ----------------------------- Validações de dados -----------------------------
    from controllers.auth.validation import validar_email, validar_senha, validar_tipo_usuario
    if not validar_email(email):
        print("Email inválido")
        erro_externo.append('Email inválido')
        if not validar_senha_cadastro(senha):
            print("Senha inválida")
            erro_externo.append('A senha precisa conter ao menos 8 caracteres, uma letra maiúscula, uma letra minúscula, um número e um caractere especial.')
            if not validar_tipo_usuario(perfil):
                print("Tipo de usuário inválido")
                erro_externo.append('Tipo de usuário inválido')
                if not validar_nome_empresa(empresa):
                    print("Nome de empresa inválido")
                    erro_externo.append('Nome de empresa inválido')

    if erro_externo:
        return render_template('admin/admin.html', erro_de_digitacao=erro_externo)

    # ----------------------------- Validações do banco de dados -----------------------------
    erro_interno = []
    from models.user_manager import UserManager
    user = UserManager()
    try:
        user.register_user(nome, email, empresa, senha, perfil)
    except Exception as e:
        erro_interno.append('Erro ao cadastrar usuário. Verifique se o email já está em uso.')
        print(f'Erro ao cadastrar usuário: {e}')

    if erro_interno:
        return render_template('admin/admin.html', erro_de_autenticacao=erro_interno)
    
    return redirect(url_for('admin.admin_dashboard', mensagem_sucesso="Usuário cadastrado com sucesso!"))

