from flask import Flask, Blueprint, render_template, url_for, redirect, request, session, flash
from utils.logger import get_logger

# Inicializar logger
logger = get_logger('auth_public')

app_index = Blueprint('index', __name__)

#------------------FUNÇÃO PRINCIPAL------------------#
@app_index.route('/')
def index():
    return render_template('public/index.html')


#------------------LOGAR------------------#
@app_index.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            logger.info("#" * 70)
            logger.info("### NOVA TENTATIVA DE LOGIN ###")
            logger.info("#" * 70)

            user_type = request.form.get('user_type')
            email = request.form.get('email')
            senha = request.form.get('password')

            logger.info(f"Dados recebidos do formulário:")
            logger.info(f"  - Tipo de usuário: {user_type}")
            logger.info(f"  - Email: {email}")
            logger.info(f"  - Senha fornecida: {'***' if senha else '(vazio)'}")
            logger.info(f"  - Tamanho da senha: {len(senha) if senha else 0} caracteres")

            # ========== VALIDAÇÕES ==========
            logger.info("-" * 50)
            logger.info("ETAPA 1: Validações de entrada")

            try:
                logger.info("Tentando importar módulo de validação...")
                logger.info("  - Importando de: controllers.auth.validation")
                from controllers.auth.validation import validar_email, validar_senha, validar_tipo_usuario
                logger.info("✓ Módulo de validação importado com sucesso")
            except ImportError as e:
                logger.error("✗ ERRO DE IMPORT no módulo de validação")
                logger.error(f"  - Tipo: ImportError")
                logger.error(f"  - Mensagem: {str(e)}")
                logger.error(f"  - Args: {e.args}")
                flash('Erro interno no servidor (import validation)', 'danger')
                return render_template('public/logar.html')
            except Exception as e:
                logger.error("✗ ERRO INESPERADO ao importar validação")
                logger.error(f"  - Tipo: {type(e).__name__}")
                logger.error(f"  - Mensagem: {str(e)}")
                logger.error(f"  - Args: {e.args}")
                import traceback
                logger.error(f"  - Traceback: {traceback.format_exc()}")
                flash('Erro interno no servidor (import exception)', 'danger')
                return render_template('public/logar.html')

            logger.info("Validando email...")
            try:
                email_valido = validar_email(email)
                logger.info(f"  - Email válido: {email_valido}")
            except Exception as e:
                logger.error(f"✗ Erro ao validar email: {type(e).__name__} - {str(e)}")
                email_valido = False

            if not email_valido:
                logger.warning("✗ Email inválido - abortando login")
                flash('Email inválido', 'danger')
                return render_template('public/logar.html')

            logger.info("Validando senha...")
            try:
                senha_valida = validar_senha(senha)
                logger.info(f"  - Senha válida: {senha_valida}")
            except Exception as e:
                logger.error(f"✗ Erro ao validar senha: {type(e).__name__} - {str(e)}")
                senha_valida = False

            if not senha_valida:
                logger.warning("✗ Senha inválida - abortando login")
                flash('Senha inválida', 'danger')
                return render_template('public/logar.html')

            logger.info("Validando tipo de usuário...")
            try:
                tipo_valido = validar_tipo_usuario(user_type)
                logger.info(f"  - Tipo de usuário válido: {tipo_valido}")
            except Exception as e:
                logger.error(f"✗ Erro ao validar tipo de usuário: {type(e).__name__} - {str(e)}")
                tipo_valido = False

            if not tipo_valido:
                logger.warning("✗ Tipo de usuário inválido - abortando login")
                flash('Tipo de usuário inválido', 'danger')
                return render_template('public/logar.html')

            logger.info("✓ Todas as validações passaram")

            # ========== BUSCAR USUÁRIO ==========
            logger.info("-" * 50)
            logger.info("ETAPA 2: Buscar usuário no banco de dados")

            try:
                logger.info("Tentando importar UserManager...")
                logger.info("  - Importando de: models.user_manager")
                from models.user_manager import UserManager
                logger.info("✓ UserManager importado com sucesso")
            except ImportError as e:
                logger.error("✗ ERRO DE IMPORT no UserManager")
                logger.error(f"  - Tipo: ImportError")
                logger.error(f"  - Mensagem: {str(e)}")
                logger.error(f"  - Args: {e.args}")
                flash('Erro interno no servidor (import UserManager)', 'danger')
                return render_template('public/logar.html')
            except Exception as e:
                logger.error("✗ ERRO INESPERADO ao importar UserManager")
                logger.error(f"  - Tipo: {type(e).__name__}")
                logger.error(f"  - Mensagem: {str(e)}")
                import traceback
                logger.error(f"  - Traceback: {traceback.format_exc()}")
                flash('Erro interno no servidor (exception UserManager)', 'danger')
                return render_template('public/logar.html')

            try:
                logger.info("Criando instância de UserManager...")
                user = UserManager()
                logger.info("✓ UserManager criado")
            except Exception as e:
                logger.error("✗ ERRO ao criar UserManager")
                logger.error(f"  - Tipo: {type(e).__name__}")
                logger.error(f"  - Mensagem: {str(e)}")
                import traceback
                logger.error(f"  - Traceback: {traceback.format_exc()}")
                flash('Erro ao conectar com banco de dados', 'danger')
                return render_template('public/logar.html')

            logger.info(f"Buscando usuário com email: {email}")
            dado = user.find_user_by_email(email)

            if dado:
                logger.info("✓ Usuário retornado do banco")
                logger.info(f"  - Dados do usuário recebidos: {list(dado.keys()) if isinstance(dado, dict) else 'não é dict'}")

                # ========== VERIFICAR SENHA ==========
                logger.info("-" * 50)
                logger.info("ETAPA 3: Verificação de senha")

                try:
                    logger.info("Tentando importar hash_senha_sha256...")
                    logger.info("  - Importando de: controllers.auth.hash")
                    from controllers.auth.hash import hash_senha_sha256
                    logger.info("✓ hash_senha_sha256 importado com sucesso")
                except ImportError as e:
                    logger.error("✗ ERRO DE IMPORT no módulo de hash")
                    logger.error(f"  - Tipo: ImportError")
                    logger.error(f"  - Mensagem: {str(e)}")
                    flash('Erro interno no servidor (import hash)', 'danger')
                    user.close()
                    return render_template('public/logar.html')
                except Exception as e:
                    logger.error("✗ ERRO INESPERADO ao importar hash")
                    logger.error(f"  - Tipo: {type(e).__name__}")
                    logger.error(f"  - Mensagem: {str(e)}")
                    import traceback
                    logger.error(f"  - Traceback: {traceback.format_exc()}")
                    flash('Erro interno no servidor (exception hash)', 'danger')
                    user.close()
                    return render_template('public/logar.html')

                try:
                    logger.info("Gerando hash SHA256 da senha fornecida...")
                    senha_hash = hash_senha_sha256(senha)
                    logger.info(f"  - Hash gerado com sucesso")
                except Exception as e:
                    logger.error("✗ ERRO ao gerar hash da senha")
                    logger.error(f"  - Tipo: {type(e).__name__}")
                    logger.error(f"  - Mensagem: {str(e)}")
                    import traceback
                    logger.error(f"  - Traceback: {traceback.format_exc()}")
                    flash('Erro ao processar senha', 'danger')
                    user.close()
                    return render_template('public/logar.html')

                logger.info(f"  - Tamanho hash fornecido: {len(senha_hash)} caracteres")
                logger.info(f"  - Tamanho hash do banco: {len(dado['password'])} caracteres")

                logger.info("Comparando hashes...")
                senhas_coincidem = (dado['password'] == senha_hash)
                logger.info(f"  - Senhas coincidem: {senhas_coincidem}")

                if senhas_coincidem:
                    logger.info("✓ Senha correta!")

                    # ========== VERIFICAR ROLE ==========
                    logger.info("-" * 50)
                    logger.info("ETAPA 4: Verificação de role")
                    logger.info(f"  - Role no banco: {dado['role']}")
                    logger.info(f"  - Role solicitado: {user_type}")

                    role_coincide = (dado['role'] == user_type)
                    logger.info(f"  - Roles coincidem: {role_coincide}")

                    if role_coincide:
                        logger.info("✓ Role correto!")

                        # ========== CRIAR SESSÃO ==========
                        logger.info("-" * 50)
                        logger.info("ETAPA 5: Criação de sessão")
                        logger.info("Definindo variáveis de sessão...")
                        session['user_email'] = dado['email']
                        session['user_role'] = dado['role']
                        logger.info(f"  ✓ session['user_email'] = {session.get('user_email')}")
                        logger.info(f"  ✓ session['user_role'] = {session.get('user_role')}")

                        # ========== REDIRECIONAMENTO ==========
                        logger.info("-" * 50)
                        logger.info("ETAPA 6: Redirecionamento")

                        if dado['role'] == 'admin':
                            logger.info("Redirecionando para: admin.admin_dashboard")
                            user.close()
                            logger.info("#" * 70)
                            logger.info("### LOGIN ADMIN BEM-SUCEDIDO ###")
                            logger.info("#" * 70)
                            return redirect(url_for('admin.admin_dashboard'))
                        else:  # user
                            logger.info("Redirecionando para: user.selecionar_empresa")
                            user.close()
                            logger.info("#" * 70)
                            logger.info("### LOGIN USER BEM-SUCEDIDO ###")
                            logger.info("#" * 70)
                            return redirect(url_for('user.selecionar_empresa'))
                    else:
                        logger.warning("✗ Tipo de usuário incorreto!")
                        logger.warning(f"  - Esperado: {user_type}")
                        logger.warning(f"  - Encontrado: {dado['role']}")
                        flash('Tipo de usuário incorreto!', 'danger')
                else:
                    logger.warning("✗ Senha Incorreta!")
                    logger.warning("  - Hash não coincide com o armazenado no banco")
                    flash('Senha incorreta!', 'danger')
            else:
                logger.warning("✗ Usuário não encontrado!")
                logger.warning(f"  - Nenhum registro com email: {email}")
                flash('Usuário não encontrado!', 'danger')

            logger.info("Fechando conexão UserManager...")
            user.close()
            logger.info("#" * 70)
            logger.info("### LOGIN FALHOU ###")
            logger.info("#" * 70)

        except Exception as e:
            logger.error("=" * 70)
            logger.error("✗✗✗ EXCEÇÃO NÃO CAPTURADA NO FLUXO DE LOGIN ✗✗✗")
            logger.error(f"Tipo da exceção: {type(e).__name__}")
            logger.error(f"Mensagem: {str(e)}")
            logger.error(f"Args: {e.args}")
            import traceback
            logger.error("Traceback completo:")
            logger.error(traceback.format_exc())
            logger.error("=" * 70)
            flash('Erro interno no servidor. Tente novamente.', 'danger')

    return render_template('public/logar.html')
