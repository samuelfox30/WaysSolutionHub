from flask import Flask, Blueprint, render_template, url_for, redirect, request, session

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
        print(user_type, email, senha)

        # Variavel para controle de erros
        erro_externo = []

        # ----------------------------- Validações de dados -----------------------------
        from controllers.auth.validation import validar_email, validar_senha, validar_tipo_usuario
        if not validar_email(email):
            print("Email inválido")
            erro_externo.append('Email inválido')
            if not validar_senha(senha):
                print("Senha inválida")
                erro_externo.append('Senha inválida')
                if not validar_tipo_usuario(user_type):
                    print("Tipo de usuário inválido")
                    erro_externo.append('Tipo de usuário inválido')

        # ----------------------------- Validações do banco de dados -----------------------------
        erro_interno = []
        from models.user_manager import UserManager
        user = UserManager()
        dado = user.find_user_by_email(email)
        if dado:
            from controllers.auth.hash import hash_senha_sha256
            print(f'Só mostranso {senha}')
            senha = hash_senha_sha256(senha)
            print(f'Só mostranso {senha}')
            if dado['password'] == senha:
                if dado['role'] == user_type:
                    # ----------------------------- Criando Sessão -----------------------------
                    print("TUDO CERTOOOO !!!!!!!!!!!!!!!!!!/n/n/LOGOUUUUUUUUUUUUUUUU")
                    print(dado['email'], dado['role'])
                    session['user_email'] = dado['email']
                    session['user_role'] = dado['role']
                    if dado['role'] == 'admin':
                        return redirect(url_for('admin.admin_dashboard'))
                    else:
                        print('REDIRECIONAMENTO PARA PAGINA DE USUARIO COMUM, QUE AINDA NÃO EXISTE')
                else:
                    print("Tipo de usuário incorreto!")
                    erro_interno.append('Tipo de usuário incorreto!')
            else:
                print("Senha Incorreta!")
                erro_interno.append('Senha Incorreta!')
        else:
            print("Usuário não encontrado!")
            erro_interno.append('Usuário não encontrado!')
        user.close()

        # ----------------------------- Retornando dados -----------------------------
        if erro_externo:
            return render_template('public/logar.html', erro_de_digitacao=erro_externo)
        elif erro_interno:
            return render_template('public/logar.html', erro_de_autenticacao=erro_interno)
        
    return render_template('public/logar.html')


