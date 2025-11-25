"""
BPO Financial Data Processing Module (Nova Estrutura)
=====================================================

Este módulo processa arquivos Excel com dados de BPO Financeiro (mensal).
Sheet: "Sheet"
Estrutura: Linha 1 = cabeçalho, Linha 2+ = dados

Autor: WaysSolutionHub
Data: 2025-11-25 (Refatorado)
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


def converter_valor(valor):
    """Converte um valor de célula para float ou None"""
    if valor is None or valor == '':
        return None

    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def converter_porcentagem(valor):
    """Converte um valor de célula para porcentagem (multiplica por 100)"""
    if valor is None or valor == '':
        return None

    try:
        return float(valor) * 100
    except (ValueError, TypeError):
        return None


def formatar_numero(valor):
    """Formata um número para exibição legível (ou 'N/A' se None)"""
    if valor is None:
        return "N/A"

    if isinstance(valor, (int, float)) and abs(valor) < 0.01:
        return "0.00"

    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(valor)


def processar_item_hierarquico(col_a, row_values, num_meses, meses_nomes, linha):
    """
    Processa um item hierárquico com a NOVA estrutura

    Estrutura FIXA:
    - Coluna 0 (A): Nome/Código
    - Colunas 1+ (B+): Meses (4 colunas cada: Orçado, Realizado, % Atingido, Diferença)
    - Últimas 3 colunas: Totais (Orçado Total, Realizado Total, Pendente Total)

    Args:
        col_a: Valor da coluna A (código e nome)
        row_values: Lista com todos os valores da linha
        num_meses: Número de meses
        meses_nomes: Lista com nomes dos meses
        linha: Número da linha atual

    Returns:
        dict: Dados estruturados do item
    """
    # Extrair código e nome
    codigo, nome, nivel = extrair_codigo_e_nome(col_a)

    # Processar dados mensais (começando no índice 1 = coluna B)
    dados_meses = []
    col_inicio_mes = 1  # Coluna B

    for i in range(num_meses):
        idx_base = col_inicio_mes + (i * 4)

        # Cada mês tem 4 colunas fixas:
        # 0: Valor Orçado
        # 1: Valor Realizado
        # 2: % Atingido (já vem como número, ex: 86.06 para 86,06%)
        # 3: Valor Diferença

        valor_orcado = converter_valor(row_values[idx_base]) if idx_base < len(row_values) else None
        valor_realizado = converter_valor(row_values[idx_base + 1]) if idx_base + 1 < len(row_values) else None
        perc_atingido = converter_valor(row_values[idx_base + 2]) if idx_base + 2 < len(row_values) else None  # SEM multiplicar por 100!
        valor_diferenca = converter_valor(row_values[idx_base + 3]) if idx_base + 3 < len(row_values) else None

        mes_data = {
            'mes_numero': i + 1,
            'mes_nome': meses_nomes[i] if i < len(meses_nomes) else f'Mês {i+1}',
            'valor_orcado': valor_orcado,
            'valor_realizado': valor_realizado,
            'perc_atingido': perc_atingido,
            'valor_diferenca': valor_diferenca,
        }
        dados_meses.append(mes_data)

    # Processar resultados totais (últimas 3 colunas)
    idx_resultados_inicio = col_inicio_mes + (num_meses * 4)

    valor_orcado_total = converter_valor(row_values[idx_resultados_inicio]) if idx_resultados_inicio < len(row_values) else None
    valor_realizado_total = converter_valor(row_values[idx_resultados_inicio + 1]) if idx_resultados_inicio + 1 < len(row_values) else None
    valor_pendente_total = converter_valor(row_values[idx_resultados_inicio + 2]) if idx_resultados_inicio + 2 < len(row_values) else None

    resultados = {
        'valor_orcado_total': valor_orcado_total,
        'valor_realizado_total': valor_realizado_total,
        'valor_pendente_total': valor_pendente_total
    }

    return {
        'codigo': codigo,
        'nome': nome,
        'nivel_hierarquia': nivel,
        'linha': linha,
        'dados_mensais': dados_meses,
        'resultados_totais': resultados
    }


# ============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ============================================================================

def process_bpo_file(file):
    """
    Processa arquivo Excel de BPO Financeiro (NOVA ESTRUTURA) e retorna dados estruturados.

    Estrutura da planilha:
    - Sheet: "Sheet"
    - Linha 1: Cabeçalho
    - Linha 2+: Dados começam
    - Coluna A: Código hierárquico e nome (ex: "1.01 - RECEITA VENDA SERVIÇO")
    - Coluna B+: Dados mensais (4 colunas por mês: Orçado, Realizado, % Ating, Diferença)
    - Últimas 3 colunas: Totais (Orçado Total, Realizado Total, Pendente Total)

    Args:
        file: Arquivo Excel (.xlsx ou .xls)

    Returns:
        dict: {
            'itens_hierarquicos': [...],  # Itens com hierarquia
            'totais_calculados': {},      # Para adicionar depois (quando souber a fórmula)
            'metadados': {...}            # Info sobre meses, totais, etc
        }
    """

    try:
        print("\n" + "="*100)
        print("🔄 PROCESSANDO PLANILHA BPO (NOVA ESTRUTURA)")
        print("="*100)

        # Carregar workbook (data_only=True para pegar valores calculados ao invés de fórmulas)
        wb = load_workbook(file, data_only=True)

        # Selecionar sheet 'Sheet'
        sheet_name = 'Sheet'
        if sheet_name not in wb.sheetnames:
            raise Exception(f"Sheet '{sheet_name}' não encontrada. Sheets disponíveis: {wb.sheetnames}")

        sheet = wb[sheet_name]
        print(f"✅ Sheet '{sheet_name}' encontrada")

        # Identificar estrutura da planilha
        total_colunas = sheet.max_column
        print(f"📊 Total de colunas na planilha: {total_colunas}")

        # Estrutura FIXA:
        # Coluna A (0): Nome/Código
        # Colunas B+ (1+): Meses (4 colunas cada) + 3 colunas de totais

        colunas_depois_nome = total_colunas - 1  # Tira coluna A
        colunas_totais = 3
        colunas_meses = colunas_depois_nome - colunas_totais
        num_meses = colunas_meses // 4

        print(f"📅 Número de meses detectados: {num_meses}")
        print(f"📋 Colunas de meses: {colunas_meses} ({num_meses} meses × 4 colunas)")
        print(f"📈 Colunas de totais: {colunas_totais}")

        # Nomes dos meses
        meses_nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

        print(f"🗓️  Meses processados: {', '.join(meses_nomes[:num_meses])}")

        # Processar itens hierárquicos (LINHA 2 em diante)
        itens_hierarquicos = []
        linha_atual = 2  # Começa na linha 2 (linha 1 = cabeçalho)

        print("\n" + "-"*100)
        print("📋 PROCESSANDO ITENS HIERÁRQUICOS")
        print("-"*100)

        while True:
            row_values = []
            for col in range(1, total_colunas + 1):
                cell_value = sheet.cell(row=linha_atual, column=col).value
                row_values.append(cell_value)

            # Verifica se linha está completamente vazia (fim da planilha)
            if all(v is None or str(v).strip() == '' for v in row_values):
                print(f"⏹️  Linha {linha_atual}: Vazia - fim dos dados")
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

                # Log apenas das primeiras 5 linhas para não poluir
                if len(itens_hierarquicos) <= 5:
                    print(f"✅ Linha {linha_atual}: [{item['codigo']}] {item['nome']}")
                    print(f"   └─ Meses: {len(item['dados_mensais'])} | Totais: Orçado={formatar_numero(item['resultados_totais']['valor_orcado_total'])}")

            linha_atual += 1

        print(f"\n📊 Total de itens processados: {len(itens_hierarquicos)}")

        # Montar estrutura final
        dados_processados = {
            'itens_hierarquicos': itens_hierarquicos,
            'totais_calculados': {
                # Será preenchido depois quando souber a fórmula
                # Estrutura planejada:
                # 'fluxo_caixa': {'receita': 0, 'despesa': 0, 'geral': 0},
                # 'real': {'receita': 0, 'despesa': 0, 'geral': 0},
                # 'real_mp': {'receita': 0, 'despesa': 0, 'geral': 0}
            },
            'metadados': {
                'total_colunas': total_colunas,
                'num_meses': num_meses,
                'meses': meses_nomes[:num_meses],
                'total_itens': len(itens_hierarquicos)
            }
        }

        print("\n" + "="*100)
        print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print("="*100)
        print(f"📊 Resumo:")
        print(f"   • Itens processados: {len(itens_hierarquicos)}")
        print(f"   • Meses: {num_meses} ({', '.join(meses_nomes[:num_meses])})")
        print(f"   • Total de colunas: {total_colunas}")
        print("="*100 + "\n")

        return dados_processados

    except Exception as e:
        print("\n" + "="*100)
        print(f"❌ ERRO AO PROCESSAR ARQUIVO BPO")
        print("="*100)
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*100 + "\n")
        raise Exception(f"Erro no processamento do BPO: {str(e)}")


def validate_bpo_data(dados):
    """
    Valida os dados de BPO processados antes de salvar no banco.

    Args:
        dados (dict): Dados processados pela função process_bpo_file()

    Returns:
        tuple: (bool, str) - (True/False, mensagem de erro/sucesso)
    """
    if not dados:
        return False, "Dados vazios ou inválidos"

    if 'itens_hierarquicos' not in dados:
        return False, "Estrutura de dados inválida: falta campo 'itens_hierarquicos'"

    if 'metadados' not in dados:
        return False, "Estrutura de dados inválida: falta campo 'metadados'"

    if len(dados['itens_hierarquicos']) == 0:
        return False, "Nenhum item hierárquico encontrado"

    return True, "Validação OK"
