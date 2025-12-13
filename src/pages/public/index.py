from flask import Flask, Blueprint, render_template, url_for, redirect, request, session, flash

# Import do sistema de logging
from utils.logger import get_logger, log_login_attempt, log_session_created, log_session_destroyed

app_index = Blueprint('index', __name__)
logger = get_logger('auth')

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

        logger.info(f"🔐 Tentativa de login: email={email}, tipo={user_type}, IP={request.remote_addr}")

        from controllers.auth.validation import validar_email, validar_senha, validar_tipo_usuario
        if not validar_email(email):
            logger.warning(f"❌ Login falhou - Email inválido: {email}")
            flash('Email inválido', 'danger')
            return render_template('public/logar.html')

        if not validar_senha(senha):
            logger.warning(f"❌ Login falhou - Senha inválida para: {email}")
            flash('Senha inválida', 'danger')
            return render_template('public/logar.html')

        if not validar_tipo_usuario(user_type):
            logger.warning(f"❌ Login falhou - Tipo de usuário inválido: {user_type} para {email}")
            flash('Tipo de usuário inválido', 'danger')
            return render_template('public/logar.html')

        from models.user_manager import UserManager
        user = UserManager()

        try:
            dado = user.find_user_by_email(email)

            if dado:
                logger.debug(f"🔍 Usuário encontrado no banco: {email}")

                from controllers.auth.hash import hash_senha_sha256
                senha_hash = hash_senha_sha256(senha)

                if dado['password'] == senha_hash:
                    if dado['role'] == user_type:
                        session['user_email'] = dado['email']
                        session['user_role'] = dado['role']

                        # Log de sucesso
                        log_session_created(dado['email'], str(id(session)))
                        logger.info(f"✅ Login bem-sucedido: {email} como {user_type}")

                        # Redireciona conforme o tipo de usuário
                        if dado['role'] == 'admin':
                            user.close()
                            return redirect(url_for('admin.admin_dashboard'))
                        else:  # user
                            user.close()
                            return redirect(url_for('user.selecionar_empresa'))
                    else:
                        logger.warning(f"❌ Login falhou - Tipo de usuário incorreto: esperado={dado['role']}, tentou={user_type} para {email}")
                        flash('Tipo de usuário incorreto!', 'danger')
                else:
                    logger.warning(f"❌ Login falhou - Senha incorreta para: {email}")
                    flash('Senha incorreta!', 'danger')
            else:
                logger.warning(f"❌ Login falhou - Usuário não encontrado: {email}")
                flash('Usuário não encontrado!', 'danger')
        except Exception as e:
            logger.error(f"💥 ERRO durante login de {email}: {str(e)}", exc_info=True)
            flash('Erro no servidor. Tente novamente.', 'danger')
        finally:
            user.close()

    return render_template('public/logar.html')