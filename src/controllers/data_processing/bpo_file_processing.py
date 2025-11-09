"""
BPO Financial Data Processing Module
=====================================

Este módulo é responsável por processar arquivos Excel com dados de BPO Financeiro (mensal).
Diferente da viabilidade financeira (anual), os dados de BPO são processados mensalmente.

Autor: WaysSolutionHub
Data: 2025-10-31
"""

import openpyxl
from openpyxl import load_workbook


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def mapear_colunas(cabecalho_linha2, cabecalho_linha3):
    """
    Mapeia dinamicamente as colunas baseado no cabeçalho multi-nível.

    Args:
        cabecalho_linha2: Lista com valores da linha 2 (categorias principais)
        cabecalho_linha3: Lista com valores da linha 3 (sub-métricas)

    Returns:
        dict: Mapeamento de colunas
    """

    mapeamento = {
        'col_natureza': 0,  # Coluna 0 (índice) = Coluna A (Excel)
        'col_viab_perc': None,
        'col_viab_valor': None,
        'meses': [],
        'resultados': {}
    }

    # Processar cabeçalho
    mes_atual = None
    colunas_mes_atual = {}

    for idx, (cat_principal, sub_metrica) in enumerate(zip(cabecalho_linha2, cabecalho_linha3)):
        # Normalizar valores
        cat_str = str(cat_principal).strip().upper() if cat_principal else ""
        sub_str = str(sub_metrica).strip().upper() if sub_metrica else ""

        # Coluna NATUREZA ou NATUREZA DE LANÇAMENTO
        if "NATUREZA" in cat_str:
            mapeamento['col_natureza'] = idx
            continue

        # Coluna VIABILIDADE
        if "VIABILIDADE" in cat_str:
            if "%" in sub_str or "PERCENT" in sub_str:
                mapeamento['col_viab_perc'] = idx
            elif "VALOR" in sub_str:
                mapeamento['col_viab_valor'] = idx
            continue

        # Detectar meses
        meses_possiveis = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'MARCO', 'ABRIL', 'MAIO', 'JUNHO',
                          'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']

        # Verificar se é um mês
        eh_mes = False
        for mes_nome in meses_possiveis:
            if mes_nome in cat_str:
                eh_mes = True
                # Se mudou de mês, salvar o anterior
                if mes_atual and mes_atual != cat_str:
                    if colunas_mes_atual:
                        mapeamento['meses'].append({
                            'nome': mes_atual.title(),
                            **colunas_mes_atual
                        })
                        colunas_mes_atual = {}

                mes_atual = cat_str
                break

        if eh_mes:
            # Mapear sub-colunas do mês
            if "%" in sub_str and "ATINGIDO" not in sub_str and "DIFERENÇA" not in sub_str and "DIFERENCA" not in sub_str:
                # % simples = % Realizado
                colunas_mes_atual['col_perc'] = idx
            elif "VALOR" in sub_str and "REALIZADO" in sub_str:
                colunas_mes_atual['col_valor'] = idx
            elif "ATINGIDO" in sub_str:
                colunas_mes_atual['col_atingido'] = idx
            elif "DIFERENÇA" in sub_str or "DIFERENCA" in sub_str:
                colunas_mes_atual['col_diferenca'] = idx
            continue

        # Detectar colunas de resultados/totais
        if ("ORÇADO" in cat_str or "ORCADO" in cat_str or "PREVISÃO" in cat_str or "PREVISAO" in cat_str) and "TOTAL" in cat_str:
            mapeamento['resultados']['previsao_total'] = idx
        elif "REALIZADO" in cat_str and "TOTAL" in cat_str:
            mapeamento['resultados']['total_realizado'] = idx
        elif "DIFERENÇA" in cat_str or "DIFERENCA" in cat_str:
            if "TOTAL" in cat_str:
                mapeamento['resultados']['diferenca_total'] = idx
        elif "PENDENTE" in cat_str:
            mapeamento['resultados']['pendente_total'] = idx

    # Salvar último mês
    if mes_atual and colunas_mes_atual:
        mapeamento['meses'].append({
            'nome': mes_atual.title(),
            **colunas_mes_atual
        })

    return mapeamento


def extrair_codigo_e_nome(texto):
    """
    Extrai código hierárquico e nome de um texto como "1.01.06 - PMW RECEITA VENDA SERVIÇO"

    Returns:
        tuple: (codigo, nome, nivel_hierarquia)
        Exemplo: ("1.01.06", "PMW RECEITA VENDA SERVIÇO", 3)
    """
    texto = str(texto).strip()

    # Verificar se tem " - " separando código e nome
    if " - " in texto:
        partes = texto.split(" - ", 1)
        codigo = partes[0].strip()
        nome = partes[1].strip()
    else:
        # Se não tem separador, considera tudo como nome
        codigo = ""
        nome = texto

    # Calcular nível de hierarquia (contando pontos no código)
    nivel = codigo.count('.') + 1 if codigo else 0

    return codigo, nome, nivel


def processar_item_hierarquico(col_a, row_values, mapeamento, linha):
    """
    Processa um item hierárquico (linha normal da planilha) usando mapeamento dinâmico

    Args:
        col_a: Valor da coluna A (código e nome)
        row_values: Lista com todos os valores da linha
        mapeamento: Dicionário com mapeamento de colunas
        linha: Número da linha atual

    Returns:
        dict: Dados estruturados do item
    """
    # Extrair código e nome
    codigo, nome, nivel = extrair_codigo_e_nome(col_a)

    # Extrair viabilidade usando mapeamento
    perc_viabilidade = None
    valor_viabilidade = None

    if mapeamento['col_viab_perc'] is not None:
        perc_viabilidade = converter_valor(row_values[mapeamento['col_viab_perc']])

    if mapeamento['col_viab_valor'] is not None:
        valor_viabilidade = converter_valor(row_values[mapeamento['col_viab_valor']])

    # Processar dados mensais usando mapeamento
    dados_meses = []

    for i, mes_info in enumerate(mapeamento['meses']):
        mes_data = {
            'mes_numero': i + 1,
            'mes_nome': mes_info['nome'],
            'perc_realizado': converter_valor(row_values[mes_info.get('col_perc')]) if mes_info.get('col_perc') is not None else None,
            'valor_realizado': converter_valor(row_values[mes_info.get('col_valor')]) if mes_info.get('col_valor') is not None else None,
            'perc_atingido': converter_valor(row_values[mes_info.get('col_atingido')]) if mes_info.get('col_atingido') is not None else None,
            'valor_diferenca': converter_valor(row_values[mes_info.get('col_diferenca')]) if mes_info.get('col_diferenca') is not None else None,
        }
        dados_meses.append(mes_data)

    # Processar resultados totais usando mapeamento
    resultados = {
        'previsao_total': converter_valor(row_values[mapeamento['resultados'].get('previsao_total')]) if mapeamento['resultados'].get('previsao_total') is not None else None,
        'total_realizado': converter_valor(row_values[mapeamento['resultados'].get('total_realizado')]) if mapeamento['resultados'].get('total_realizado') is not None else None,
        'diferenca_total': converter_valor(row_values[mapeamento['resultados'].get('diferenca_total')]) if mapeamento['resultados'].get('diferenca_total') is not None else None,
        'media_perc_realizado': None,  # Não tem no cabeçalho descrito
        'media_valor_realizado': None,
        'media_perc_diferenca': None,
        'media_valor_diferenca': None,
    }

    return {
        'codigo': codigo,
        'nome': nome,
        'nivel_hierarquia': nivel,
        'linha': linha,
        'viabilidade': {
            'percentual': perc_viabilidade,
            'valor': valor_viabilidade
        },
        'dados_mensais': dados_meses,
        'resultados_totais': resultados
    }


def processar_linha_resultado(col_a, row_values, mapeamento, linha):
    """
    Processa uma linha da seção RESULTADO POR FLUXO DE CAIXA usando mapeamento dinâmico

    Similar a processar_item_hierarquico, mas sem hierarquia
    """
    nome = str(col_a).strip()

    # Extrair viabilidade usando mapeamento
    perc_viabilidade = None
    valor_viabilidade = None

    if mapeamento['col_viab_perc'] is not None:
        perc_viabilidade = converter_valor(row_values[mapeamento['col_viab_perc']])

    if mapeamento['col_viab_valor'] is not None:
        valor_viabilidade = converter_valor(row_values[mapeamento['col_viab_valor']])

    # Processar dados mensais usando mapeamento
    dados_meses = []

    for i, mes_info in enumerate(mapeamento['meses']):
        mes_data = {
            'mes_numero': i + 1,
            'mes_nome': mes_info['nome'],
            'perc_realizado': converter_valor(row_values[mes_info.get('col_perc')]) if mes_info.get('col_perc') is not None else None,
            'valor_realizado': converter_valor(row_values[mes_info.get('col_valor')]) if mes_info.get('col_valor') is not None else None,
            'perc_atingido': converter_valor(row_values[mes_info.get('col_atingido')]) if mes_info.get('col_atingido') is not None else None,
            'valor_diferenca': converter_valor(row_values[mes_info.get('col_diferenca')]) if mes_info.get('col_diferenca') is not None else None,
        }
        dados_meses.append(mes_data)

    # Processar resultados usando mapeamento
    resultados = {
        'previsao_total': converter_valor(row_values[mapeamento['resultados'].get('previsao_total')]) if mapeamento['resultados'].get('previsao_total') is not None else None,
        'total_realizado': converter_valor(row_values[mapeamento['resultados'].get('total_realizado')]) if mapeamento['resultados'].get('total_realizado') is not None else None,
        'diferenca_total': converter_valor(row_values[mapeamento['resultados'].get('diferenca_total')]) if mapeamento['resultados'].get('diferenca_total') is not None else None,
        'media_perc_realizado': None,
        'media_valor_realizado': None,
        'media_perc_diferenca': None,
        'media_valor_diferenca': None,
    }

    return {
        'tipo': 'dados',
        'nome': nome,
        'linha': linha,
        'viabilidade': {
            'percentual': perc_viabilidade,
            'valor': valor_viabilidade
        },
        'dados_mensais': dados_meses,
        'resultados_totais': resultados
    }


def converter_valor(valor):
    """Converte um valor de célula para float ou None"""
    if valor is None or valor == '':
        return None

    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def exibir_resumo_processamento(dados):
    """
    Exibe um resumo visual dos dados processados de forma bem legível
    """
    print("\n" + "="*100)
    print(" "*40 + "RESUMO DO PROCESSAMENTO")
    print("="*100)

    # Metadados
    meta = dados.get('metadados', {})
    print(f"\n📊 METADADOS:")
    print(f"   • Total de colunas na planilha: {meta.get('total_colunas')}")
    print(f"   • Número de meses detectados: {meta.get('num_meses')}")
    print(f"   • Meses processados: {', '.join(meta.get('meses', []))}")
    print(f"   • Total de itens hierárquicos: {meta.get('total_itens')}")
    print(f"   • Total de linhas de resultados: {meta.get('total_resultados')}")

    # ========================================================================
    # EXIBIR ITENS HIERÁRQUICOS (ESTILO TABELA)
    # ========================================================================
    itens = dados.get('itens_hierarquicos', [])

    print("\n" + "="*100)
    print("📋 ITENS HIERÁRQUICOS (Primeiras 10 linhas comparadas com Excel)")
    print("="*100)

    num_meses = meta.get('num_meses', 0)

    for i, item in enumerate(itens[:10]):
        linha_excel = item['linha']
        codigo = item['codigo']
        nome = item['nome']
        nivel = item['nivel_hierarquia']

        # Indentação visual conforme hierarquia
        indent = "  " * nivel

        print(f"\n{'─'*100}")
        print(f"LINHA {linha_excel} (Excel) | Nível {nivel} | Código: {codigo}")
        print(f"{'─'*100}")
        print(f"{indent}📌 NOME: {nome}")

        # Viabilidade
        viab = item['viabilidade']
        print(f"{indent}├─ VIABILIDADE:")
        print(f"{indent}│  • Percentual: {formatar_numero(viab['percentual'])}%")
        print(f"{indent}│  • Valor: R$ {formatar_numero(viab['valor'])}")

        # Dados mensais
        if num_meses > 0:
            print(f"{indent}├─ DADOS MENSAIS:")
            for mes_data in item['dados_mensais']:
                mes_nome = mes_data['mes_nome']
                print(f"{indent}│  └─ {mes_nome}:")
                print(f"{indent}│     • % Realizado: {formatar_numero(mes_data['perc_realizado'])}%")
                print(f"{indent}│     • Valor Realizado: R$ {formatar_numero(mes_data['valor_realizado'])}")
                print(f"{indent}│     • % Atingido: {formatar_numero(mes_data['perc_atingido'])}%")
                print(f"{indent}│     • Valor Diferença: R$ {formatar_numero(mes_data['valor_diferenca'])}")

        # Resultados totais
        res = item['resultados_totais']
        print(f"{indent}└─ RESULTADOS TOTAIS:")
        print(f"{indent}   • Previsão Total: R$ {formatar_numero(res['previsao_total'])}")
        print(f"{indent}   • Total Realizado: R$ {formatar_numero(res['total_realizado'])}")
        print(f"{indent}   • Diferença Total: R$ {formatar_numero(res['diferenca_total'])}")
        print(f"{indent}   • Média % Realizado: {formatar_numero(res['media_perc_realizado'])}%")
        print(f"{indent}   • Média Valor Realizado: R$ {formatar_numero(res['media_valor_realizado'])}")
        print(f"{indent}   • Média % Diferença: {formatar_numero(res['media_perc_diferenca'])}%")
        print(f"{indent}   • Média Valor Diferença: R$ {formatar_numero(res['media_valor_diferenca'])}")

    if len(itens) > 10:
        print(f"\n... (e mais {len(itens) - 10} itens não exibidos)")

    # ========================================================================
    # EXIBIR SEÇÃO RESULTADO POR FLUXO DE CAIXA
    # ========================================================================
    resultados = dados.get('resultados_fluxo', {}).get('secoes', [])
    if resultados:
        print("\n" + "="*100)
        print("📈 SEÇÃO: RESULTADO POR FLUXO DE CAIXA")
        print("="*100)

        for i, item in enumerate(resultados):
            linha_excel = item.get('linha', 'N/A')

            if item.get('tipo') == 'titulo':
                # É um título
                print(f"\n{'═'*100}")
                print(f"LINHA {linha_excel} (Excel) | TÍTULO")
                print(f"{'═'*100}")
                print(f"📌 {item['texto']}")
            else:
                # É uma linha com dados
                nome = item.get('nome', 'N/A')

                print(f"\n{'─'*100}")
                print(f"LINHA {linha_excel} (Excel) | {nome}")
                print(f"{'─'*100}")

                # Viabilidade
                viab = item['viabilidade']
                print(f"├─ VIABILIDADE:")
                print(f"│  • Percentual: {formatar_numero(viab['percentual'])}%")
                print(f"│  • Valor: R$ {formatar_numero(viab['valor'])}")

                # Dados mensais
                if num_meses > 0 and item.get('dados_mensais'):
                    print(f"├─ DADOS MENSAIS:")
                    for mes_data in item['dados_mensais']:
                        mes_nome = mes_data['mes_nome']
                        print(f"│  └─ {mes_nome}:")
                        print(f"│     • % Realizado: {formatar_numero(mes_data['perc_realizado'])}%")
                        print(f"│     • Valor Realizado: R$ {formatar_numero(mes_data['valor_realizado'])}")
                        print(f"│     • % Atingido: {formatar_numero(mes_data['perc_atingido'])}%")
                        print(f"│     • Valor Diferença: R$ {formatar_numero(mes_data['valor_diferenca'])}")

                # Resultados totais
                res = item['resultados_totais']
                print(f"└─ RESULTADOS TOTAIS:")
                print(f"   • Previsão Total: R$ {formatar_numero(res['previsao_total'])}")
                print(f"   • Total Realizado: R$ {formatar_numero(res['total_realizado'])}")
                print(f"   • Diferença Total: R$ {formatar_numero(res['diferenca_total'])}")
                print(f"   • Média % Realizado: {formatar_numero(res['media_perc_realizado'])}%")
                print(f"   • Média Valor Realizado: R$ {formatar_numero(res['media_valor_realizado'])}")
                print(f"   • Média % Diferença: {formatar_numero(res['media_perc_diferenca'])}%")
                print(f"   • Média Valor Diferença: R$ {formatar_numero(res['media_valor_diferenca'])}")

    print("\n" + "="*100)


def formatar_numero(valor):
    """
    Formata um número para exibição legível (ou 'N/A' se None)
    """
    if valor is None:
        return "N/A"

    # Se for um número muito pequeno (perto de zero), exibir como 0.00
    if isinstance(valor, (int, float)) and abs(valor) < 0.01:
        return "0.00"

    # Formatar com 2 casas decimais e separador de milhares
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(valor)


# ============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ============================================================================

def process_bpo_file(file):
    """
    Processa arquivo Excel de BPO Financeiro e retorna dados estruturados.

    Estrutura da planilha:
    - Linha 4+: Dados começam
    - Coluna A: Código hierárquico e nome (ex: "1.01 - RECEITA VENDA SERVIÇO")
    - Coluna B: % Viabilidade
    - Coluna C: Valor Viabilidade (R$)
    - Colunas D+: Dados mensais (4 colunas por mês) + 7 colunas de resultados

    Args:
        file: Arquivo Excel (.xlsx ou .xls)

    Returns:
        dict: {
            'itens_hierarquicos': [...],  # Itens com hierarquia
            'resultados_fluxo': {...},     # Seção RESULTADO POR FLUXO DE CAIXA
            'metadados': {...}             # Info sobre meses, totais, etc
        }
    """

    try:
        print("\n" + "="*80)
        print("INICIANDO PROCESSAMENTO DA PLANILHA BPO FINANCEIRO")
        print("="*80)

        # Carregar workbook
        wb = load_workbook(file)
        sheet = wb.active

        # ====================================================================
        # PASSO 1: LER CABEÇALHO MULTI-NÍVEL (LINHAS 2 e 3)
        # ====================================================================
        print(f"\n🔍 Lendo cabeçalho da planilha...")

        # Linha 2: Categorias principais (NATUREZA, VIABILIDADE, JANEIRO, FEVEREIRO, etc.)
        # Linha 3: Sub-métricas (%, VALOR, %, VALOR REALIZADO, % ATINGIDO, VALOR DIFERENÇA)

        cabecalho_linha2 = []
        cabecalho_linha3 = []

        total_colunas = sheet.max_column

        for col in range(1, total_colunas + 1):
            val2 = sheet.cell(row=2, column=col).value
            val3 = sheet.cell(row=3, column=col).value
            cabecalho_linha2.append(val2)
            cabecalho_linha3.append(val3)

        print(f"📊 Total de colunas: {total_colunas}")

        # ====================================================================
        # PASSO 2: MAPEAR COLUNAS DINAMICAMENTE
        # ====================================================================
        print(f"\n🗺️  Mapeando estrutura das colunas...")

        mapeamento = mapear_colunas(cabecalho_linha2, cabecalho_linha3)

        print(f"   • Coluna Natureza: {mapeamento['col_natureza']}")
        print(f"   • Colunas Viabilidade: {mapeamento['col_viab_perc']}, {mapeamento['col_viab_valor']}")
        print(f"   • Número de meses: {len(mapeamento['meses'])}")

        for mes_info in mapeamento['meses']:
            print(f"      - {mes_info['nome']}: Colunas {mes_info['col_perc']}, {mes_info['col_valor']}, {mes_info['col_atingido']}, {mes_info['col_diferenca']}")

        print(f"   • Colunas Resultados: {mapeamento['resultados']}")

        num_meses = len(mapeamento['meses'])
        meses_nomes = [m['nome'] for m in mapeamento['meses']]

        # ====================================================================
        # PASSO 3: PROCESSAR ITENS HIERÁRQUICOS (LINHA 4 ATÉ "RESULTADO...")
        # ====================================================================
        itens_hierarquicos = []
        linha_atual = 4  # Começa na linha 4 (dados começam após cabeçalho)

        print(f"\n🔍 Processando itens hierárquicos...")

        while True:
            row_values = []
            for col in range(1, total_colunas + 1):
                cell_value = sheet.cell(row=linha_atual, column=col).value
                row_values.append(cell_value)

            # Verifica se chegou na seção de resultados
            if row_values[0] and "RESULTADO POR FLUXO DE CAIXA" in str(row_values[0]):
                print(f"\n✅ Encontrado 'RESULTADO POR FLUXO DE CAIXA' na linha {linha_atual}")
                break

            # Verifica se linha está completamente vazia (fim da planilha)
            if all(v is None or str(v).strip() == '' for v in row_values):
                print(f"\n⚠️  Linha vazia encontrada na linha {linha_atual} - parando processamento")
                break

            # Processar item se coluna A tem conteúdo
            col_a = row_values[0]
            if col_a and str(col_a).strip():
                item = processar_item_hierarquico(
                    col_a,
                    row_values,
                    mapeamento,
                    linha_atual
                )
                itens_hierarquicos.append(item)

            linha_atual += 1

        print(f"✅ Total de itens hierárquicos processados: {len(itens_hierarquicos)}")

        # ====================================================================
        # PASSO 3: PROCESSAR SEÇÃO "RESULTADO POR FLUXO DE CAIXA"
        # ====================================================================
        resultados_fluxo = {}

        if row_values[0] and "RESULTADO POR FLUXO DE CAIXA" in str(row_values[0]):
            print(f"\n🔍 Processando seção RESULTADO POR FLUXO DE CAIXA...")

            # Pular linha do título
            linha_atual += 1

            # Processar as 12 linhas especiais
            secoes_resultado = []

            while True:
                row_values = []
                for col in range(1, total_colunas + 1):
                    cell_value = sheet.cell(row=linha_atual, column=col).value
                    row_values.append(cell_value)

                # Se linha vazia, acabou
                if all(v is None or str(v).strip() == '' for v in row_values):
                    print(f"✅ Fim da seção de resultados na linha {linha_atual}")
                    break

                col_a = row_values[0]
                if col_a and str(col_a).strip():
                    # Verificar se é título (sem dados à direita) ou linha com dados
                    tem_dados = any(row_values[i] is not None and row_values[i] != ''
                                   for i in range(1, len(row_values)))

                    if tem_dados:
                        # Linha com dados
                        item_resultado = processar_linha_resultado(
                            col_a,
                            row_values,
                            mapeamento,
                            linha_atual
                        )
                        secoes_resultado.append(item_resultado)
                    else:
                        # Linha de título
                        print(f"  📌 Título encontrado: {col_a}")
                        secoes_resultado.append({
                            'tipo': 'titulo',
                            'texto': str(col_a).strip(),
                            'linha': linha_atual
                        })

                linha_atual += 1

            resultados_fluxo = {
                'secoes': secoes_resultado,
                'total_linhas': len(secoes_resultado)
            }

            print(f"✅ Total de linhas na seção de resultados: {len(secoes_resultado)}")

        # ====================================================================
        # PASSO 4: MONTAR ESTRUTURA FINAL
        # ====================================================================
        dados_processados = {
            'itens_hierarquicos': itens_hierarquicos,
            'resultados_fluxo': resultados_fluxo,
            'metadados': {
                'total_colunas': total_colunas,
                'num_meses': num_meses,
                'meses': meses_nomes[:num_meses],
                'total_itens': len(itens_hierarquicos),
                'total_resultados': len(resultados_fluxo.get('secoes', []))
            }
        }

        # ====================================================================
        # PASSO 5: EXIBIR RESUMO
        # ====================================================================
        exibir_resumo_processamento(dados_processados)

        print("\n" + "="*80)
        print("PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print("="*80 + "\n")

        return dados_processados

    except Exception as e:
        print(f"\n❌ ERRO ao processar arquivo BPO: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erro no processamento do BPO: {str(e)}")


def validate_bpo_data(dados):
    """
    Valida os dados de BPO processados antes de salvar no banco.

    Args:
        dados (dict): Dados processados pela função process_bpo_file()

    Returns:
        tuple: (bool, str) - (True/False, mensagem de erro/sucesso)

    TODO: IMPLEMENTAR VALIDAÇÕES NECESSÁRIAS
    =========================================
    Exemplos de validações:
    - Verificar se há dados mensais
    - Validar se os meses estão no range correto (1-12)
    - Verificar se valores são numéricos
    - Validar campos obrigatórios
    - Verificar consistência dos dados
    """

    # Validação básica temporária
    if not dados:
        return False, "Dados vazios ou inválidos"

    if 'dados_mensais' not in dados:
        return False, "Estrutura de dados inválida: falta campo 'dados_mensais'"

    # TODO: Adicionar validações específicas aqui

    return True, "Validação OK (temporária)"


def get_bpo_summary(dados):
    """
    Gera um resumo dos dados de BPO para exibição rápida.

    Args:
        dados (dict): Dados processados do BPO

    Returns:
        dict: Resumo com informações agregadas

    TODO: IMPLEMENTAR LÓGICA DE SUMARIZAÇÃO
    ========================================
    Exemplos de dados do resumo:
    - Total por mês
    - Total por categoria
    - Média mensal
    - Meses com dados
    - etc.
    """

    return {
        'total_registros': len(dados.get('dados_mensais', [])),
        'status': 'Em desenvolvimento'
    }
