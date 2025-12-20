from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from datetime import datetime
from utils.logger import get_logger

# Inicializar logger
logger = get_logger('user_pages')

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

        # Renderizar dashboard de viabilidade do usuário
        return render_template(
            'user/dashboard_empresa.html',
            user=user_data,
            empresa_nome=empresa_nome,
            empresa_id=empresa_id,
            anos_disponiveis=anos_disponiveis,
            is_user_view=True  # Flag para o template saber que é visualização de usuário
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


@user_bp.route('/user/api/dados-bpo-tabela/<int:empresa_id>')
def api_dados_bpo_tabela(empresa_id):
    """
    API para retornar dados BPO em formato tabular (tipo planilha)
    Filtra por período e retorna itens hierárquicos com dados mensais
    """
    if 'user_email' not in session or session.get('user_role') != 'user':
        return jsonify({'error': 'Não autorizado'}), 403

    # Verificar se usuário tem acesso a esta empresa
    empresa_id_session = session.get('empresa_id')
    if empresa_id != empresa_id_session:
        return jsonify({'error': 'Acesso negado a esta empresa'}), 403

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


@user_bp.route('/user/relatorio-pdf/<int:empresa_id>/<int:ano>/<grupo_viabilidade>')
def gerar_relatorio_pdf(empresa_id, ano, grupo_viabilidade):
    """Gera PDF do relatório de viabilidade (rota para usuários)"""
    if 'user_email' not in session or session.get('user_role') != 'user':
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))

    # Verificar se usuário tem acesso a esta empresa
    empresa_id_session = session.get('empresa_id')
    if empresa_id != empresa_id_session:
        flash("Acesso negado a esta empresa.", "danger")
        return redirect(url_for('user.user_dashboard'))

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
            return redirect(url_for('user.user_dashboard'))

        # Buscar template do relatório
        template_data = company_manager.buscar_template_relatorio(empresa_id, ano)
        company_manager.close()

        if not template_data:
            flash(f"Template de relatório não encontrado para o ano {ano}.", "warning")
            return redirect(url_for('user.user_dashboard'))

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
        return redirect(url_for('user.user_dashboard'))


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


@user_bp.route('/user/api/dados-empresa/<int:empresa_id>/<int:ano>')
def api_dados_empresa_user(empresa_id, ano):
    """API compatível com template do admin - retorna dados organizados por subgrupo"""
    if not ('user_email' in session and session.get('user_role') == 'user'):
        return jsonify({"error": "Não autorizado"}), 403

    from models.user_manager import UserManager
    from models.company_manager import CompanyManager

    # SEGURANÇA: Verificar se o usuário tem acesso a esta empresa
    empresa_id_session = session.get('empresa_id')
    if empresa_id != empresa_id_session:
        return jsonify({"error": "Acesso negado a esta empresa"}), 403

    user_manager = UserManager()
    user_data = user_manager.find_user_by_email(session.get('user_email'))
    user_manager.close()

    if not user_data:
        return jsonify({"error": "Usuário não encontrado"}), 404

    company_manager = CompanyManager()
    data_results = company_manager.buscar_dados_empresa(empresa_id, ano)
    company_manager.close()

    # ====== LOGS DETALHADOS DO BANCO DE DADOS ======
    logger.info("="*80)
    logger.info(f"📊 DADOS RECUPERADOS DO BANCO - Empresa ID: {empresa_id}, Ano: {ano}")
    logger.info("="*80)

    if data_results:
        logger.info(f"✓ TbItens: {len(data_results.get('TbItens', [])) if data_results.get('TbItens') else 0} registros")
        logger.info(f"✓ TbItensGastosOperacionais: {len(data_results.get('TbItensGastosOperacionais', [])) if data_results.get('TbItensGastosOperacionais') else 0} registros")
        logger.info(f"✓ TbItensInvestimentos: {len(data_results.get('TbItensInvestimentos', [])) if data_results.get('TbItensInvestimentos') else 0} registros")
        logger.info(f"✓ TbItensDividas: {len(data_results.get('TbItensDividas', [])) if data_results.get('TbItensDividas') else 0} registros")
        logger.info(f"✓ TbItensInvestimentoGeral: {len(data_results.get('TbItensInvestimentoGeral', [])) if data_results.get('TbItensInvestimentoGeral') else 0} registros")
    else:
        logger.warning("⚠️ data_results está vazio ou None!")

    logger.info("="*80)

    # Organizar dados por SUBGRUPO dentro de cada grupo de viabilidade (MESMA LÓGICA DO ADMIN)
    dados_organizados = {}

    # Processar TbItens
    if data_results and data_results.get('TbItens'):
        logger.info("\n🔍 PROCESSANDO TbItens (dados normais - percentual + valor):")

        # Contar por grupo e subgrupo
        contagem_por_grupo = {}
        gastos_op_encontrados = []

        for item in data_results['TbItens']:
            grupo = item[0]
            subgrupo = item[1]

            if grupo not in contagem_por_grupo:
                contagem_por_grupo[grupo] = {}
            if subgrupo not in contagem_por_grupo[grupo]:
                contagem_por_grupo[grupo][subgrupo] = 0
            contagem_por_grupo[grupo][subgrupo] += 1

            # Detectar GastosOperacionais especificamente
            if subgrupo == 'GastosOperacionais':
                gastos_op_encontrados.append({
                    'grupo': grupo,
                    'descricao': item[2],
                    'percentual': item[3],
                    'valor': item[4]
                })

        # Log da contagem
        for grupo, subgrupos in contagem_por_grupo.items():
            logger.info(f"  Grupo: {grupo}")
            for subgrupo, count in subgrupos.items():
                logger.info(f"    └─ {subgrupo}: {count} itens")

        # Log específico de GastosOperacionais
        logger.info(f"\n🎯 GastosOperacionais (NORMAL) encontrados no banco: {len(gastos_op_encontrados)} registros")
        if gastos_op_encontrados:
            for item in gastos_op_encontrados:
                logger.info(f"  ✓ Grupo: {item['grupo']} | Desc: {item['descricao'][:30]} | Perc: {item['percentual']} | Valor: {item['valor']}")
        else:
            logger.warning("  ⚠️ NENHUM GastosOperacionais (normal) encontrado em TbItens!")

        logger.info("")

        # Processar normalmente
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
        logger.info("🔍 PROCESSANDO TbItensGastosOperacionais (dados especiais - veículos):")

        # Contar por grupo
        contagem_veiculos = {}
        veiculos_detalhes = []

        for item in data_results['TbItensGastosOperacionais']:
            grupo = item[0]
            descricao = item[2]
            custo_km = item[3] if len(item) > 3 else None
            custo_mensal = item[4] if len(item) > 4 else None

            if grupo not in contagem_veiculos:
                contagem_veiculos[grupo] = 0
            contagem_veiculos[grupo] += 1

            veiculos_detalhes.append({
                'grupo': grupo,
                'descricao': descricao,
                'custo_km': custo_km,
                'custo_mensal': custo_mensal
            })

        # Log da contagem por grupo
        for grupo, count in contagem_veiculos.items():
            logger.info(f"  Grupo: {grupo} → {count} veículos")

        # Log detalhado
        logger.info(f"\n🚗 Gastos Operacionais Veículos (ESPECIAL) no banco: {len(veiculos_detalhes)} registros")
        for item in veiculos_detalhes:
            logger.info(f"  ✓ Grupo: {item['grupo']} | Desc: {item['descricao'][:30]} | Custo KM: {item['custo_km']} | Custo Mensal: {item['custo_mensal']}")

        logger.info("")

        # Processar normalmente
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

    return jsonify({
        "ano": ano,
        "dados": dados_organizados
    })


@user_bp.route('/user/api/dados/<int:ano>')
def api_dados_ano(ano):
    """API para retornar dados de um ano específico organizados por grupo de viabilidade"""
    if not ('user_email' in session and session.get('user_role') == 'user'):
        return jsonify({"error": "Não autorizado"}), 403

    from models.user_manager import UserManager
    from models.company_manager import CompanyManager

    # Verifica se tem empresa selecionada
    if 'empresa_id' not in session:
        return jsonify({"error": "Empresa não selecionada"}), 400

    user_manager = UserManager()
    user_data = user_manager.find_user_by_email(session.get('user_email'))
    user_manager.close()

    if not user_data:
        return jsonify({"error": "Usuário não encontrado"}), 404

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

    return jsonify({
        "ano": ano,
        "grupos": dados_por_grupo
    })


@user_bp.route('/user/bpo')
def visualizar_bpo():
    """Página de visualização do BPO da empresa selecionada"""
    if 'user_email' in session and session.get('user_role') == 'user':
        from models.user_manager import UserManager

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

        # Criar objeto empresa compatível com o template do admin
        empresa = {'nome': empresa_nome}

        # Renderizar dashboard BPO do usuário
        return render_template(
            'user/dashboard_bpo.html',
            user=user_data,
            empresa=empresa,
            empresa_nome=empresa_nome,
            empresa_id=empresa_id,
            is_user_view=True  # Flag para o template saber que é visualização de usuário
        )
    else:
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))


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


@user_bp.route('/user/api/dados-bpo/<int:empresa_id>')
def api_dados_bpo_user(empresa_id):
    """API compatível com template do admin - retorna dados BPO processados"""
    if not ('user_email' in session and session.get('user_role') == 'user'):
        return jsonify({"error": "Não autorizado"}), 403

    # SEGURANÇA: Verificar se o usuário tem acesso a esta empresa
    empresa_id_session = session.get('empresa_id')
    if empresa_id != empresa_id_session:
        return jsonify({"error": "Acesso negado a esta empresa"}), 403

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
        ano_curto = str(ano)[-2:]
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

            mes_dados = cenario_data.get(mes_num, cenario_data.get(str(mes_num), {}))

            if mes_dados and isinstance(mes_dados, dict):
                # Extrair valores realizados
                realizado = mes_dados.get('realizado', {})
                if isinstance(realizado, dict):
                    receita = realizado.get('receita', 0) or 0
                    despesa = realizado.get('despesa', 0) or 0
                    geral = realizado.get('geral', 0) or 0

                    totais[cenario_key]['receita'] += receita
                    totais[cenario_key]['despesa'] += despesa
                    totais[cenario_key]['geral'] += geral

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

                    totais_orcamento[cenario_key]['receita'] += receita_orc
                    totais_orcamento[cenario_key]['despesa'] += despesa_orc
                    totais_orcamento[cenario_key]['geral'] += geral_orc

        # Adicionar aos arrays do gráfico
        receitas_mensais.append(receita_grafico)
        despesas_mensais.append(despesa_grafico)
        gerais_mensais.append(geral_grafico)

    # Processar categorias de despesa (itens 2.0X)
    categorias_despesa = {}
    total_receita_orcado = 0

    try:
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

            # Pegar total receita orçado
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
                    except (IndexError, KeyError, TypeError):
                        pass

        # Calcular médias e diferenças
        num_meses = len(meses_data)
        for codigo in categorias_despesa:
            cat = categorias_despesa[codigo]
            cat['realizado'] = cat['realizado'] / num_meses if num_meses > 0 else 0
            cat['diferenca'] = cat['orcado'] - cat['realizado']

    except Exception:
        categorias_despesa = {}
        total_receita_orcado = 0

    # Processar categorias de receita (itens 1.0X)
    categorias_receita = {}

    try:
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

        # Calcular médias e diferenças
        num_meses = len(meses_data)
        for codigo in categorias_receita:
            cat = categorias_receita[codigo]
            cat['realizado'] = cat['realizado'] / num_meses if num_meses > 0 else 0
            cat['diferenca'] = cat['orcado'] - cat['realizado']

    except Exception:
        categorias_receita = {}

    return jsonify({
        'totais_acumulados': totais,
        'totais_orcamento': totais_orcamento,
        'num_meses': len(meses_data),
        'meses': labels_meses,
        'receitas': receitas_mensais,
        'despesas': despesas_mensais,
        'gerais': gerais_mensais,
        'categorias_despesa': categorias_despesa,
        'categorias_receita': categorias_receita,
        'total_receita_orcado': total_receita_orcado
    })


@user_bp.route('/user/consultar-bpo', methods=['GET', 'POST'])
def consultar_dados_bpo():
    """Consulta dados de BPO em formato de tabela para a empresa do usuário"""
    if not ('user_email' in session and session.get('user_role') == 'user'):
        flash("Acesso negado. Faça login como usuário.", "danger")
        return redirect(url_for('index.login'))

    # Verifica se tem empresa selecionada
    if 'empresa_id' not in session:
        return redirect(url_for('user.selecionar_empresa'))

    from models.user_manager import UserManager
    from models.company_manager import CompanyManager

    # Pega informações do usuário logado
    user_manager = UserManager()
    user_data = user_manager.find_user_by_email(session.get('user_email'))
    user_manager.close()

    if not user_data:
        flash("Erro ao carregar dados do usuário.", "danger")
        return redirect(url_for('index.login'))

    empresa_id = session.get('empresa_id')
    empresa_nome = session.get('empresa_nome')

    data_results = None
    ano_selecionado = None
    mes_selecionado = None

    if request.method == 'POST':
        ano_selecionado = request.form.get('ano')
        mes_selecionado = request.form.get('mes')

        if ano_selecionado and mes_selecionado:
            company_manager = CompanyManager()
            data_results = company_manager.buscar_dados_bpo_empresa(
                empresa_id,
                int(ano_selecionado),
                int(mes_selecionado)
            )
            company_manager.close()

    return render_template(
        'user/consultar_bpo.html',
        user=user_data,
        empresa_id=empresa_id,
        empresa_nome=empresa_nome,
        data_results=data_results,
        ano_selecionado=ano_selecionado,
        mes_selecionado=mes_selecionado
    )


@user_bp.route('/user/logout')
def logout():
    """Logout do usuário"""
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.pop('empresa_id', None)
    session.pop('empresa_nome', None)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for('index.login'))
