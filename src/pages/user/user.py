from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/dashboard')
def user_dashboard():
    """Dashboard principal do usuário - agora mostra dados anuais"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager
        
        # Pega informações do usuário logado
        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()
        
        if not user_data:
            flash("Erro ao carregar dados do usuário.", "danger")
            return redirect(url_for('index.login'))
        
        # Busca anos com dados disponíveis
        company_manager = CompanyManager()
        anos_disponiveis = company_manager.get_anos_com_dados(user_data['id'])
        company_manager.close()
        
        return render_template(
            'user/dashboard.html',
            user=user_data,
            anos_disponiveis=anos_disponiveis
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/dados')
def visualizar_dados():
    """Página de visualização detalhada dos dados anuais"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager
        
        # Pega informações do usuário logado
        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()
        
        if not user_data:
            flash("Erro ao carregar dados do usuário.", "danger")
            return redirect(url_for('index.login'))
        
        # Parâmetro de filtro (apenas ano)
        ano_selecionado = request.args.get('ano', type=int)
        
        data_results = None
        
        if ano_selecionado:
            # Busca dados específicos do ano
            company_manager = CompanyManager()
            data_results = company_manager.buscar_dados_empresa(
                user_data['empresa'],
                ano_selecionado
            )
            company_manager.close()
        
        return render_template(
            'user/dados.html',
            user=user_data,
            data_results=data_results,
            ano_selecionado=ano_selecionado
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/api/dados/<int:ano>')
def api_dados_ano(ano):
    """API para retornar dados de um ano específico organizados por grupo de viabilidade"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager
        from models.company_manager import CompanyManager
        import json
        
        user_manager = UserManager()
        user_data = user_manager.find_user_by_email(session.get('user_email'))
        user_manager.close()
        
        if not user_data:
            return json.dumps({"error": "Usuário não encontrado"}), 404
        
        company_manager = CompanyManager()
        data_results = company_manager.buscar_dados_empresa(
            user_data['empresa'],
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


@user_bp.route('/user/logout')
def logout():
    """Logout do usuário"""
    session.pop('user_email', None)
    session.pop('user_role', None)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for('index.login'))