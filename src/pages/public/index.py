from flask import Flask, Blueprint, render_template, url_for, redirect, request, session, flash

app_index = Blueprint('index', __name__)

#------------------FUNÇÃO PRINCIPAL------------------#
@app_index.route('/')
def index():
    """ if 'user' in session:
        return redirect(url_for('profile.profile'))
    return render_template('pages/public/index.html') """
    return render_template('public/index.html')


#------------------LOGAR------------------#
@app_index.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # ----------------------------- Recebendo parâmetros -----------------------------
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        senha = request.form.get('password')

        # ----------------------------- Validações de dados -----------------------------
        if not validar_email(email):
            flash('Email inválido. Por favor, verifique o formato.', 'danger')
            return redirect(url_for('index.login'))

        if not validar_senha(senha):
            flash('Senha inválida.', 'danger')
            return redirect(url_for('index.login'))

        if not validar_tipo_usuario(user_type):
            flash('Tipo de usuário inválido.', 'danger')
            return redirect(url_for('index.login'))

        # ----------------------------- Validações do banco de dados -----------------------------
        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(email)
        
        if not user_data:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('index.login'))
        
        # Você não precisa mais de hash_senha_sha256 na sua rota de login.
        # A forma correta de verificar senhas é usando check_password_hash.
        # Supondo que você use generate_password_hash, a verificação seria assim:
        from werkzeug.security import check_password_hash # type: ignore
        if not check_password_hash(user_data['password'], senha):
            flash('Senha incorreta.', 'danger')
            return redirect(url_for('index.login'))
        
        if user_data['role'] != user_type:
            flash('Tipo de usuário incorreto.', 'danger')
            return redirect(url_for('index.login'))

        # ----------------------------- Criando Sessão -----------------------------
        session['user_email'] = user_data['email']
        session['user_role'] = user_data['role']
        
        user_manager.close()

        if user_data['role'] == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        else:
            # Rota para usuário comum
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('user.user_dashboard')) # Exemplo de rota

    # Se a requisição for GET, renderiza a página de login
    return render_template('public/logar.html')


