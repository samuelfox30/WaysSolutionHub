from flask import Flask, Blueprint, render_template, url_for, redirect, request, session, flash

app_index = Blueprint('index', __name__)

#------------------FUNÇÃO PRINCIPAL------------------#
@app_index.route('/')
def index():
    return render_template('public/index.html')


#------------------LOGAR------------------#
@app_index.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        senha = request.form.get('password')
        print(user_type, email, senha)

        from controllers.auth.validation import validar_email, validar_senha, validar_tipo_usuario
        if not validar_email(email):
            print("Email inválido")
            flash('Email inválido', 'danger')
            return render_template('public/logar.html')
            
        if not validar_senha(senha):
            print("Senha inválida")
            flash('Senha inválida', 'danger')
            return render_template('public/logar.html')
            
        if not validar_tipo_usuario(user_type):
            print("Tipo de usuário inválido")
            flash('Tipo de usuário inválido', 'danger')
            return render_template('public/logar.html')

        from models.user_manager import UserManager
        user = UserManager()
        dado = user.find_user_by_email(email)
        
        if dado:
            from controllers.auth.hash import hash_senha_sha256
            senha_hash = hash_senha_sha256(senha)
            
            if dado['password'] == senha_hash:
                if dado['role'] == user_type:
                    session['user_email'] = dado['email']
                    session['user_role'] = dado['role']
                    
                    # Redireciona conforme o tipo de usuário
                    if dado['role'] == 'admin':
                        user.close()
                        return redirect(url_for('admin.admin_dashboard'))
                    else:  # user
                        user.close()
                        return redirect(url_for('user.user_dashboard'))
                else:
                    print("Tipo de usuário incorreto!")
                    flash('Tipo de usuário incorreto!', 'danger')
            else:
                print("Senha Incorreta!")
                flash('Senha incorreta!', 'danger')
        else:
            print("Usuário não encontrado!")
            flash('Usuário não encontrado!', 'danger')
        
        user.close()

    return render_template('public/logar.html')