from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime


admin_bp = Blueprint('admin', __name__)

# ============================
# DASHBOARD E AUTENTICAÇÃO
# ============================

@admin_bp.route('/admin')
def admin_dashboard():
    """Dashboard principal - gerenciamento de usuários"""
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
    """Logout do administrador"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    session.pop('user_email', None)
    session.pop('user_role', None)
    return redirect(url_for('index.login'))


# ============================
# GERENCIAMENTO DE USUÁRIOS
# ============================

@admin_bp.route('/admin/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    """Cadastra um novo usuário (SEM campos de empresa)"""
    if request.method != 'POST':
        return redirect(url_for('admin.admin_dashboard'))

    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    senha = request.form.get('senha')
    perfil = request.form.get('perfil')

    # ----------------------------- Validações -----------------------------
    from controllers.auth.validation import validar_email, validar_senha_cadastro, validar_tipo_usuario, validar_telefone

    if not validar_email(email):
        flash('Email inválido. Por favor, verifique o formato.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_senha_cadastro(senha):
        flash('A senha precisa conter ao menos 8 caracteres, uma letra maiúscula, uma letra minúscula, um número e um caractere especial.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_tipo_usuario(perfil):
        flash('Tipo de usuário inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_telefone(telefone):
        flash('Por favor, digite um número de telefone válido. Use o formato: (XX) XXXXX-XXXX ou XXXXXXXXXXX.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    # ----------------------------- Cadastro no banco -----------------------------
    from models.user_manager import UserManager
    user_manager = UserManager()

    user_id = user_manager.register_user(nome, email, telefone, senha, perfil)

    if user_id:
        flash(f"Usuário cadastrado com sucesso! Agora você pode vinculá-lo a empresas.", "success")
    else:
        flash("Ocorreu um erro ao cadastrar o usuário. Por favor, verifique os dados e tente novamente.", "danger")

    user_manager.close()
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/editar_usuario', methods=['POST'])
def editar_usuario():
    """Edita um usuário existente (SEM campo empresa)"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    user_id = request.form.get('id')
    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    perfil = request.form.get('perfil')

    # ----------------------------- Validações -----------------------------
    from controllers.auth.validation import validar_email, validar_tipo_usuario, validar_telefone

    if not validar_email(email):
        flash('Email inválido. Por favor, verifique o formato.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_tipo_usuario(perfil):
        flash('Tipo de usuário inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if not validar_telefone(telefone):
        flash('Telefone inválido.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    # ----------------------------- Atualização no banco -----------------------------
    from models.user_manager import UserManager
    user_manager = UserManager()
    success = user_manager.update_user(user_id, nome, email, telefone, perfil)
    user_manager.close()

    if success:
        flash("Usuário atualizado com sucesso!", "success")
    else:
        flash("Erro ao atualizar usuário. Verifique os dados e tente novamente.", "danger")

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/deletar_usuario/<int:user_id>', methods=['GET', 'POST'])
def deletar_usuario(user_id):
    """Deleta um usuário"""
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


# ============================
# GERENCIAMENTO DE EMPRESAS
# ============================

@admin_bp.route('/admin/empresas')
def gerenciar_empresas():
    """Página de gerenciamento de empresas"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    empresas = company_manager.listar_todas_empresas()

    # Para cada empresa, buscar anos com dados
    uploads = {}
    for empresa in empresas:
        anos_com_dados = company_manager.get_anos_com_dados(empresa['id'])
        uploads[empresa['id']] = anos_com_dados

    company_manager.close()

    return render_template('admin/empresas.html', empresas=empresas, uploads=uploads)


@admin_bp.route('/admin/cadastrar_empresa', methods=['POST'])
def cadastrar_empresa():
    """Cadastra uma nova empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    nome = request.form.get('nome')
    cnpj = request.form.get('cnpj')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    cep = request.form.get('cep')
    complemento = request.form.get('complemento', '')
    seguimento = request.form.get('seguimento')
    website = request.form.get('website', None)

    # ----------------------------- Validações básicas -----------------------------
    if not all([nome, cnpj, telefone, email, cep, seguimento]):
        flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
        return redirect(url_for('admin.gerenciar_empresas'))

    # ----------------------------- Cadastro no banco -----------------------------
    from models.company_manager import CompanyManager
    company_manager = CompanyManager()

    empresa_id = company_manager.criar_empresa(
        nome, cnpj, telefone, email, cep, complemento, seguimento, website
    )

    if empresa_id:
        flash(f"Empresa '{nome}' cadastrada com sucesso!", "success")
    else:
        flash("Erro ao cadastrar empresa. Verifique se o CNPJ já não está cadastrado.", "danger")

    company_manager.close()
    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/editar_empresa', methods=['POST'])
def editar_empresa():
    """Edita uma empresa existente"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    empresa_id = request.form.get('id')
    nome = request.form.get('nome')
    cnpj = request.form.get('cnpj')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    cep = request.form.get('cep')
    complemento = request.form.get('complemento', '')
    seguimento = request.form.get('seguimento')
    website = request.form.get('website', None)

    # ----------------------------- Validações básicas -----------------------------
    if not all([empresa_id, nome, cnpj, telefone, email, cep, seguimento]):
        flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
        return redirect(url_for('admin.gerenciar_empresas'))

    # ----------------------------- Atualização no banco -----------------------------
    from models.company_manager import CompanyManager
    company_manager = CompanyManager()

    success = company_manager.atualizar_empresa(
        empresa_id, nome, cnpj, telefone, email, cep, complemento, seguimento, website
    )

    if success:
        flash("Empresa atualizada com sucesso!", "success")
    else:
        flash("Erro ao atualizar empresa.", "danger")

    company_manager.close()
    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/deletar_empresa/<int:empresa_id>', methods=['GET', 'POST'])
def deletar_empresa(empresa_id):
    """Deleta uma empresa (e todos os seus dados CASCADE)"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    success = company_manager.deletar_empresa(empresa_id)
    company_manager.close()

    if success:
        flash("Empresa excluída com sucesso!", "success")
    else:
        flash("Erro ao excluir empresa.", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/dashboard-empresa/<int:empresa_id>')
def dashboard_empresa(empresa_id):
    """Dashboard de uma empresa específica (acesso admin)"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager

    company_manager = CompanyManager()
    empresa = company_manager.buscar_empresa_por_id(empresa_id)

    if not empresa:
        flash("Empresa não encontrada.", "danger")
        company_manager.close()
        return redirect(url_for('admin.gerenciar_empresas'))

    # Busca anos com dados disponíveis para esta empresa
    anos_disponiveis = company_manager.get_anos_com_dados(empresa_id)
    company_manager.close()

    # Busca informações do admin logado (para exibir no header)
    from models.user_manager import UserManager
    user_manager = UserManager()
    user_data = user_manager.find_user_by_email(session.get('user_email'))
    user_manager.close()

    return render_template(
        'admin/dashboard_empresa.html',
        user=user_data,
        empresa=empresa,
        empresa_nome=empresa['nome'],
        empresa_id=empresa_id,
        anos_disponiveis=anos_disponiveis
    )


@admin_bp.route('/admin/api/dados-empresa/<int:empresa_id>/<int:ano>')
def api_dados_empresa(empresa_id, ano):
    """API para retornar dados de uma empresa (acesso admin)"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        return json.dumps({"error": "Não autorizado"}), 403

    from models.company_manager import CompanyManager
    import json

    company_manager = CompanyManager()
    data_results = company_manager.buscar_dados_empresa(empresa_id, ano)
    company_manager.close()

    # Organizar dados por SUBGRUPO dentro de cada grupo de viabilidade
    dados_organizados = {}

    # Processar TbItens
    if data_results and data_results.get('TbItens'):
        for item in data_results['TbItens']:
            grupo = item[0]
            subgrupo = item[1]
            descricao = item[2]
            percentual = float(item[3]) if item[3] else 0
            valor = float(item[4]) if item[4] else 0

            if grupo not in dados_organizados:
                dados_organizados[grupo] = {}

            if subgrupo not in dados_organizados[grupo]:
                dados_organizados[grupo][subgrupo] = []

            dados_organizados[grupo][subgrupo].append({
                "descricao": descricao,
                "percentual": percentual,
                "valor": valor
            })

    # Processar outras tabelas
    for tabela in ['TbItensInvestimentos', 'TbItensDividas', 'TbItensInvestimentoGeral', 'TbItensGastosOperacionais']:
        if data_results and data_results.get(tabela):
            for item in data_results[tabela]:
                grupo = item[0]
                subgrupo = item[1]
                descricao = item[2]

                if tabela in ['TbItensInvestimentos', 'TbItensDividas']:
                    valor = float(item[5]) if len(item) > 5 and item[5] else 0
                elif tabela == 'TbItensInvestimentoGeral':
                    valor = float(item[3]) if len(item) > 3 and item[3] else 0
                elif tabela == 'TbItensGastosOperacionais':
                    valor = float(item[4]) if len(item) > 4 and item[4] else 0
                else:
                    continue

                if grupo not in dados_organizados:
                    dados_organizados[grupo] = {}

                if subgrupo not in dados_organizados[grupo]:
                    dados_organizados[grupo][subgrupo] = []

                dados_organizados[grupo][subgrupo].append({
                    "descricao": descricao,
                    "valor": valor,
                    "percentual": 0
                })

    return json.dumps({
        "ano": ano,
        "dados": dados_organizados
    }), 200, {'Content-Type': 'application/json'}


# ============================
# RELACIONAMENTO USER-EMPRESA
# ============================

@admin_bp.route('/admin/vinculos')
def gerenciar_vinculos():
    """Página de gerenciamento de vínculos usuário-empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.user_manager import UserManager
    from models.company_manager import CompanyManager

    user_manager = UserManager()
    company_manager = CompanyManager()

    users = user_manager.get_all_users()
    empresas = company_manager.listar_todas_empresas()

    # Para cada usuário, buscar empresas vinculadas
    user_empresas = {}
    for user in users:
        user_empresas[user['id']] = user_manager.get_empresas_do_usuario(user['id'])

    user_manager.close()
    company_manager.close()

    return render_template('admin/vinculos.html',
                         users=users,
                         empresas=empresas,
                         user_empresas=user_empresas)


@admin_bp.route('/admin/vincular', methods=['POST'])
def vincular_user_empresa():
    """Vincula um usuário a uma empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    user_id = request.form.get('user_id')
    empresa_id = request.form.get('empresa_id')

    if not user_id or not empresa_id:
        flash("Selecione um usuário e uma empresa.", "danger")
        return redirect(url_for('admin.gerenciar_vinculos'))

    from models.user_manager import UserManager
    user_manager = UserManager()
    success = user_manager.vincular_user_empresa(int(user_id), int(empresa_id))
    user_manager.close()

    if success:
        flash("Vínculo criado com sucesso!", "success")
    else:
        flash("Erro ao criar vínculo.", "danger")

    return redirect(url_for('admin.gerenciar_vinculos'))


@admin_bp.route('/admin/desvincular', methods=['POST'])
def desvincular_user_empresa():
    """Desvincula um usuário de uma empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    user_id = request.form.get('user_id')
    empresa_id = request.form.get('empresa_id')

    if not user_id or not empresa_id:
        flash("Parâmetros inválidos.", "danger")
        return redirect(url_for('admin.gerenciar_vinculos'))

    from models.user_manager import UserManager
    user_manager = UserManager()
    success = user_manager.desvincular_user_empresa(int(user_id), int(empresa_id))
    user_manager.close()

    if success:
        flash("Vínculo removido com sucesso!", "success")
    else:
        flash("Erro ao remover vínculo.", "danger")

    return redirect(url_for('admin.gerenciar_vinculos'))


# ============================
# UPLOAD E GESTÃO DE DADOS
# ============================

@admin_bp.route('/admin/upload', methods=['GET', 'POST'])
def upload_dados():
    """Recebe upload de arquivo Excel com dados anuais da empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    if request.method != 'POST':
        return redirect(url_for('admin.gerenciar_empresas'))

    empresa_id = request.form.get('empresa_id')
    ano = request.form.get('ano')
    arquivo = request.files.get('arquivo')

    # Validação básica
    if not empresa_id or not ano or not arquivo:
        flash("Todos os campos são obrigatórios.", "danger")
        return redirect(url_for('admin.gerenciar_empresas'))

    try:
        from controllers.data_processing.file_processing import process_uploaded_file
        from models.company_manager import CompanyManager

        dados = process_uploaded_file(arquivo)
        d1 = dados[0]
        d2 = dados[1]

        company_manager = CompanyManager()
        company_manager.salvar_itens_empresa(int(empresa_id), int(ano), d1, d2)
        company_manager.close()

        flash(f"Dados da empresa para o ano {ano} foram salvos com sucesso.", "success")
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        flash(f"Erro ao processar o arquivo: {str(e)}", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/consultar', methods=['GET', 'POST'])
def consultar_dados():
    """Consulta dados de uma empresa para um ano específico"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager

    company_manager = CompanyManager()
    empresas = company_manager.listar_todas_empresas()

    data_results = None
    empresa_selecionada = None
    ano_selecionado = None

    if request.method == 'POST':
        empresa_id = request.form.get('empresa_id')
        ano_selecionado = request.form.get('ano')

        if empresa_id and ano_selecionado:
            data_results = company_manager.buscar_dados_empresa(
                int(empresa_id),
                int(ano_selecionado)
            )
            empresa_selecionada = int(empresa_id)

    company_manager.close()

    return render_template(
        'admin/consultar_dados.html',
        empresas=empresas,
        data_results=data_results,
        empresa_selecionada=empresa_selecionada,
        ano_selecionado=ano_selecionado
    )


@admin_bp.route('/admin/deletar_dados', methods=['POST'])
def deletar_dados_empresa():
    """Exclui todos os dados de uma empresa para um ano específico"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    empresa_id = request.form.get('empresa_id')
    ano = request.form.get('ano', type=int)

    if not empresa_id or not ano:
        flash("Parâmetros inválidos para exclusão.", "danger")
        return redirect(url_for('admin.gerenciar_empresas'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    ok = company_manager.excluir_dados_empresa(int(empresa_id), ano)
    company_manager.close()

    if ok:
        flash(f"Dados da empresa para o ano {ano} foram excluídos com sucesso.", "success")
    else:
        flash(f"Erro ao excluir dados da empresa para o ano {ano}.", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))
