from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify, make_response
from datetime import datetime
from utils.logger import get_logger

# Inicializar logger
logger = get_logger('admin_pages')


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
    nova_senha = request.form.get('senha')  # Campo opcional

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

    # Atualizar dados básicos
    success = user_manager.update_user(user_id, nome, email, telefone, perfil)

    # Atualizar senha se foi fornecida
    password_updated = True
    if nova_senha and nova_senha.strip():  # Se senha foi fornecida e não está vazia
        password_updated = user_manager.update_user_password(user_id, nova_senha)

    user_manager.close()

    if success and password_updated:
        if nova_senha and nova_senha.strip():
            flash("Usuário e senha atualizados com sucesso!", "success")
        else:
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

    # Executar migrações do banco de dados
    company_manager.remover_unique_cnpj()  # Permitir CNPJ duplicado (matriz/filiais)
    company_manager.adicionar_coluna_ativo_se_nao_existir()  # Adicionar coluna ativo

    empresas = company_manager.listar_todas_empresas()

    # Para cada empresa, buscar anos com dados de Viabilidade
    uploads = {}
    for empresa in empresas:
        anos_com_dados = company_manager.get_anos_com_dados(empresa['id'])
        uploads[empresa['id']] = anos_com_dados

    # Para cada empresa, buscar meses com dados de BPO
    uploads_bpo = {}
    for empresa in empresas:
        meses_com_dados_bpo = company_manager.get_meses_com_dados_bpo(empresa['id'])
        uploads_bpo[empresa['id']] = meses_com_dados_bpo

    company_manager.close()

    return render_template('admin/empresas.html', empresas=empresas, uploads=uploads, uploads_bpo=uploads_bpo)


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
        flash("Erro ao cadastrar empresa. Tente novamente.", "danger")

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


@admin_bp.route('/admin/inativar_empresa/<int:empresa_id>', methods=['POST'])
def inativar_empresa(empresa_id):
    """Inativa uma empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    success = company_manager.inativar_empresa(empresa_id)
    company_manager.close()

    if success:
        flash("Empresa inativada com sucesso!", "success")
    else:
        flash("Erro ao inativar empresa.", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/ativar_empresa/<int:empresa_id>', methods=['POST'])
def ativar_empresa(empresa_id):
    """Ativa uma empresa"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    from models.company_manager import CompanyManager
    company_manager = CompanyManager()
    success = company_manager.ativar_empresa(empresa_id)
    company_manager.close()

    if success:
        flash("Empresa ativada com sucesso!", "success")
    else:
        flash("Erro ao ativar empresa.", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/salvar_percentual_mp', methods=['POST'])
def salvar_percentual_mp():
    """Salva percentual MP manual para mês(es) de BPO"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        return jsonify({"error": "Não autorizado"}), 403

    try:
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        meses_percentuais = data.get('meses_percentuais', [])  # Lista de {ano, mes, percentual}

        if not empresa_id or not meses_percentuais:
            return jsonify({"error": "Dados incompletos"}), 400

        from models.company_manager import CompanyManager
        company_manager = CompanyManager()

        sucesso_total = True
        erros = []

        for item in meses_percentuais:
            ano = item.get('ano')
            mes = item.get('mes')
            percentual = item.get('percentual')

            if ano is None or mes is None or percentual is None:
                erros.append(f"Dados incompletos para mês {mes}/{ano}")
                continue

            # Converter percentual para float
            try:
                percentual_float = float(percentual)
            except ValueError:
                erros.append(f"Percentual inválido para {mes}/{ano}: {percentual}")
                continue

            # Salvar no banco
            success = company_manager.atualizar_percentual_mp_manual(
                empresa_id, ano, mes, percentual_float
            )

            if not success:
                sucesso_total = False
                erros.append(f"Erro ao salvar {mes}/{ano}")

        company_manager.close()

        if sucesso_total and len(erros) == 0:
            return jsonify({"success": True, "message": "Percentuais salvos com sucesso!"})
        elif len(erros) > 0:
            return jsonify({"success": False, "errors": erros}), 400
        else:
            return jsonify({"success": False, "message": "Erro ao salvar percentuais"}), 500

    except Exception as e:
        logger.error(f"Erro em salvar_percentual_mp: {e}")
        return jsonify({"error": str(e)}), 500


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


@admin_bp.route('/admin/api/dados-bpo-tabela/<int:empresa_id>')
def api_dados_bpo_tabela(empresa_id):
    """
    API para retornar dados BPO em formato tabular (tipo planilha)
    Filtra por período e retorna itens hierárquicos com dados mensais
    """
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        return jsonify({'error': 'Não autorizado'}), 403

    try:
        from models.company_manager import CompanyManager
        import json

        # Pegar parâmetros do filtro
        mes_inicio = int(request.args.get('mes_inicio', 1))
        ano_inicio = int(request.args.get('ano_inicio', 2025))
        mes_fim = int(request.args.get('mes_fim', 12))
        ano_fim = int(request.args.get('ano_fim', 2025))

        company_manager = CompanyManager()

        # Buscar todos os meses do período
        meses_dados = []
        ano_atual = ano_inicio
        mes_atual = mes_inicio

        while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
            dados = company_manager.buscar_dados_bpo_empresa(empresa_id, ano_atual, mes_atual)
            if dados:
                dados_json = dados['dados']  # Já vem parseado
                meses_dados.append({
                    'mes': mes_atual,
                    'ano': ano_atual,
                    'dados': dados_json
                })

            # Avançar para próximo mês
            mes_atual += 1
            if mes_atual > 12:
                mes_atual = 1
                ano_atual += 1

        company_manager.close()

        if not meses_dados:
            return jsonify({'error': 'Nenhum dado encontrado para o período'}), 404

        # Consolidar itens hierárquicos de todos os meses
        itens_consolidados = {}
        meses_info = []

        for mes_data in meses_dados:
            mes = mes_data['mes']
            ano = mes_data['ano']
            dados = mes_data['dados']

            # Adicionar info do mês
            meses_nomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                          'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            meses_info.append({
                'mes_numero': mes,
                'mes_nome': meses_nomes[mes],
                'ano': ano
            })

            # Processar cada item hierárquico
            for item in dados.get('itens_hierarquicos', []):
                codigo = item['codigo']

                if codigo not in itens_consolidados:
                    itens_consolidados[codigo] = {
                        'codigo': codigo,
                        'nome': item['nome'],
                        'nivel_hierarquia': item['nivel_hierarquia'],
                        'dados_mensais': {}
                    }

                # Adicionar dados deste mês
                if item.get('dados_mensais') and len(item['dados_mensais']) > 0:
                    dados_mes = item['dados_mensais'][0]  # Pega primeiro mês (deveria ser único)
                    chave_mes = f"{ano}_{mes}"
                    itens_consolidados[codigo]['dados_mensais'][chave_mes] = {
                        'mes_numero': mes,
                        'ano': ano,
                        'valor_orcado': dados_mes.get('valor_orcado'),
                        'valor_realizado': dados_mes.get('valor_realizado'),
                        'perc_atingido': dados_mes.get('perc_atingido'),
                        'valor_diferenca': dados_mes.get('valor_diferenca')
                    }

        # Converter para lista ordenada por código
        itens_lista = sorted(itens_consolidados.values(), key=lambda x: x['codigo'])

        # Buscar totais calculados para o período (se existirem)
        totais_calculados = {
            'fluxo_caixa': {},
            'real': {},
            'real_mp': {}
        }

        for mes_data in meses_dados:
            mes = mes_data['mes']
            ano = mes_data['ano']
            dados = mes_data['dados']
            chave_mes = f"{ano}_{mes}"

            # Extrair totais calculados
            totais = dados.get('totais_calculados', {})

            logger.debug(f"Mês {mes}/{ano}: totais keys: {list(totais.keys()) if totais else 'VAZIO'}")
            if totais:
                for cenario in ['fluxo_caixa', 'real', 'real_mp']:
                    if cenario in totais:
                        logger.debug(f"   {cenario}: {list(totais[cenario].keys()) if isinstance(totais[cenario], dict) else type(totais[cenario])}")

            # Os totais_calculados vêm com TODOS os meses do Excel
            # Então apenas precisamos mesclar os dados de cada cenário
            for cenario in ['fluxo_caixa', 'real', 'real_mp']:
                if cenario in totais and isinstance(totais[cenario], dict):
                    # Mesclar todos os meses deste cenário
                    for mes_key, mes_value in totais[cenario].items():
                        # Normalizar chave: converter formato antigo '1' para novo '2025_1'
                        # Se mes_key é apenas número (formato antigo), converter
                        if mes_key.isdigit():
                            # Formato antigo: apenas número do mês
                            mes_num = int(mes_key)
                            # Pegar o ano dos metadados do mes_value ou usar ano atual
                            ano_mes = mes_value.get('ano', ano)
                            chave_normalizada = f"{ano_mes}_{mes_num}"
                        else:
                            # Formato novo: já está como 'ano_mes'
                            chave_normalizada = mes_key

                        # Adicionar apenas se ainda não tiver (evitar duplicação)
                        if chave_normalizada not in totais_calculados[cenario]:
                            totais_calculados[cenario][chave_normalizada] = mes_value

        logger.debug(f"TOTAIS CALCULADOS FINAL:")
        for cenario in ['fluxo_caixa', 'real', 'real_mp']:
            logger.debug(f"   {cenario}: {len(totais_calculados[cenario])} meses - {list(totais_calculados[cenario].keys())}")

        return jsonify({
            'itens': itens_lista,
            'meses': meses_info,
            'totais_calculados': totais_calculados
        })

    except Exception as e:
        logger.error(f"Erro na API dados-bpo-tabela: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/relatorio-pdf/<int:empresa_id>/<int:ano>/<grupo_viabilidade>')
def gerar_relatorio_pdf(empresa_id, ano, grupo_viabilidade):
    """Gera PDF do relatório de viabilidade"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    try:
        from models.company_manager import CompanyManager
        from xhtml2pdf import pisa
        import io

        # Buscar empresa
        company_manager = CompanyManager()
        empresa = company_manager.buscar_empresa_por_id(empresa_id)

        if not empresa:
            flash("Empresa não encontrada.", "danger")
            company_manager.close()
            return redirect(url_for('admin.dashboard_empresa', empresa_id=empresa_id))

        # Buscar template do relatório
        template_data = company_manager.buscar_template_relatorio(empresa_id, ano)
        company_manager.close()

        if not template_data:
            flash(f"Template de relatório não encontrado para o ano {ano}. Por favor, faça o upload de um arquivo Excel com a aba 'Relatório'.", "warning")
            return redirect(url_for('admin.dashboard_empresa', empresa_id=empresa_id))

        # Pegar o texto do template (já vem pronto com os valores)
        conteudo_texto = template_data['template']

        # Adicionar CSS para formatação do PDF
        css_style = """
        <style>
            @page { size: A4; margin: 2cm; }
            body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #333; }
            h1 { color: #2c3e50; font-size: 18pt; margin-top: 1em; }
            h2 { color: #34495e; font-size: 14pt; margin-top: 1em; }
            h3 { color: #34495e; font-size: 12pt; margin-top: 0.8em; }
            table { width: 100%; border-collapse: collapse; margin: 1em 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .header { text-align: center; margin-bottom: 2em; border-bottom: 2px solid #2c3e50; padding-bottom: 1em; }
            .section { margin: 1.5em 0; }
            p { margin: 0.5em 0; }
        </style>
        """

        # Converter quebras de linha do texto em tags HTML <br>
        conteudo_html = conteudo_texto.replace('\n', '<br>\n')

        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {css_style}
        </head>
        <body>
            <div class="header">
                <h1>RELATÓRIO DE VIABILIDADE FINANCEIRA</h1>
                <p><strong>{empresa['nome']}</strong> - Ano: {ano}</p>
                <p>Cenário: {grupo_viabilidade}</p>
            </div>
            <div class="content">
                {conteudo_html}
            </div>
        </body>
        </html>
        """

        # Gerar PDF usando xhtml2pdf (funciona melhor no Windows)
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            html_completo.encode('utf-8'),
            dest=pdf_file,
            encoding='utf-8'
        )

        if pisa_status.err:
            raise Exception(f"Erro ao gerar PDF: {pisa_status.err}")

        pdf_file.seek(0)

        # Retornar PDF como download
        from flask import send_file
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Relatorio_Viabilidade_{empresa["nome"]}_{ano}_{grupo_viabilidade}.pdf'
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao gerar PDF: {str(e)}", "danger")
        return redirect(url_for('admin.dashboard_empresa', empresa_id=empresa_id))


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

    logger.debug(f"Dados organizados para API: {len(dados_organizados)} grupos")

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
        logger.error(f"Erro ao processar arquivo: {e}")
        flash(f"Erro ao processar o arquivo: {str(e)}", "danger")

    return redirect(url_for('admin.gerenciar_empresas'))


@admin_bp.route('/admin/upload_bpo', methods=['POST'])
def upload_dados_bpo():
    """Recebe upload de arquivo Excel com dados MENSAIS de BPO Financeiro"""
    if not ('user_email' in session and session.get('user_role') == 'admin'):
        flash("Acesso negado. Você precisa ser um administrador.", "danger")
        return redirect(url_for('index.login'))

    empresa_id = request.form.get('empresa_id')
    arquivo = request.files.get('arquivo')

    # Validação básica
    if not empresa_id or not arquivo:
        flash("Empresa e arquivo são obrigatórios para upload de BPO.", "danger")
        return redirect(url_for('admin.gerenciar_empresas'))

    try:
        from controllers.data_processing.bpo_file_processing import process_bpo_file
        from models.company_manager import CompanyManager

        # Processar arquivo Excel (detecta meses e anos automaticamente do cabeçalho)
        dados_bpo = process_bpo_file(arquivo)
        meses_info = dados_bpo['metadados']['meses_info']
        meses_processados = []

        company_manager = CompanyManager()

        # Salvar cada mês separadamente (agora com mes_numero e ano do cabeçalho)
        for mes_info in meses_info:
            mes_numero = mes_info['mes_numero']
            ano = mes_info['ano']
            chave_mes = f"{ano}_{mes_numero}"  # Ex: "2025_3" para Março 2025

            # Filtrar totais_calculados deste mês
            totais_mes = {}
            totais_calculados = dados_bpo.get('totais_calculados', {})

            for cenario_key in ['fluxo_caixa', 'real', 'real_mp']:
                if cenario_key in totais_calculados:
                    cenario_data = totais_calculados[cenario_key]
                    # Pegar apenas dados deste mês usando chave ano_mes
                    if chave_mes in cenario_data:
                        totais_mes[cenario_key] = {mes_numero: cenario_data[chave_mes]}
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
                    m for m in item['dados_mensais']
                    if m['mes_numero'] == mes_numero and m['ano'] == ano
                ]
                dados_mes['itens_hierarquicos'].append(item_mes)

            # Salvar se tiver dados
            if dados_mes['itens_hierarquicos']:
                sucesso = company_manager.salvar_dados_bpo_empresa(
                    empresa_id=int(empresa_id),
                    ano=ano,
                    mes=mes_numero,
                    dados_processados=dados_mes
                )
                if sucesso:
                    meses_processados.append(f"{mes_info['mes_nome']} {ano}")

        company_manager.close()

        if meses_processados:
            meses_str = ', '.join(meses_processados)
            flash(f"Dados BPO salvos com sucesso! Meses processados: {meses_str}", "success")
        else:
            flash("Nenhum dado BPO foi encontrado na planilha.", "warning")

    except Exception as e:
        logger.error(f"Erro ao processar arquivo BPO: {e}")
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

    logger.debug(f"API DASHBOARD BPO - Empresa {empresa_id}")
    logger.debug(f"Período: {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim}")
    logger.debug(f"DRE selecionado: {tipo_dre}")
    logger.debug(f"Total de meses encontrados no DB: {len(meses_data)}")

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

        logger.debug(f"Processando mês {mes_num}/{ano}")

        # Extrair totais_calculados (nova estrutura)
        totais_calculados = dados.get('totais_calculados', {})

        # Verificar se totais_calculados está vazio ou None
        if not totais_calculados or totais_calculados == {}:
            logger.warning(f"totais_calculados vazio para mês {mes_num}/{ano}")
            logger.info("DICA: Faça upload da planilha novamente para recalcular os dados")
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
                logger.warning(f"{cenario_key.upper()}: cenário vazio ou inválido para mês {mes_num}/{ano}")
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

                    # RECALCULAR DESPESA DO REAL_MP SE EXISTIR PERCENTUAL MANUAL
                    if cenario_key == 'real_mp':
                        percentual_mp_manual = dados.get('percentual_mp_manual')
                        if percentual_mp_manual is not None:
                            # Usar percentual manual: (percentual / 100) * receita
                            despesa_recalculada = (percentual_mp_manual / 100) * receita
                            logger.debug(f"REAL_MP {mes_num}/{ano}: Usando percentual manual {percentual_mp_manual}% → Despesa recalculada: R$ {despesa_recalculada:,.2f} (original: R$ {despesa:,.2f})")
                            despesa = despesa_recalculada
                            geral = receita - despesa  # Recalcular geral também

                    # Acumular totais
                    totais[cenario_key]['receita'] += receita
                    totais[cenario_key]['despesa'] += despesa
                    totais[cenario_key]['geral'] += geral

                    logger.debug(f"{cenario_key.upper()}: Receita: R$ {receita:,.2f}, Despesa: R$ {despesa:,.2f}, Geral: R$ {geral:,.2f}")

                    # Se é o DRE selecionado, guardar para gráfico
                    if cenario_key == tipo_dre:
                        receita_grafico = receita
                        despesa_grafico = despesa
                        geral_grafico = geral
                else:
                    logger.warning(f"{cenario_key.upper()}: estrutura 'realizado' inválida para mês {mes_num}/{ano}")

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
                logger.warning(f"{cenario_key.upper()}: sem dados para mês {mes_num}")

        # Adicionar aos arrays do gráfico
        receitas_mensais.append(receita_grafico)
        despesas_mensais.append(despesa_grafico)
        gerais_mensais.append(geral_grafico)

    logger.debug("TOTAIS ACUMULADOS FINAIS:")
    for dre_key, valores in totais.items():
        logger.debug(f"{dre_key.upper()}: Receita: R$ {valores['receita']:,.2f}, Despesa: R$ {valores['despesa']:,.2f}, Geral: R$ {valores['geral']:,.2f}")

    # Processar categorias de despesa (itens 2.0X)
    categorias_despesa = {}
    total_receita_orcado = 0

    logger.debug("PROCESSANDO CATEGORIAS DE DESPESA")

    try:
        for mes_data in meses_data:
            dados = mes_data['dados']
            itens = dados.get('itens_hierarquicos', [])

            logger.debug(f"Mês {mes_data['mes']}/{mes_data['ano']}: {len(itens)} itens encontrados")

            # Processar cada item (funciona para lista ou dicionário)
            items_to_process = itens if isinstance(itens, list) else itens.items()

            for item in items_to_process:
                # Se for lista, item é o objeto direto
                # Se for dicionário, item é tupla (codigo, item_data)
                if isinstance(itens, list):
                    codigo = item.get('codigo', '')
                    item_data = item
                else:
                    codigo, item_data = item

                # Filtrar apenas itens 2.0X (ex: 2.01, 2.02, não 2.01.01)
                if codigo.startswith('2.') and len(codigo.split('.')) == 2 and codigo.split('.')[0] == '2' and codigo.split('.')[1].startswith('0'):
                    if codigo not in categorias_despesa:
                        categorias_despesa[codigo] = {
                            'nome': item_data.get('nome', codigo),
                            'orcado': 0,
                            'realizado': 0
                        }

                    # Pegar valores de dados_mensais (lista com dados do mês atual)
                    dados_mensais = item_data.get('dados_mensais', [])
                    if dados_mensais and len(dados_mensais) > 0:
                        mes_atual_dados = dados_mensais[0]  # Primeiro elemento tem os dados do mês
                        orcado_val = mes_atual_dados.get('valor_orcado', 0) or 0
                        realizado_val = mes_atual_dados.get('valor_realizado', 0) or 0

                        # Orçado (pegar apenas uma vez, pois se repete para todos os meses)
                        if categorias_despesa[codigo]['orcado'] == 0:
                            categorias_despesa[codigo]['orcado'] = orcado_val

                        # Realizado (somar todos os meses)
                        categorias_despesa[codigo]['realizado'] += realizado_val

            # Pegar total receita orçado (pegar só do primeiro mês, pois se repete)
            if total_receita_orcado == 0:
                totais_calc = dados.get('totais_calculados', {})
                cenario_fc = totais_calc.get(tipo_dre, {})
                if cenario_fc and isinstance(cenario_fc, dict) and len(cenario_fc) > 0:
                    try:
                        primeiro_mes = list(cenario_fc.keys())[0]
                        mes_info = cenario_fc.get(primeiro_mes, {})
                        if isinstance(mes_info, dict):
                            orcamento_info = mes_info.get('orcamento', {})
                            if isinstance(orcamento_info, dict):
                                total_receita_orcado = orcamento_info.get('receita', 0) or 0
                    except (IndexError, KeyError, TypeError) as e:
                        print(f"Erro ao buscar total_receita_orcado: {e}")
                        pass

        # Calcular médias e diferenças
        num_meses = len(meses_data)
        for codigo in categorias_despesa:
            cat = categorias_despesa[codigo]
            # Dividir realizado pela quantidade de meses para ter a MÉDIA
            cat['realizado'] = cat['realizado'] / num_meses if num_meses > 0 else 0
            # Diferença entre média realizada e média prevista (realizado - orçado)
            cat['diferenca'] = cat['realizado'] - cat['orcado']

        logger.debug(f"Total de categorias de despesa: {len(categorias_despesa)}, Total receita orçado: R$ {total_receita_orcado:,.2f}, Meses processados: {num_meses}")
    except Exception as e:
        logger.error(f"Erro ao processar categorias de despesa: {e}")
        import traceback
        traceback.print_exc()
        categorias_despesa = {}
        total_receita_orcado = 0

    # Processar categorias de receita (itens 1.0X)
    categorias_receita = {}

    logger.debug("PROCESSANDO CATEGORIAS DE RECEITA")

    try:
        for mes_data in meses_data:
            dados = mes_data['dados']
            itens = dados.get('itens_hierarquicos', [])

            # Processar cada item (funciona para lista ou dicionário)
            items_to_process = itens if isinstance(itens, list) else itens.items()

            for item in items_to_process:
                # Se for lista, item é o objeto direto
                # Se for dicionário, item é tupla (codigo, item_data)
                if isinstance(itens, list):
                    codigo = item.get('codigo', '')
                    item_data = item
                else:
                    codigo, item_data = item

                # Filtrar apenas itens 1.0X (ex: 1.01, 1.02, não 1.01.01)
                if codigo.startswith('1.') and len(codigo.split('.')) == 2 and codigo.split('.')[0] == '1' and codigo.split('.')[1].startswith('0'):
                    if codigo not in categorias_receita:
                        categorias_receita[codigo] = {
                            'nome': item_data.get('nome', codigo),
                            'orcado': 0,
                            'realizado': 0
                        }

                    # Pegar valores de dados_mensais (lista com dados do mês atual)
                    dados_mensais = item_data.get('dados_mensais', [])
                    if dados_mensais and len(dados_mensais) > 0:
                        mes_atual_dados = dados_mensais[0]  # Primeiro elemento tem os dados do mês
                        orcado_val = mes_atual_dados.get('valor_orcado', 0) or 0
                        realizado_val = mes_atual_dados.get('valor_realizado', 0) or 0

                        # Orçado (pegar apenas uma vez, pois se repete para todos os meses)
                        if categorias_receita[codigo]['orcado'] == 0:
                            categorias_receita[codigo]['orcado'] = orcado_val

                        # Realizado (somar todos os meses)
                        categorias_receita[codigo]['realizado'] += realizado_val

        # Calcular médias e diferenças
        num_meses = len(meses_data)
        for codigo in categorias_receita:
            cat = categorias_receita[codigo]
            # Dividir realizado pela quantidade de meses para ter a MÉDIA
            cat['realizado'] = cat['realizado'] / num_meses if num_meses > 0 else 0
            # Diferença entre média realizada e média prevista (realizado - orçado)
            cat['diferenca'] = cat['realizado'] - cat['orcado']

        logger.debug(f"Total de categorias de receita: {len(categorias_receita)}")
    except Exception as e:
        logger.error(f"Erro ao processar categorias de receita: {e}")
        import traceback
        traceback.print_exc()
        categorias_receita = {}

    return jsonify({
        'totais_acumulados': totais,
        'totais_orcamento': totais_orcamento,
        'num_meses': len(meses_data),
        'meses': labels_meses,
        'meses_data': meses_data,  # Incluir dados completos para modal de percentual MP
        'receitas': receitas_mensais,
        'despesas': despesas_mensais,
        'gerais': gerais_mensais,
        'categorias_despesa': categorias_despesa,
        'categorias_receita': categorias_receita,
        'total_receita_orcado': total_receita_orcado
    })


@admin_bp.route('/admin/gerar_pdf_bpo/<int:empresa_id>')
def gerar_pdf_bpo(empresa_id):
    """Gera relatório PDF do dashboard BPO"""
    logger.info(f"[PDF BPO ADMIN] Iniciando geração de PDF BPO para empresa_id={empresa_id}")

    if not ('user_email' in session and session.get('user_role') == 'admin'):
        logger.warning(f"[PDF BPO ADMIN] Acesso negado para empresa_id={empresa_id}")
        return "Acesso negado", 403

    try:
        logger.info(f"[PDF BPO ADMIN] Importando dependências...")
        from models.company_manager import CompanyManager
        from weasyprint import HTML, CSS
        from datetime import datetime
        import io
        logger.info(f"[PDF BPO ADMIN] Dependências importadas com sucesso")

        # Buscar dados da empresa
        logger.info(f"[PDF BPO ADMIN] Buscando dados da empresa {empresa_id}...")
        company_manager = CompanyManager()
        empresa = company_manager.buscar_empresa_por_id(empresa_id)
        logger.info(f"[PDF BPO ADMIN] Empresa encontrada: {empresa['nome'] if empresa else 'Não encontrada'}")

        if not empresa:
            company_manager.close()
            logger.error(f"[PDF BPO ADMIN] Empresa {empresa_id} não encontrada")
            return "Empresa não encontrada", 404

        # Pegar parâmetros do filtro
        ano_inicio = int(request.args.get('ano_inicio', 2025))
        mes_inicio = int(request.args.get('mes_inicio', 1))
        ano_fim = int(request.args.get('ano_fim', 2025))
        mes_fim = int(request.args.get('mes_fim', 12))
        tipo_dre = request.args.get('tipo_dre', 'fluxo_caixa')
        logger.info(f"[PDF BPO ADMIN] Parâmetros: {ano_inicio}/{mes_inicio} a {ano_fim}/{mes_fim}, DRE: {tipo_dre}")

        # ========== PROCESSAR DADOS BPO (mesma lógica da API) ==========

        # Buscar todos os meses
        logger.info(f"[PDF BPO ADMIN] Buscando dados BPO dos meses...")
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

        logger.info(f"[PDF BPO ADMIN] {len(meses_data)} meses encontrados com dados BPO")

        # Inicializar totais acumulados
        logger.info(f"[PDF BPO ADMIN] Processando dados para o relatório...")
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

            # Extrair totais_calculados
            totais_calculados = dados.get('totais_calculados', {})

            if not totais_calculados or totais_calculados == {}:
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

                if not cenario_data or not isinstance(cenario_data, dict):
                    continue

                # Pegar dados do mês
                mes_dados = cenario_data.get(mes_num, cenario_data.get(str(mes_num), {}))

                if mes_dados and isinstance(mes_dados, dict):
                    # Extrair valores realizados
                    realizado = mes_dados.get('realizado', {})
                    if isinstance(realizado, dict):
                        receita = realizado.get('receita', 0) or 0
                        despesa = realizado.get('despesa', 0) or 0
                        geral = realizado.get('geral', 0) or 0

                        # RECALCULAR DESPESA DO REAL_MP SE EXISTIR PERCENTUAL MANUAL
                        if cenario_key == 'real_mp':
                            percentual_mp_manual = dados.get('percentual_mp_manual')
                            if percentual_mp_manual is not None:
                                despesa_recalculada = (percentual_mp_manual / 100) * receita
                                despesa = despesa_recalculada
                                geral = receita - despesa

                        # Acumular totais
                        totais[cenario_key]['receita'] += receita
                        totais[cenario_key]['despesa'] += despesa
                        totais[cenario_key]['geral'] += geral

                        # Se é o DRE selecionado, guardar para gráfico
                        if cenario_key == tipo_dre:
                            receita_grafico = receita
                            despesa_grafico = despesa
                            geral_grafico = geral

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

            # Adicionar aos arrays do gráfico
            receitas_mensais.append(receita_grafico)
            despesas_mensais.append(despesa_grafico)
            gerais_mensais.append(geral_grafico)

        # Processar categorias de despesa (itens 2.0X)
        categorias_despesa = {}

        for mes_data in meses_data:
            dados = mes_data['dados']
            itens = dados.get('itens_hierarquicos', [])

            items_to_process = itens if isinstance(itens, list) else itens.items()

            for item in items_to_process:
                if isinstance(itens, list):
                    codigo = item.get('codigo', '')
                    item_data = item
                else:
                    codigo, item_data = item

                # Filtrar apenas itens 2.0X
                if codigo.startswith('2.') and len(codigo.split('.')) == 2 and codigo.split('.')[0] == '2' and codigo.split('.')[1].startswith('0'):
                    if codigo not in categorias_despesa:
                        categorias_despesa[codigo] = {
                            'nome': item_data.get('nome', codigo),
                            'orcado': 0,
                            'realizado': 0
                        }

                    dados_mensais = item_data.get('dados_mensais', [])
                    if dados_mensais and len(dados_mensais) > 0:
                        mes_atual_dados = dados_mensais[0]
                        orcado_val = mes_atual_dados.get('valor_orcado', 0) or 0
                        realizado_val = mes_atual_dados.get('valor_realizado', 0) or 0

                        if categorias_despesa[codigo]['orcado'] == 0:
                            categorias_despesa[codigo]['orcado'] = orcado_val

                        categorias_despesa[codigo]['realizado'] += realizado_val

        # Calcular médias de categorias de despesa
        num_meses = len(meses_data)
        for codigo in categorias_despesa:
            cat = categorias_despesa[codigo]
            cat['realizado'] = cat['realizado'] / num_meses if num_meses > 0 else 0
            cat['diferenca'] = cat['realizado'] - cat['orcado']

        # Processar categorias de receita (itens 1.0X)
        categorias_receita = {}

        for mes_data in meses_data:
            dados = mes_data['dados']
            itens = dados.get('itens_hierarquicos', [])

            items_to_process = itens if isinstance(itens, list) else itens.items()

            for item in items_to_process:
                if isinstance(itens, list):
                    codigo = item.get('codigo', '')
                    item_data = item
                else:
                    codigo, item_data = item

                # Filtrar apenas itens 1.0X
                if codigo.startswith('1.') and len(codigo.split('.')) == 2 and codigo.split('.')[0] == '1' and codigo.split('.')[1].startswith('0'):
                    if codigo not in categorias_receita:
                        categorias_receita[codigo] = {
                            'nome': item_data.get('nome', codigo),
                            'orcado': 0,
                            'realizado': 0
                        }

                    dados_mensais = item_data.get('dados_mensais', [])
                    if dados_mensais and len(dados_mensais) > 0:
                        mes_atual_dados = dados_mensais[0]
                        orcado_val = mes_atual_dados.get('valor_orcado', 0) or 0
                        realizado_val = mes_atual_dados.get('valor_realizado', 0) or 0

                        if categorias_receita[codigo]['orcado'] == 0:
                            categorias_receita[codigo]['orcado'] = orcado_val

                        categorias_receita[codigo]['realizado'] += realizado_val

        # Calcular médias de categorias de receita
        for codigo in categorias_receita:
            cat = categorias_receita[codigo]
            cat['realizado'] = cat['realizado'] / num_meses if num_meses > 0 else 0
            cat['diferenca'] = cat['realizado'] - cat['orcado']

        # Renderizar template HTML para PDF
        logger.info(f"[PDF BPO ADMIN] Renderizando template HTML...")
        html_content = render_template('admin/relatorio_bpo_pdf.html',
            empresa=empresa,
            ano_inicio=ano_inicio,
            mes_inicio=mes_inicio,
            ano_fim=ano_fim,
            mes_fim=mes_fim,
            tipo_dre=tipo_dre,
            data_geracao=datetime.now().strftime('%d/%m/%Y %H:%M'),
            totais=totais,
            totais_orcamento=totais_orcamento,
            num_meses=num_meses,
            labels_meses=labels_meses,
            receitas_mensais=receitas_mensais,
            despesas_mensais=despesas_mensais,
            gerais_mensais=gerais_mensais,
            categorias_despesa=categorias_despesa,
            categorias_receita=categorias_receita
        )
        logger.info(f"[PDF BPO ADMIN] Template renderizado com sucesso")

        # Gerar PDF
        logger.info(f"[PDF BPO ADMIN] Iniciando conversão HTML para PDF com WeasyPrint...")
        pdf = HTML(string=html_content).write_pdf()
        logger.info(f"[PDF BPO ADMIN] PDF gerado com sucesso, tamanho: {len(pdf)} bytes")

        # Retornar PDF como resposta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Relatorio_BPO_{empresa["nome"]}_{datetime.now().strftime("%Y%m%d")}.pdf'

        company_manager.close()
        logger.info(f"[PDF BPO ADMIN] PDF enviado com sucesso para empresa {empresa['nome']}")
        return response

    except Exception as e:
        logger.error(f"[PDF BPO ADMIN] ERRO ao gerar PDF para empresa_id={empresa_id}: {str(e)}", exc_info=True)
        return f"Erro ao gerar PDF: {str(e)}", 500

@admin_bp.route('/admin/gerar_pdf_viabilidade/<int:empresa_id>')
def gerar_pdf_viabilidade(empresa_id):
    """Gera relatório PDF comparando os 3 grupos de viabilidade"""
    logger.info(f"[PDF VIAB ADMIN] Iniciando geração de PDF Viabilidade para empresa_id={empresa_id}")

    if not ('user_email' in session and session.get('user_role') == 'admin'):
        logger.warning(f"[PDF VIAB ADMIN] Acesso negado para empresa_id={empresa_id}")
        return "Acesso negado", 403

    try:
        logger.info(f"[PDF VIAB ADMIN] Importando dependências...")
        from models.company_manager import CompanyManager
        from weasyprint import HTML
        from datetime import datetime
        logger.info(f"[PDF VIAB ADMIN] Dependências importadas com sucesso")

        # Buscar dados da empresa
        logger.info(f"[PDF VIAB ADMIN] Buscando dados da empresa {empresa_id}...")
        company_manager = CompanyManager()
        empresa = company_manager.buscar_empresa_por_id(empresa_id)
        logger.info(f"[PDF VIAB ADMIN] Empresa encontrada: {empresa['nome'] if empresa else 'Não encontrada'}")

        if not empresa:
            company_manager.close()
            logger.error(f"[PDF VIAB ADMIN] Empresa {empresa_id} não encontrada")
            return "Empresa não encontrada", 404

        # Obter ano selecionado
        ano_selecionado = int(request.args.get('ano_selecionado', datetime.now().year))
        logger.info(f"[PDF VIAB ADMIN] Ano selecionado: {ano_selecionado}")

        # Buscar dados dos 3 grupos de viabilidade
        logger.info(f"[PDF VIAB ADMIN] Buscando dados de viabilidade...")
        dados_completos = company_manager.buscar_dados_empresa(empresa_id, ano_selecionado)

        if not dados_completos:
            company_manager.close()
            logger.error(f"[PDF VIAB ADMIN] Sem dados de viabilidade para empresa {empresa_id}, ano {ano_selecionado}")
            return "Sem dados de viabilidade disponíveis para este ano", 404

        # Processar dados dos 3 grupos
        logger.info(f"[PDF VIAB ADMIN] Processando dados dos 3 grupos de viabilidade...")
        grupos_info = {
            'Viabilidade Real': {'receita': 0, 'despesa': 0, 'resultado': 0, 'subgrupos': {}},
            'Viabilidade PE': {'receita': 0, 'despesa': 0, 'resultado': 0, 'subgrupos': {}},
            'Viabilidade Ideal': {'receita': 0, 'despesa': 0, 'resultado': 0, 'subgrupos': {}}
        }

        # Processar cada grupo
        for grupo_nome, grupo_data in dados_completos.get('dados', {}).items():
            if grupo_nome not in grupos_info:
                continue

            for subgrupo_nome, itens in grupo_data.items():
                total_subgrupo = sum(item.get('valor', 0) for item in itens)

                # Classificar como receita ou despesa baseado no nome do subgrupo
                if subgrupo_nome in ['Receita', 'Geral']:
                    grupos_info[grupo_nome]['receita'] += total_subgrupo
                else:
                    grupos_info[grupo_nome]['despesa'] += total_subgrupo

                # Armazenar detalhes do subgrupo
                if subgrupo_nome not in grupos_info[grupo_nome]['subgrupos']:
                    grupos_info[grupo_nome]['subgrupos'][subgrupo_nome] = []
                grupos_info[grupo_nome]['subgrupos'][subgrupo_nome].extend(itens)

        # Calcular resultados
        for grupo in grupos_info.values():
            grupo['resultado'] = grupo['receita'] - grupo['despesa']

        logger.info(f"[PDF VIAB ADMIN] Dados processados com sucesso")

        # Data de geração
        data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')

        # Renderizar template
        logger.info(f"[PDF VIAB ADMIN] Renderizando template HTML...")
        html_content = render_template(
            'admin/relatorio_viabilidade_pdf.html',
            empresa=empresa,
            ano_selecionado=ano_selecionado,
            grupos_info=grupos_info,
            data_geracao=data_geracao
        )
        logger.info(f"[PDF VIAB ADMIN] Template renderizado com sucesso")

        # Gerar PDF
        logger.info(f"[PDF VIAB ADMIN] Iniciando conversão HTML para PDF com WeasyPrint...")
        pdf = HTML(string=html_content).write_pdf()
        logger.info(f"[PDF VIAB ADMIN] PDF gerado com sucesso, tamanho: {len(pdf)} bytes")

        # Retornar PDF
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Relatorio_Viabilidade_{empresa["nome"]}_{ano_selecionado}.pdf'

        company_manager.close()
        logger.info(f"[PDF VIAB ADMIN] PDF enviado com sucesso para empresa {empresa['nome']}")
        return response

    except Exception as e:
        logger.error(f"[PDF VIAB ADMIN] ERRO ao gerar PDF para empresa_id={empresa_id}: {str(e)}", exc_info=True)
        return f"Erro ao gerar PDF: {str(e)}", 500

