from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
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
        return jsonify({"error": "Não autorizado"}), 403

    from models.company_manager import CompanyManager

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

    # Processar Investimentos (TODOS OS CAMPOS)
    if data_results and data_results.get('TbItensInvestimentos'):
        for item in data_results['TbItensInvestimentos']:
            grupo = item[0]
            subgrupo = item[1]
            descricao = item[2]
            parcela = float(item[3]) if len(item) > 3 and item[3] else 0
            juros = float(item[4]) if len(item) > 4 and item[4] else 0
            total = float(item[5]) if len(item) > 5 and item[5] else 0

            if grupo not in dados_organizados:
                dados_organizados[grupo] = {}

            if subgrupo not in dados_organizados[grupo]:
                dados_organizados[grupo][subgrupo] = []

            dados_organizados[grupo][subgrupo].append({
                "descricao": descricao,
                "parcela": parcela,
                "juros": juros,
                "valor": total,
                "percentual": 0
            })

    # Processar Dívidas (TODOS OS CAMPOS)
    if data_results and data_results.get('TbItensDividas'):
        for item in data_results['TbItensDividas']:
            grupo = item[0]
            subgrupo = item[1]
            descricao = item[2]
            parcela = float(item[3]) if len(item) > 3 and item[3] else 0
            juros = float(item[4]) if len(item) > 4 and item[4] else 0
            total = float(item[5]) if len(item) > 5 and item[5] else 0

            if grupo not in dados_organizados:
                dados_organizados[grupo] = {}

            if subgrupo not in dados_organizados[grupo]:
                dados_organizados[grupo][subgrupo] = []

            dados_organizados[grupo][subgrupo].append({
                "descricao": descricao,
                "parcela": parcela,
                "juros": juros,
                "valor": total,
                "percentual": 0
            })

    # Processar Investimento Geral
    if data_results and data_results.get('TbItensInvestimentoGeral'):
        for item in data_results['TbItensInvestimentoGeral']:
            grupo = item[0]
            subgrupo = item[1]
            descricao = item[2]
            valor = float(item[3]) if len(item) > 3 and item[3] else 0

            if grupo not in dados_organizados:
                dados_organizados[grupo] = {}

            if subgrupo not in dados_organizados[grupo]:
                dados_organizados[grupo][subgrupo] = []

            dados_organizados[grupo][subgrupo].append({
                "descricao": descricao,
                "valor": valor,
                "percentual": 0
            })

    # Processar Gastos Operacionais (COM NOME DIFERENCIADO)
    if data_results and data_results.get('TbItensGastosOperacionais'):
        for item in data_results['TbItensGastosOperacionais']:
            grupo = item[0]
            subgrupo_original = item[1]  # Pode ser "GastosOperacionais"
            descricao = item[2]
            custo_km = float(item[3]) if len(item) > 3 and item[3] else 0
            custo_mensal = float(item[4]) if len(item) > 4 and item[4] else 0

            # Renomear subgrupo para "Gastos Operacionais Veículos" para diferenciar
            subgrupo = 'Gastos Operacionais Veículos'

            if grupo not in dados_organizados:
                dados_organizados[grupo] = {}

            if subgrupo not in dados_organizados[grupo]:
                dados_organizados[grupo][subgrupo] = []

            dados_organizados[grupo][subgrupo].append({
                "descricao": descricao,
                "custo_km": custo_km,
                "valor": custo_mensal,
                "percentual": 0
            })

    print("Dados organizados para API:", dados_organizados)

    return jsonify({
        "ano": ano,
        "dados": dados_organizados
    })


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


@admin_bp.route('/admin/upload_bpo', methods=['POST'])
def upload_dados_bpo():
    """Recebe upload de arquivo Excel com dados MENSAIS de BPO Financeiro"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    empresa_id = request.form.get('empresa_id')
    ano = request.form.get('ano')
    arquivo = request.files.get('arquivo')

    # Validação básica
    if not empresa_id or not ano or not arquivo:
        flash("Empresa, ano e arquivo são obrigatórios para upload de BPO.", "danger")
        return redirect(url_for('admin.gerenciar_empresas'))

    try:
        from controllers.data_processing.bpo_file_processing import process_bpo_file
        from models.company_manager import CompanyManager

        # Processar arquivo Excel (detecta meses automaticamente)
        dados_bpo = process_bpo_file(arquivo)
        num_meses = dados_bpo['metadados']['num_meses']
        meses_processados = []

        company_manager = CompanyManager()

        # Salvar cada mês separadamente
        for mes_num in range(1, num_meses + 1):
            # Filtrar totais_calculados deste mês
            totais_mes = {}
            totais_calculados = dados_bpo.get('totais_calculados', {})

            for cenario_key in ['fluxo_caixa', 'real', 'real_mp']:
                if cenario_key in totais_calculados:
                    cenario_data = totais_calculados[cenario_key]
                    # Pegar apenas dados do mês atual (mes_num é a chave)
                    if mes_num in cenario_data:
                        totais_mes[cenario_key] = {mes_num: cenario_data[mes_num]}
                    else:
                        totais_mes[cenario_key] = {}
                else:
                    totais_mes[cenario_key] = {}

            # Filtrar dados deste mês
            dados_mes = {
                'itens_hierarquicos': [],
                'totais_calculados': totais_mes,
                'metadados': dados_bpo['metadados']
            }

            # Para cada item hierárquico, pegar só dados do mês atual
            for item in dados_bpo['itens_hierarquicos']:
                item_mes = item.copy()
                item_mes['dados_mensais'] = [
                    m for m in item['dados_mensais'] if m['mes_numero'] == mes_num
                ]
                dados_mes['itens_hierarquicos'].append(item_mes)

            # Salvar se tiver dados
            if dados_mes['itens_hierarquicos']:
                sucesso = company_manager.salvar_dados_bpo_empresa(
                    empresa_id=int(empresa_id),
                    ano=int(ano),
                    mes=mes_num,
                    dados_processados=dados_mes
                )
                if sucesso:
                    meses_processados.append(mes_num)

        company_manager.close()

        if meses_processados:
            meses_nomes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun',
                          7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            meses_str = ', '.join([meses_nomes[m] for m in meses_processados])
            flash(f"Dados BPO salvos para {len(meses_processados)} meses ({meses_str}/{ano})!", "success")
        else:
            flash("Nenhum dado BPO foi encontrado na planilha.", "warning")

    except Exception as e:
        print(f"Erro ao processar arquivo BPO: {e}")
        flash(f"Erro ao processar o arquivo BPO: {str(e)}", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/consultar', methods=['GET', 'POST'])
def consultar_dados():
    """Consulta dados de VIABILIDADE FINANCEIRA de uma empresa para um ano específico"""
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


@admin_bp.route('/admin/consultar_bpo', methods=['GET', 'POST'])
def consultar_dados_bpo():
    """Consulta dados de BPO FINANCEIRO de uma empresa para um período específico"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager

    company_manager = CompanyManager()
    empresas = company_manager.listar_todas_empresas()

    data_results = None
    empresa_selecionada = None
    ano_selecionado = None
    mes_selecionado = None

    # Aceitar empresa_id por GET (quando vem do botão)
    empresa_id = request.args.get('empresa_id') or request.form.get('empresa_id')
    if empresa_id:
        empresa_selecionada = int(empresa_id)

    if request.method == 'POST':
        ano_selecionado = request.form.get('ano')
        mes_selecionado = request.form.get('mes')

        if empresa_id and ano_selecionado and mes_selecionado:
            data_results = company_manager.buscar_dados_bpo_empresa(
                int(empresa_id),
                int(ano_selecionado),
                int(mes_selecionado)
            )
            empresa_selecionada = int(empresa_id)

    company_manager.close()

    return render_template(
        'admin/consultar_bpo.html',
        empresas=empresas,
        data_results=data_results,
        empresa_selecionada=empresa_selecionada,
        ano_selecionado=ano_selecionado,
        mes_selecionado=mes_selecionado
    )


@admin_bp.route('/admin/deletar_dados', methods=['POST'])
def deletar_dados_empresa():
    """Exclui todos os dados de VIABILIDADE de uma empresa para um ano específico"""
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
        flash(f"Dados de Viabilidade da empresa para o ano {ano} foram excluídos com sucesso.", "success")
    else:
        flash(f"Erro ao excluir dados de Viabilidade da empresa para o ano {ano}.", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/deletar_dados_bpo', methods=['POST'])
def deletar_dados_bpo_empresa():
    """Exclui todos os dados de BPO de uma empresa para um período específico"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    empresa_id = request.form.get('empresa_id')
    ano = request.form.get('ano', type=int)
    mes = request.form.get('mes', type=int)

    if not empresa_id or not ano or not mes:
        flash("Parâmetros inválidos para exclusão de dados BPO.", "danger")
        return redirect(url_for('admin.gerenciar_empresas'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    sucesso = company_manager.excluir_dados_bpo_empresa(int(empresa_id), ano, mes)
    company_manager.close()

    if sucesso:
        flash(f"Dados de BPO para {mes}/{ano} foram excluídos com sucesso.", "success")
    else:
        flash(f"Erro ao excluir dados de BPO para {mes}/{ano}.", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/dashboard-bpo/<int:empresa_id>')
def dashboard_bpo(empresa_id):
    """Dashboard BPO de uma empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    empresa = company_manager.buscar_empresa_por_id(empresa_id)
    company_manager.close()

    if not empresa:
        flash("Empresa não encontrada.", "danger")
        return redirect(url_for('admin.gerenciar_empresas'))

    return render_template(
        'admin/dashboard_bpo.html',
        empresa=empresa,
        empresa_id=empresa_id
    )


@admin_bp.route('/admin/api/dados-bpo/<int:empresa_id>')
def api_dados_bpo(empresa_id):
    """API retorna dados BPO processados para dashboard"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        return jsonify({"error": "Não autorizado"}), 403

    ano_inicio = int(request.args.get('ano_inicio', 2025))
    mes_inicio = int(request.args.get('mes_inicio', 1))
    ano_fim = int(request.args.get('ano_fim', 2025))
    mes_fim = int(request.args.get('mes_fim', 12))
    tipo_dre = request.args.get('tipo_dre', 'fluxo_caixa')

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()

    # Buscar todos os meses
    meses_data = []
    ano_atual = ano_inicio
    mes_atual = mes_inicio

    while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
        dados = company_manager.buscar_dados_bpo_empresa(empresa_id, ano_atual, mes_atual)
        if dados:
            meses_data.append({
                'ano': ano_atual,
                'mes': mes_atual,
                'dados': dados['dados']
            })
        mes_atual += 1
        if mes_atual > 12:
            mes_atual = 1
            ano_atual += 1

    company_manager.close()

    print("\n" + "="*80)
    print(f"🔍 DEBUG API DASHBOARD BPO - Empresa {empresa_id}")
    print("="*80)
    print(f"Período: {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim}")
    print(f"DRE selecionado: {tipo_dre}")
    print(f"Total de meses encontrados no DB: {len(meses_data)}")

    # Inicializar totais acumulados
    totais = {
        'fluxo_caixa': {'receita': 0, 'despesa': 0, 'geral': 0},
        'real': {'receita': 0, 'despesa': 0, 'geral': 0},
        'real_mp': {'receita': 0, 'despesa': 0, 'geral': 0}
    }

    # Totais de orçamento (para média prevista)
    totais_orcamento = {
        'fluxo_caixa': {'receita': 0, 'despesa': 0, 'geral': 0},
        'real': {'receita': 0, 'despesa': 0, 'geral': 0},
        'real_mp': {'receita': 0, 'despesa': 0, 'geral': 0}
    }

    # Arrays para gráficos (por mês, do DRE selecionado)
    labels_meses = []
    receitas_mensais = []
    despesas_mensais = []
    gerais_mensais = []

    # Nomes dos meses
    nomes_meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }

    for mes_data in meses_data:
        mes_num = mes_data['mes']
        ano = mes_data['ano']
        dados = mes_data['dados']

        # Label para gráfico (formato: Janeiro/25)
        nome_mes = nomes_meses.get(mes_num, str(mes_num))
        ano_curto = str(ano)[-2:]  # Pega só os 2 últimos dígitos
        labels_meses.append(f"{nome_mes}/{ano_curto}")

        print(f"\n📅 MÊS {mes_num}/{ano}:")

        # Extrair totais_calculados (nova estrutura)
        totais_calculados = dados.get('totais_calculados', {})

        # Verificar se totais_calculados está vazio ou None
        if not totais_calculados or totais_calculados == {}:
            print(f"   ⚠️  totais_calculados vazio para este mês")
            print(f"   💡 DICA: Faça upload da planilha novamente para recalcular os dados")
            receitas_mensais.append(0)
            despesas_mensais.append(0)
            gerais_mensais.append(0)
            continue

        # Variáveis para gráfico deste mês
        receita_grafico = 0
        despesa_grafico = 0
        geral_grafico = 0

        # Processar cada cenário (fluxo_caixa, real, real_mp)
        for cenario_key in ['fluxo_caixa', 'real', 'real_mp']:
            cenario_data = totais_calculados.get(cenario_key, {})

            # Verificar se o cenário existe e não está vazio
            if not cenario_data or not isinstance(cenario_data, dict):
                print(f"   ⚠️  {cenario_key.upper()}: cenário vazio ou inválido")
                continue

            # Pegar dados do mês (a chave pode ser string ou int)
            # Tentar primeiro como int, depois como string
            mes_dados = cenario_data.get(mes_num, cenario_data.get(str(mes_num), {}))

            if mes_dados and isinstance(mes_dados, dict):
                # Extrair valores realizados
                realizado = mes_dados.get('realizado', {})
                if isinstance(realizado, dict):
                    receita = realizado.get('receita', 0) or 0
                    despesa = realizado.get('despesa', 0) or 0
                    geral = realizado.get('geral', 0) or 0

                    # Acumular totais
                    totais[cenario_key]['receita'] += receita
                    totais[cenario_key]['despesa'] += despesa
                    totais[cenario_key]['geral'] += geral

                    print(f"   {cenario_key.upper()}:")
                    print(f"      Receita: R$ {receita:,.2f}")
                    print(f"      Despesa: R$ {despesa:,.2f}")
                    print(f"      Geral:   R$ {geral:,.2f}")

                    # Se é o DRE selecionado, guardar para gráfico
                    if cenario_key == tipo_dre:
                        receita_grafico = receita
                        despesa_grafico = despesa
                        geral_grafico = geral
                else:
                    print(f"   ⚠️  {cenario_key.upper()}: estrutura 'realizado' inválida")

                # Extrair valores de orçamento
                orcamento = mes_dados.get('orcamento', {})
                if isinstance(orcamento, dict):
                    receita_orc = orcamento.get('receita', 0) or 0
                    despesa_orc = orcamento.get('despesa', 0) or 0
                    geral_orc = orcamento.get('geral', 0) or 0

                    # Acumular orçamento
                    totais_orcamento[cenario_key]['receita'] += receita_orc
                    totais_orcamento[cenario_key]['despesa'] += despesa_orc
                    totais_orcamento[cenario_key]['geral'] += geral_orc
            else:
                print(f"   ⚠️  {cenario_key.upper()}: sem dados para mês {mes_num}")

        # Adicionar aos arrays do gráfico
        receitas_mensais.append(receita_grafico)
        despesas_mensais.append(despesa_grafico)
        gerais_mensais.append(geral_grafico)

    print("\n" + "="*80)
    print("📊 TOTAIS ACUMULADOS FINAIS:")
    print("="*80)
    for dre_key, valores in totais.items():
        print(f"{dre_key.upper()}:")
        print(f"   Receita: R$ {valores['receita']:,.2f}")
        print(f"   Despesa: R$ {valores['despesa']:,.2f}")
        print(f"   Geral:   R$ {valores['geral']:,.2f}")
    print("="*80 + "\n")

    # Processar categorias de despesa (itens 2.0X)
    categorias_despesa = {}
    total_receita_orcado = 0

    for mes_data in meses_data:
        dados = mes_data['dados']
        itens = dados.get('itens_hierarquicos', {})

        # Processar cada item
        for codigo, item_data in itens.items():
            # Filtrar apenas itens 2.0X (ex: 2.01, 2.02, não 2.01.01)
            if codigo.startswith('2.0') and codigo.count('.') == 1:
                if codigo not in categorias_despesa:
                    categorias_despesa[codigo] = {
                        'nome': item_data.get('nome', codigo),
                        'orcado': 0,
                        'realizado': 0
                    }

                # Pegar valores dos meses
                meses_item = item_data.get('meses', {})
                for mes_key, mes_valores in meses_item.items():
                    # Orçado (pegar apenas uma vez, pois se repete)
                    if categorias_despesa[codigo]['orcado'] == 0:
                        categorias_despesa[codigo]['orcado'] = mes_valores.get('orcado', 0) or 0

                    # Realizado (somar todos os meses)
                    categorias_despesa[codigo]['realizado'] += mes_valores.get('realizado', 0) or 0

        # Pegar total receita orçado (pegar só do primeiro mês, pois se repete)
        if total_receita_orcado == 0:
            totais_calc = dados.get('totais_calculados', {})
            cenario_fc = totais_calc.get(tipo_dre, {})
            if cenario_fc:
                primeiro_mes = list(cenario_fc.keys())[0] if cenario_fc else None
                if primeiro_mes:
                    mes_info = cenario_fc.get(primeiro_mes, {})
                    if isinstance(mes_info, dict):
                        orcamento_info = mes_info.get('orcamento', {})
                        if isinstance(orcamento_info, dict):
                            total_receita_orcado = orcamento_info.get('receita', 0) or 0

    # Calcular diferenças
    for codigo in categorias_despesa:
        cat = categorias_despesa[codigo]
        cat['diferenca'] = cat['realizado'] - cat['orcado']

    return jsonify({
        'totais_acumulados': totais,
        'totais_orcamento': totais_orcamento,
        'num_meses': len(meses_data),
        'meses': labels_meses,
        'receitas': receitas_mensais,
        'despesas': despesas_mensais,
        'gerais': gerais_mensais,
        'categorias_despesa': categorias_despesa,
        'total_receita_orcado': total_receita_orcado
    })

