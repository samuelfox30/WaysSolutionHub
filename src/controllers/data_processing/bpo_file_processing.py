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


def processar_item_hierarquico(col_a, row_values, num_meses, meses_nomes, linha):
    """
    Processa um item hierárquico (linha normal da planilha)

    Args:
        col_a: Valor da coluna A (código e nome)
        row_values: Lista com todos os valores da linha
        num_meses: Número de meses detectados
        meses_nomes: Lista com nomes dos meses
        linha: Número da linha atual

    Returns:
        dict: Dados estruturados do item
    """
    # Extrair código e nome
    codigo, nome, nivel = extrair_codigo_e_nome(col_a)

    # Extrair viabilidade (colunas B e C, índices 1 e 2)
    perc_viabilidade = row_values[1] if len(row_values) > 1 else None
    valor_viabilidade = row_values[2] if len(row_values) > 2 else None

    # Converter valores de viabilidade
    if perc_viabilidade is not None:
        try:
            perc_viabilidade = float(perc_viabilidade)
        except (ValueError, TypeError):
            perc_viabilidade = None

    if valor_viabilidade is not None:
        try:
            valor_viabilidade = float(valor_viabilidade)
        except (ValueError, TypeError):
            valor_viabilidade = None

    # Processar dados mensais
    dados_meses = []
    col_inicio_mes = 3  # Coluna D (índice 3)

    for i in range(num_meses):
        idx_base = col_inicio_mes + (i * 4)

        # Cada mês tem 4 colunas: % realizado, valor realizado, % atingido, valor diferença
        mes_data = {
            'mes_numero': i + 1,
            'mes_nome': meses_nomes[i] if i < len(meses_nomes) else f'Mês {i+1}',
            'perc_realizado': converter_valor(row_values[idx_base]) if idx_base < len(row_values) else None,
            'valor_realizado': converter_valor(row_values[idx_base + 1]) if idx_base + 1 < len(row_values) else None,
            'perc_atingido': converter_valor(row_values[idx_base + 2]) if idx_base + 2 < len(row_values) else None,
            'valor_diferenca': converter_valor(row_values[idx_base + 3]) if idx_base + 3 < len(row_values) else None,
        }
        dados_meses.append(mes_data)

    # Processar resultados totais (últimas 7 colunas)
    idx_resultados_inicio = col_inicio_mes + (num_meses * 4)

    resultados = {
        'previsao_total': converter_valor(row_values[idx_resultados_inicio]) if idx_resultados_inicio < len(row_values) else None,
        'total_realizado': converter_valor(row_values[idx_resultados_inicio + 1]) if idx_resultados_inicio + 1 < len(row_values) else None,
        'diferenca_total': converter_valor(row_values[idx_resultados_inicio + 2]) if idx_resultados_inicio + 2 < len(row_values) else None,
        'media_perc_realizado': converter_valor(row_values[idx_resultados_inicio + 3]) if idx_resultados_inicio + 3 < len(row_values) else None,
        'media_valor_realizado': converter_valor(row_values[idx_resultados_inicio + 4]) if idx_resultados_inicio + 4 < len(row_values) else None,
        'media_perc_diferenca': converter_valor(row_values[idx_resultados_inicio + 5]) if idx_resultados_inicio + 5 < len(row_values) else None,
        'media_valor_diferenca': converter_valor(row_values[idx_resultados_inicio + 6]) if idx_resultados_inicio + 6 < len(row_values) else None,
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


def processar_linha_resultado(col_a, row_values, num_meses, meses_nomes, linha):
    """
    Processa uma linha da seção RESULTADO POR FLUXO DE CAIXA

    Similar a processar_item_hierarquico, mas sem hierarquia
    """
    nome = str(col_a).strip()

    # Extrair viabilidade
    perc_viabilidade = converter_valor(row_values[1]) if len(row_values) > 1 else None
    valor_viabilidade = converter_valor(row_values[2]) if len(row_values) > 2 else None

    # Processar dados mensais
    dados_meses = []
    col_inicio_mes = 3

    for i in range(num_meses):
        idx_base = col_inicio_mes + (i * 4)

        mes_data = {
            'mes_numero': i + 1,
            'mes_nome': meses_nomes[i] if i < len(meses_nomes) else f'Mês {i+1}',
            'perc_realizado': converter_valor(row_values[idx_base]) if idx_base < len(row_values) else None,
            'valor_realizado': converter_valor(row_values[idx_base + 1]) if idx_base + 1 < len(row_values) else None,
            'perc_atingido': converter_valor(row_values[idx_base + 2]) if idx_base + 2 < len(row_values) else None,
            'valor_diferenca': converter_valor(row_values[idx_base + 3]) if idx_base + 3 < len(row_values) else None,
        }
        dados_meses.append(mes_data)

    # Processar resultados
    idx_resultados_inicio = col_inicio_mes + (num_meses * 4)

    resultados = {
        'previsao_total': converter_valor(row_values[idx_resultados_inicio]) if idx_resultados_inicio < len(row_values) else None,
        'total_realizado': converter_valor(row_values[idx_resultados_inicio + 1]) if idx_resultados_inicio + 1 < len(row_values) else None,
        'diferenca_total': converter_valor(row_values[idx_resultados_inicio + 2]) if idx_resultados_inicio + 2 < len(row_values) else None,
        'media_perc_realizado': converter_valor(row_values[idx_resultados_inicio + 3]) if idx_resultados_inicio + 3 < len(row_values) else None,
        'media_valor_realizado': converter_valor(row_values[idx_resultados_inicio + 4]) if idx_resultados_inicio + 4 < len(row_values) else None,
        'media_perc_diferenca': converter_valor(row_values[idx_resultados_inicio + 5]) if idx_resultados_inicio + 5 < len(row_values) else None,
        'media_valor_diferenca': converter_valor(row_values[idx_resultados_inicio + 6]) if idx_resultados_inicio + 6 < len(row_values) else None,
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
    Exibe um resumo visual dos dados processados
    """
    print("\n" + "="*80)
    print("RESUMO DO PROCESSAMENTO")
    print("="*80)

    # Metadados
    meta = dados.get('metadados', {})
    print(f"\n📊 METADADOS:")
    print(f"   • Total de colunas: {meta.get('total_colunas')}")
    print(f"   • Número de meses: {meta.get('num_meses')}")
    print(f"   • Meses: {', '.join(meta.get('meses', []))}")
    print(f"   • Total de itens hierárquicos: {meta.get('total_itens')}")
    print(f"   • Total de linhas de resultados: {meta.get('total_resultados')}")

    # Primeiros 5 itens hierárquicos
    itens = dados.get('itens_hierarquicos', [])
    print(f"\n📋 PRIMEIROS 5 ITENS HIERÁRQUICOS:")
    for i, item in enumerate(itens[:5]):
        indent = "  " * item['nivel_hierarquia']
        print(f"   {i+1}. {indent}[{item['codigo']}] {item['nome']}")
        print(f"      {indent}└─ Viabilidade: {item['viabilidade']['percentual']}% | R$ {item['viabilidade']['valor']}")

    # Resumo da seção de resultados
    resultados = dados.get('resultados_fluxo', {}).get('secoes', [])
    if resultados:
        print(f"\n📈 SEÇÃO RESULTADO POR FLUXO DE CAIXA ({len(resultados)} linhas):")
        for i, item in enumerate(resultados[:10]):  # Mostrar primeiras 10
            if item.get('tipo') == 'titulo':
                print(f"   {i+1}. 📌 TÍTULO: {item['texto']}")
            else:
                nome = item.get('nome', 'N/A')
                previsao = item.get('resultados_totais', {}).get('previsao_total')
                realizado = item.get('resultados_totais', {}).get('total_realizado')
                print(f"   {i+1}. {nome}")
                print(f"      └─ Previsão: R$ {previsao} | Realizado: R$ {realizado}")

    print("\n" + "="*80)


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
        # PASSO 1: IDENTIFICAR ESTRUTURA DA PLANILHA
        # ====================================================================
        total_colunas = sheet.max_column
        print(f"\n📊 Total de colunas encontradas: {total_colunas}")

        # Calcular número de meses
        # Total - 3 (nome + 2 viabilidade) - 7 (resultados) = colunas mensais
        colunas_mensais = total_colunas - 3 - 7
        num_meses = colunas_mensais // 4

        print(f"📅 Número de meses detectados: {num_meses}")
        print(f"📈 Estrutura: 3 fixas + {colunas_mensais} mensais ({num_meses} meses) + 7 resultados")

        # Nomes dos meses
        meses_nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

        # ====================================================================
        # PASSO 2: PROCESSAR ITENS HIERÁRQUICOS (LINHA 4 ATÉ "RESULTADO...")
        # ====================================================================
        itens_hierarquicos = []
        linha_atual = 4  # Começa na linha 4

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
                    num_meses,
                    meses_nomes,
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
                            num_meses,
                            meses_nomes,
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
