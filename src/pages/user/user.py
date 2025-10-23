from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/dashboard')
def user_dashboard():
    """Dashboard principal do usuário"""
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
        
        # Pega o ano atual ou o ano filtrado
        ano_atual = request.args.get('ano', datetime.now().year, type=int)
        
        # Busca meses com dados disponíveis
        company_manager = CompanyManager()
        meses_disponiveis = company_manager.get_meses_com_dados(user_data['id'], ano_atual)
        company_manager.close()
        
        return render_template(
            'user/dashboard.html',
            user=user_data,
            ano_atual=ano_atual,
            meses_disponiveis=meses_disponiveis
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/dados')
def visualizar_dados():
    """Página de visualização detalhada dos dados"""
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
        
        # Parâmetros de filtro
        mes_selecionado = request.args.get('mes', type=int)
        ano_selecionado = request.args.get('ano', datetime.now().year, type=int)
        
        data_results = None
        
        if mes_selecionado:
            # Busca dados específicos
            company_manager = CompanyManager()
            data_results = company_manager.buscar_dados_empresa(
                user_data['empresa'],
                mes_selecionado,
                ano_selecionado
            )
            company_manager.close()
        
        return render_template(
            'user/dados.html',
            user=user_data,
            data_results=data_results,
            mes_selecionado=mes_selecionado,
            ano_selecionado=ano_selecionado
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/api/dados/<int:mes>/<int:ano>')
def api_dados_mes(mes, ano):
    """API para retornar dados de um mês específico (para gráficos)"""
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
            mes,
            ano
        )
        company_manager.close()
        
        # Processa dados para formato JSON amigável
        dados_processados = {
            "mes": mes,
            "ano": ano,
            "itens": [],
            "totais": {}
        }
        
        # Processa itens normais e calcula totais por grupo
        if data_results and data_results.get('TbItens'):
            totais_grupos = {}
            for item in data_results['TbItens']:
                grupo = item[0]
                valor = float(item[4]) if item[4] else 0
                
                if grupo not in totais_grupos:
                    totais_grupos[grupo] = 0
                totais_grupos[grupo] += valor
                
            dados_processados["totais"] = totais_grupos
        
        return json.dumps(dados_processados), 200, {'Content-Type': 'application/json'}
    
    return json.dumps({"error": "Não autorizado"}), 403


@user_bp.route('/user/logout')
def logout():
    """Logout do usuário"""
    session.pop('user_email', None)
    session.pop('user_role', None)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for('index.login'))