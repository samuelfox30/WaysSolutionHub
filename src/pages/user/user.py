from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/selecionar-empresa')
def selecionar_empresa():
    """Página para o usuário selecionar qual empresa deseja acessar"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager

        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))

        if not user_data:
            flash("Erro ao carregar dados do usuário.", "danger")
            return redirect(url_for('index.login'))

        # Busca empresas vinculadas ao usuário
        empresas = user_manager.get_empresas_do_usuario(user_data['id'])
        user_manager.close()

        # Se não tiver empresa vinculada
        if not empresas:
            flash("Você não está vinculado a nenhuma empresa. Entre em contato com o administrador.", "warning")
            return redirect(url_for('user.logout'))

        # Se tiver apenas 1 empresa, redireciona direto pro dashboard
        if len(empresas) == 1:
            session['empresa_id'] = empresas[0]['id']
            session['empresa_nome'] = empresas[0]['nome']
            return redirect(url_for('user.user_dashboard'))

        # Se tiver múltiplas empresas, exibe página de seleção
        return render_template(
            'user/selecionar_empresa.html',
            user=user_data,
            empresas=empresas
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/definir-empresa/<int:empresa_id>')
def definir_empresa(empresa_id):
    """Define a empresa que o usuário quer acessar"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager

        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))

        if not user_data:
            flash("Erro ao carregar dados do usuário.", "danger")
            return redirect(url_for('index.login'))

        # Verifica se o usuário tem acesso a essa empresa
        empresas = user_manager.get_empresas_do_usuario(user_data['id'])
        user_manager.close()

        empresa_encontrada = None
        for empresa in empresas:
            if empresa['id'] == empresa_id:
                empresa_encontrada = empresa
                break

        if not empresa_encontrada:
            flash("Você não tem acesso a esta empresa.", "danger")
            return redirect(url_for('user.selecionar_empresa'))

        # Salva na sessão
        session['empresa_id'] = empresa_id
        session['empresa_nome'] = empresa_encontrada['nome']

        flash(f"Empresa '{empresa_encontrada['nome']}' selecionada com sucesso!", "success")
        return redirect(url_for('user.user_dashboard'))
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/dashboard')
def user_dashboard():
    """Dashboard principal do usuário - mostra dados anuais da empresa selecionada"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager

        # Verifica se tem empresa selecionada
        if 'empresa_id' not in session:
            return redirect(url_for('user.selecionar_empresa'))

        # Pega informações do usuário logado
        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()

        if not user_data:
            flash("Erro ao carregar dados do usuário.", "danger")
            return redirect(url_for('index.login'))

        empresa_id = session.get('empresa_id')
        empresa_nome = session.get('empresa_nome')

        # Busca anos com dados disponíveis para esta empresa
        company_manager = CompanyManager()
        anos_disponiveis = company_manager.get_anos_com_dados(empresa_id)
        company_manager.close()

        return render_template(
            'user/dashboard.html',
            user=user_data,
            empresa_nome=empresa_nome,
            anos_disponiveis=anos_disponiveis
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/dados')
def visualizar_dados():
    """Página de visualização detalhada dos dados anuais da empresa selecionada"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager

        # Verifica se tem empresa selecionada
        if 'empresa_id' not in session:
            return redirect(url_for('user.selecionar_empresa'))

        # Pega informações do usuário logado
        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()

        if not user_data:
            flash("Erro ao carregar dados do usuário.", "danger")
            return redirect(url_for('index.login'))

        empresa_id = session.get('empresa_id')
        empresa_nome = session.get('empresa_nome')

        # Parâmetro de filtro (apenas ano)
        ano_selecionado = request.args.get('ano', type=int)

        data_results = None

        if ano_selecionado:
            # Busca dados específicos do ano para esta empresa
            company_manager = CompanyManager()
            data_results = company_manager.buscar_dados_empresa(
                empresa_id,
                ano_selecionado
            )
            company_manager.close()

        return render_template(
            'user/dados.html',
            user=user_data,
            empresa_nome=empresa_nome,
            data_results=data_results,
            ano_selecionado=ano_selecionado
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/api/dados-detalhados/<int:ano>')
def api_dados_detalhados_ano(ano):
    """API nova que retorna dados organizados por subgrupo para gráficos específicos"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager
        import json

        # Verifica se tem empresa selecionada
        if 'empresa_id' not in session:
            return json.dumps({"error": "Empresa não selecionada"}), 400

        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()

        if not user_data:
            return json.dumps({"error": "Usuário não encontrado"}), 404

        empresa_id = session.get('empresa_id')

        company_manager = CompanyManager()
        data_results = company_manager.buscar_dados_empresa(
            empresa_id,
            ano
        )
        company_manager.close()

        # Organizar dados por SUBGRUPO dentro de cada grupo de viabilidade
        dados_organizados = {}

        # Processar TbItens
        if data_results and data_results.get('TbItens'):
            for item in data_results['TbItens']:
                grupo = item[0]  # 'Viabilidade Real', 'Viabilidade PE', ou 'Viabilidade Ideal'
                subgrupo = item[1]  # 'Geral', 'Receita', 'Controle', etc
                descricao = item[2]
                percentual = float(item[3]) if item[3] else 0
                valor = float(item[4]) if item[4] else 0

                # Inicializar estrutura se não existir
                if grupo not in dados_organizados:
                    dados_organizados[grupo] = {}

                if subgrupo not in dados_organizados[grupo]:
                    dados_organizados[grupo][subgrupo] = []

                # Adicionar item com descrição, valor e percentual
                dados_organizados[grupo][subgrupo].append({
                    "descricao": descricao,
                    "valor": valor,
                    "percentual": percentual
                })

        # Processar outras tabelas
        for tabela in ['TbItensInvestimentos', 'TbItensDividas', 'TbItensInvestimentoGeral', 'TbItensGastosOperacionais']:
            if data_results and data_results.get(tabela):
                for item in data_results[tabela]:
                    grupo = item[0]
                    subgrupo = item[1]
                    descricao = item[2]

                    # Pegar o valor adequado dependendo da tabela
                    if tabela in ['TbItensInvestimentos', 'TbItensDividas']:
                        valor_parcela = float(item[3]) if len(item) > 3 and item[3] else 0
                        valor_juros = float(item[4]) if len(item) > 4 and item[4] else 0
                        valor = float(item[5]) if len(item) > 5 and item[5] else 0  # valor_total_parc
                    elif tabela == 'TbItensInvestimentoGeral':
                        valor = float(item[3]) if len(item) > 3 and item[3] else 0
                    elif tabela == 'TbItensGastosOperacionais':
                        valor = float(item[4]) if len(item) > 4 and item[4] else 0  # valor_mensal
                    else:
                        continue

                    # Inicializar estrutura se não existir
                    if grupo not in dados_organizados:
                        dados_organizados[grupo] = {}

                    if subgrupo not in dados_organizados[grupo]:
                        dados_organizados[grupo][subgrupo] = []

                    # Adicionar item
                    dados_organizados[grupo][subgrupo].append({
                        "descricao": descricao,
                        "valor": valor,
                        "percentual": 0  # Essas tabelas não têm percentual
                    })

        return json.dumps({
            "ano": ano,
            "dados": dados_organizados
        }), 200, {'Content-Type': 'application/json'}

    return json.dumps({"error": "Não autorizado"}), 403


@user_bp.route('/user/api/dados/<int:ano>')
def api_dados_ano(ano):
    """API para retornar dados de um ano específico organizados por grupo de viabilidade"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager
        import json

        # Verifica se tem empresa selecionada
        if 'empresa_id' not in session:
            return json.dumps({"error": "Empresa não selecionada"}), 400

        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()

        if not user_data:
            return json.dumps({"error": "Usuário não encontrado"}), 404

        empresa_id = session.get('empresa_id')

        company_manager = CompanyManager()
        data_results = company_manager.buscar_dados_empresa(
            empresa_id,
            ano
        )
        company_manager.close()

        # Organizar dados por grupo de viabilidade
        dados_por_grupo = {
            "Viabilidade Real": {},
            "Viabilidade PE": {},
            "Viabilidade Ideal": {}
        }

        # Processar TbItens
        if data_results and data_results.get('TbItens'):
            for item in data_results['TbItens']:
                grupo = item[0]  # 'Viabilidade Real', 'Viabilidade PE', ou 'Viabilidade Ideal'
                subgrupo = item[1]  # 'Geral', 'Receita', 'Controle', etc
                descricao = item[2]
                percentual = float(item[3]) if item[3] else 0
                valor = float(item[4]) if item[4] else 0

                if grupo not in dados_por_grupo:
                    continue

                # Criar chave única: subgrupo + descrição
                chave = f"{subgrupo} - {descricao}"

                if chave not in dados_por_grupo[grupo]:
                    dados_por_grupo[grupo][chave] = 0

                dados_por_grupo[grupo][chave] += valor

        # Processar outras tabelas (Investimentos, Dívidas, etc) se necessário
        for tabela in ['TbItensInvestimentos', 'TbItensDividas', 'TbItensInvestimentoGeral', 'TbItensGastosOperacionais']:
            if data_results and data_results.get(tabela):
                for item in data_results[tabela]:
                    grupo = item[0]
                    subgrupo = item[1]
                    descricao = item[2]

                    # Pegar o valor adequado dependendo da tabela
                    if tabela in ['TbItensInvestimentos', 'TbItensDividas']:
                        valor = float(item[5]) if len(item) > 5 and item[5] else 0  # valor_total_parc
                    elif tabela == 'TbItensInvestimentoGeral':
                        valor = float(item[3]) if len(item) > 3 and item[3] else 0
                    elif tabela == 'TbItensGastosOperacionais':
                        valor = float(item[4]) if len(item) > 4 and item[4] else 0  # valor_mensal
                    else:
                        continue

                    if grupo not in dados_por_grupo:
                        continue

                    chave = f"{subgrupo} - {descricao}"

                    if chave not in dados_por_grupo[grupo]:
                        dados_por_grupo[grupo][chave] = 0

                    dados_por_grupo[grupo][chave] += valor

        return json.dumps({
            "ano": ano,
            "grupos": dados_por_grupo
        }), 200, {'Content-Type': 'application/json'}

    return json.dumps({"error": "Não autorizado"}), 403


@user_bp.route('/user/trocar-empresa')
def trocar_empresa():
    """Permite o usuário trocar de empresa"""
    if 'user_email' in session and session.get('user_role') == 'user':
        # Remove empresa da sessão e redireciona para seleção
        session.pop('empresa_id', None)
        session.pop('empresa_nome', None)
        return redirect(url_for('user.selecionar_empresa'))
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/logout')
def logout():
    """Logout do usuário"""
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.pop('empresa_id', None)
    session.pop('empresa_nome', None)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for('index.login'))
