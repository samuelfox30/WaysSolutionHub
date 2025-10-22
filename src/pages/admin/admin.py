from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():

    if 'user_email' in session and session.get('user_role') == 'admin':
        from models.user_manager import UserManager
        user_manager = UserManager()
        users = user_manager.get_all_users()
        user_manager.close()
        return render_template('admin/admin.html', users=users)

    else:

        return redirect(url_for('index.login'))


@admin_bp.route('/logout')
def logout():
    # Verificação de autenticação de administrador
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))
        
    # Remove as informações do usuário da sessão
    session.pop('user_email', None)
    session.pop('user_role', None)

    # Redireciona o usuário para a página inicial (ou de login)
    return redirect(url_for('index.login'))


@admin_bp.route('/admin/cadastrar', methods=['GET', 'POST'])
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
    from controllers.auth.validation import validar_email, validar_senha_cadastro, validar_tipo_usuario, validar_nome_empresa, validar_telefone, validar_seguimento

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
    success = user_manager.register_user(
        nome, 
        email, 
        telefone, 
        empresa, 
        seguimento, 
        senha, 
        perfil
    )

    if success:
        flash("Usuário cadastrado com sucesso!", "success")
    else:
        flash("Ocorreu um erro ao cadastrar o usuário. Por favor, verifique os dados e tente novamente.", "danger")

    # Fecha a conexão do banco de dados (boa prática)
    user_manager.close()
    
    # Redireciona para a página principal, onde a mensagem será exibida
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/delete/<int:user_id>', methods=['GET', 'POST'])
def delete_user_route(user_id):
    # Verificação de segurança: apenas admins podem excluir usuários
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.user_manager import UserManager
    user_manager = UserManager()
    success = user_manager.delete_user(user_id)
    user_manager.close()

    if success:
        flash("Usuário excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir usuário.", "danger")

    return redirect(url_for('admin.admin_dashboard'))



@admin_bp.route('/admin/edit', methods=['POST'])
def editar_usuario():
    # Verificação de autenticação de administrador
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    # Coleta dos dados do formulário
    user_id = request.form.get('id')
    nome = request.form.get('nome')
    email = request.form.get('email')
    empresa = request.form.get('empresa')
    perfil = request.form.get('perfil')

    # ----------------------------- Validações -----------------------------
    from controllers.auth.validation import validar_email, validar_tipo_usuario, validar_nome_empresa

    if not validar_email(email):
        flash('Email inválido. Por favor, verifique o formato.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_tipo_usuario(perfil):
        flash('Tipo de usuário inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_nome_empresa(empresa):
        flash('Nome de empresa inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    # ----------------------------- Atualização no banco de dados -----------------------------
    from models.user_manager import UserManager
    user_manager = UserManager()
    success = user_manager.update_user(user_id, nome, email, empresa, perfil)
    user_manager.close()

    if success:
        flash("Usuário atualizado com sucesso!", "success")
    else:
        flash("Erro ao atualizar usuário. Verifique os dados e tente novamente.", "danger")

    return redirect(url_for('admin.admin_dashboard'))


# ----------------------------------------------------------------------------- CONTROLE DE EMPRESAS --------------------------------------------------------------------------------------------

@admin_bp.route('/admin/empresas')
def dados_empresas():
    if 'user_email' in session and session.get('user_role') == 'admin':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager

        # Pega o ano da query string ou usa o ano atual
        ano = request.args.get('ano', datetime.now().year, type=int)

        user_manager = UserManager()
        users = user_manager.get_all_users()
        user_manager.close()

        company_manager = CompanyManager()
        uploads = {}
        for user in users:
            meses_com_dados = company_manager.get_meses_com_dados(user["id"], ano)
            uploads[user["empresa"]] = {m: (m in meses_com_dados) for m in range(1, 13)}
        company_manager.close()

        return render_template(
            'admin/empresas.html',
            users=users,
            uploads=uploads,
            current_year=ano
        )
    else:
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))



@admin_bp.route('/admin/upload', methods=['GET', 'POST'])
def upload_dados():

    # Verificação de autenticação de administrador
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    if request.method != 'POST':
        return redirect(url_for('admin.dados_empresas'))

    empresa = request.form.get('empresa')
    mes = request.form.get('mes')
    ano = request.form.get('ano')
    arquivo = request.files.get('arquivo')

    # ✅ Prints de verificação
    print(f"Empresa selecionada: {empresa}")
    print(f"Mês selecionado: {mes}")
    print(f"Ano selecionado: {ano}")
    print(f"Nome do arquivo recebido: {arquivo.filename if arquivo else 'Nenhum arquivo'}")
    from controllers.data_processing.file_processing import process_uploaded_file
    dados = process_uploaded_file(arquivo)
    d1 = dados[0]
    d2 = dados[1]
    from models.company_manager import CompanyManager
    company_manager_variable = CompanyManager()
    company_manager_variable.salvar_itens_empresa(empresa, mes, ano, d1, d2)
    company_manager_variable.close()


    # ...continuação do processamento

    return redirect(url_for('admin.dados_empresas'))
    


@admin_bp.route('/admin/consultar', methods=['GET', 'POST'])
def consultar_dados_page():
    # Verificação de autenticação de administrador
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))  # Use o nome correto do seu Blueprint de login

    from models.user_manager import UserManager
    from models.company_manager import CompanyManager

    user_manager = UserManager()
    users = user_manager.get_all_users()  # Lista de empresas para o select

    data_results = None
    empresa_selecionada = None
    mes_selecionado = None
    ano_selecionado = None

    if request.method == 'POST':
        empresa_selecionada = request.form.get('empresa')
        mes_selecionado = request.form.get('mes')
        ano_selecionado = request.form.get('ano')

        if empresa_selecionada and mes_selecionado and ano_selecionado:
            company_manager = CompanyManager()
            data_results = company_manager.buscar_dados_empresa(
                empresa_selecionada,
                int(mes_selecionado),
                int(ano_selecionado)
            )
            company_manager.close()

    return render_template(
        'admin/consultar_dados.html',
        users=users,
        data_results=data_results,
        empresa_selecionada=empresa_selecionada,
        mes_selecionado=mes_selecionado,
        ano_selecionado=ano_selecionado
    )


@admin_bp.route('/admin/deletar_dados', methods=['POST'])
def deletar_dados_empresa():
    if 'user_email' in session and session.get('user_role') == 'admin':
        empresa = request.form.get('empresa')
        mes = request.form.get('mes', type=int)
        ano = request.form.get('ano', type=int)

        if not empresa or not mes or not ano:
            flash("Parâmetros inválidos para exclusão.", "danger")
            return redirect(url_for('admin.dados_empresas'))

        from models.company_manager import CompanyManager
        company_manager = CompanyManager()
        ok = company_manager.excluir_dados_empresa(empresa, mes, ano)
        company_manager.close()

        if ok:
            flash(f"Dados da empresa '{empresa}' para {mes}/{ano} foram excluídos com sucesso.", "success")
        else:
            flash(f"Erro ao excluir dados da empresa '{empresa}' para {mes}/{ano}.", "danger")

        return redirect(url_for('admin.dados_empresas'))

    else:
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))
