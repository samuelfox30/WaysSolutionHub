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


def calcular_totais_fluxo_caixa(itens_hierarquicos, num_meses):
    """
    Calcula os totais do 1º cenário: RESULTADO POR FLUXO DE CAIXA

    Para cada mês, calcula 3 totais em 4 colunas:
    - Orçamento: Receita, Despesa, Geral
    - Realizado: Receita, Despesa, Geral
    - % Atingido: Receita%, Despesa%, Geral%
    - Diferença: Receita, Despesa, Geral

    Args:
        itens_hierarquicos: Lista de itens processados
        num_meses: Número de meses

    Returns:
        dict: Totais calculados por mês
    """

    # Estrutura de retorno
    totais = {
        'fluxo_caixa': {},  # Será preenchido por mês
        'real': {},         # Para depois (vazio por enquanto)
        'real_mp': {}       # Para depois (vazio por enquanto)
    }

    # Encontrar os itens "1 - RECEITA" e "2 - DESPESAS"
    item_receita = None
    item_despesa = None

    for item in itens_hierarquicos:
        nome_upper = item['nome'].upper()
        codigo = item['codigo']

        # Procurar por "1 - RECEITA" ou similar
        if codigo == "1" or ("RECEITA" in nome_upper and codigo.startswith("1")):
            if not item_receita:  # Pegar o primeiro
                item_receita = item
                print(f"✅ Item RECEITA encontrado: [{item['codigo']}] {item['nome']}")

        # Procurar por "2 - DESPESAS" ou similar
        if codigo == "2" or ("DESPESA" in nome_upper and codigo.startswith("2")):
            if not item_despesa:  # Pegar o primeiro
                item_despesa = item
                print(f"✅ Item DESPESA encontrado: [{item['codigo']}] {item['nome']}")

    if not item_receita or not item_despesa:
        print("⚠️  ATENÇÃO: Não foi possível encontrar itens RECEITA e/ou DESPESAS!")
        print(f"   Item RECEITA: {'Encontrado' if item_receita else 'NÃO ENCONTRADO'}")
        print(f"   Item DESPESA: {'Encontrado' if item_despesa else 'NÃO ENCONTRADO'}")
        return totais

    # Calcular para cada mês
    for mes_num in range(1, num_meses + 1):
        # Encontrar dados deste mês
        dados_mes_receita = next((m for m in item_receita['dados_mensais'] if m['mes_numero'] == mes_num), None)
        dados_mes_despesa = next((m for m in item_despesa['dados_mensais'] if m['mes_numero'] == mes_num), None)

        if not dados_mes_receita or not dados_mes_despesa:
            print(f"⚠️  Mês {mes_num}: Dados não encontrados")
            continue

        # ====================================================================
        # COLUNA 1 - ORÇAMENTO
        # ====================================================================
        orcamento_receita = dados_mes_receita['valor_orcado'] or 0
        orcamento_despesa = dados_mes_despesa['valor_orcado'] or 0
        orcamento_geral = orcamento_receita - orcamento_despesa

        # ====================================================================
        # COLUNA 2 - REALIZADO
        # ====================================================================
        realizado_receita = dados_mes_receita['valor_realizado'] or 0
        realizado_despesa = dados_mes_despesa['valor_realizado'] or 0
        realizado_geral = realizado_receita - realizado_despesa

        # ====================================================================
        # COLUNA 3 - % ATINGIDO
        # ====================================================================
        # Fórmula: (Realizado / Orçado) * 100
        if orcamento_receita != 0:
            perc_receita = (realizado_receita / orcamento_receita) * 100
        else:
            perc_receita = 0

        if orcamento_despesa != 0:
            perc_despesa = (realizado_despesa / orcamento_despesa) * 100
        else:
            perc_despesa = 0

        if orcamento_geral != 0:
            perc_geral = (realizado_geral / orcamento_geral) * 100
        else:
            perc_geral = 0

        # ====================================================================
        # COLUNA 4 - DIFERENÇA
        # ====================================================================
        # Receita: Realizado - Orçado
        # Despesa: Orçado - Realizado (INVERTIDO!)
        # Geral: Receita + Despesa
        diferenca_receita = realizado_receita - orcamento_receita
        diferenca_despesa = orcamento_despesa - realizado_despesa  # INVERTIDO
        diferenca_geral = diferenca_receita + diferenca_despesa

        # Salvar totais deste mês
        totais['fluxo_caixa'][mes_num] = {
            'orcamento': {
                'receita': orcamento_receita,
                'despesa': orcamento_despesa,
                'geral': orcamento_geral
            },
            'realizado': {
                'receita': realizado_receita,
                'despesa': realizado_despesa,
                'geral': realizado_geral
            },
            'perc_atingido': {
                'receita': perc_receita,
                'despesa': perc_despesa,
                'geral': perc_geral
            },
            'diferenca': {
                'receita': diferenca_receita,
                'despesa': diferenca_despesa,
                'geral': diferenca_geral
            }
        }

        # Log apenas do primeiro mês para não poluir
        if mes_num == 1:
            print(f"\n📅 Mês {mes_num} - Exemplo de cálculo:")
            print(f"   ORÇAMENTO  → Receita: R$ {formatar_numero(orcamento_receita)} | Despesa: R$ {formatar_numero(orcamento_despesa)} | Geral: R$ {formatar_numero(orcamento_geral)}")
            print(f"   REALIZADO  → Receita: R$ {formatar_numero(realizado_receita)} | Despesa: R$ {formatar_numero(realizado_despesa)} | Geral: R$ {formatar_numero(realizado_geral)}")
            print(f"   % ATINGIDO → Receita: {perc_receita:.2f}% | Despesa: {perc_despesa:.2f}% | Geral: {perc_geral:.2f}%")
            print(f"   DIFERENÇA  → Receita: R$ {formatar_numero(diferenca_receita)} | Despesa: R$ {formatar_numero(diferenca_despesa)} | Geral: R$ {formatar_numero(diferenca_geral)}")

    print(f"\n✅ Totais do Fluxo de Caixa calculados para {len(totais['fluxo_caixa'])} meses")

    # ========================================================================
    # CALCULAR 2º CENÁRIO: RESULTADO REAL
    # ========================================================================
    print("\n" + "-"*100)
    print("🧮 CALCULANDO TOTAIS - RESULTADO REAL")
    print("-"*100)

    # Itens a subtrair da RECEITA para o Resultado Real
    itens_subtrair_receita = ['RECEITA EMPRESTIMO', 'OUTRAS RECEITAS']

    # Itens a subtrair da DESPESA para o Resultado Real
    itens_subtrair_despesa = [
        'OUTRAS DESPESAS NÃO DEDUTIVEIS',
        'Distribuição de lucro Associados',
        'SAIDA- EMPRESTIMOS',
        'INVESTIMENTOS'
    ]

    # Função auxiliar para buscar valores de um item por nome
    def buscar_valores_item(nome_item):
        """Retorna os dados_mensais de um item pelo nome"""
        for item in itens_hierarquicos:
            if item['nome'].strip().upper() == nome_item.upper():
                return item.get('dados_mensais', [])
        return []

    # Função auxiliar para calcular total de subtração
    def calcular_total_subtracao(nomes_itens, mes_num, campo):
        """
        Soma os valores de múltiplos itens para um mês específico
        campo: 'valor_orcado', 'valor_realizado'
        """
        total = 0
        for nome in nomes_itens:
            dados_mensais = buscar_valores_item(nome)
            for mes_data in dados_mensais:
                if mes_data['mes_numero'] == mes_num:
                    valor = mes_data.get(campo, 0)
                    total += valor if valor else 0
                    break
        return total

    # Calcular para cada mês
    for mes_num in range(1, num_meses + 1):
        # Pegar dados do Fluxo de Caixa deste mês
        dados_fc = totais['fluxo_caixa'].get(mes_num)

        if not dados_fc:
            print(f"⚠️  Mês {mes_num}: Dados do Fluxo de Caixa não encontrados")
            continue

        # ====================================================================
        # COLUNA 1 - ORÇAMENTO
        # ====================================================================
        orcamento_receita_fc = dados_fc['orcamento']['receita']
        orcamento_despesa_fc = dados_fc['orcamento']['despesa']

        # Subtrair os itens específicos
        subtracao_receita_orcado = calcular_total_subtracao(itens_subtrair_receita, mes_num, 'valor_orcado')
        subtracao_despesa_orcado = calcular_total_subtracao(itens_subtrair_despesa, mes_num, 'valor_orcado')

        orcamento_receita_real = orcamento_receita_fc - subtracao_receita_orcado
        orcamento_despesa_real = orcamento_despesa_fc - subtracao_despesa_orcado
        orcamento_geral_real = orcamento_receita_real - orcamento_despesa_real

        # ====================================================================
        # COLUNA 2 - REALIZADO
        # ====================================================================
        realizado_receita_fc = dados_fc['realizado']['receita']
        realizado_despesa_fc = dados_fc['realizado']['despesa']

        # Subtrair os itens específicos
        subtracao_receita_realizado = calcular_total_subtracao(itens_subtrair_receita, mes_num, 'valor_realizado')
        subtracao_despesa_realizado = calcular_total_subtracao(itens_subtrair_despesa, mes_num, 'valor_realizado')

        realizado_receita_real = realizado_receita_fc - subtracao_receita_realizado
        realizado_despesa_real = realizado_despesa_fc - subtracao_despesa_realizado
        realizado_geral_real = realizado_receita_real - realizado_despesa_real

        # ====================================================================
        # COLUNA 3 - % ATINGIDO
        # ====================================================================
        # Fórmula: (Realizado / Orçado) * 100
        if orcamento_receita_real != 0:
            perc_receita_real = (realizado_receita_real / orcamento_receita_real) * 100
        else:
            perc_receita_real = 0

        if orcamento_despesa_real != 0:
            perc_despesa_real = (realizado_despesa_real / orcamento_despesa_real) * 100
        else:
            perc_despesa_real = 0

        if orcamento_geral_real != 0:
            perc_geral_real = (realizado_geral_real / orcamento_geral_real) * 100
        else:
            perc_geral_real = 0

        # ====================================================================
        # COLUNA 4 - DIFERENÇA
        # ====================================================================
        # Receita: Realizado - Orçado
        # Despesa: Orçado - Realizado (INVERTIDO!)
        # Geral: Receita + Despesa
        diferenca_receita_real = realizado_receita_real - orcamento_receita_real
        diferenca_despesa_real = orcamento_despesa_real - realizado_despesa_real  # INVERTIDO
        diferenca_geral_real = diferenca_receita_real + diferenca_despesa_real

        # Salvar totais deste mês
        totais['real'][mes_num] = {
            'orcamento': {
                'receita': orcamento_receita_real,
                'despesa': orcamento_despesa_real,
                'geral': orcamento_geral_real
            },
            'realizado': {
                'receita': realizado_receita_real,
                'despesa': realizado_despesa_real,
                'geral': realizado_geral_real
            },
            'perc_atingido': {
                'receita': perc_receita_real,
                'despesa': perc_despesa_real,
                'geral': perc_geral_real
            },
            'diferenca': {
                'receita': diferenca_receita_real,
                'despesa': diferenca_despesa_real,
                'geral': diferenca_geral_real
            }
        }

        # Log apenas do primeiro mês
        if mes_num == 1:
            print(f"\n📅 Mês {mes_num} - Exemplo de cálculo (Resultado Real):")
            print(f"   ORÇAMENTO  → Receita: R$ {formatar_numero(orcamento_receita_real)} | Despesa: R$ {formatar_numero(orcamento_despesa_real)} | Geral: R$ {formatar_numero(orcamento_geral_real)}")
            print(f"   REALIZADO  → Receita: R$ {formatar_numero(realizado_receita_real)} | Despesa: R$ {formatar_numero(realizado_despesa_real)} | Geral: R$ {formatar_numero(realizado_geral_real)}")
            print(f"   % ATINGIDO → Receita: {perc_receita_real:.2f}% | Despesa: {perc_despesa_real:.2f}% | Geral: {perc_geral_real:.2f}%")
            print(f"   DIFERENÇA  → Receita: R$ {formatar_numero(diferenca_receita_real)} | Despesa: R$ {formatar_numero(diferenca_despesa_real)} | Geral: R$ {formatar_numero(diferenca_geral_real)}")

    print(f"\n✅ Totais do Resultado Real calculados para {len(totais['real'])} meses")

    # ========================================================================
    # CALCULAR 3º CENÁRIO: RESULTADO REAL + CUSTO MATÉRIA PRIMA
    # ========================================================================
    print("\n" + "-"*100)
    print("🧮 CALCULANDO TOTAIS - RESULTADO REAL + CUSTO MATÉRIA PRIMA")
    print("-"*100)

    # Item a buscar: CUSTO MATERIA PRIMA
    item_custo_mp_nome = 'CUSTO MATERIA PRIMA'

    # Calcular para cada mês
    for mes_num in range(1, num_meses + 1):
        # Pegar dados do cenário "Real" deste mês
        dados_real = totais['real'].get(mes_num)

        if not dados_real:
            print(f"⚠️  Mês {mes_num}: Dados do Resultado Real não encontrados")
            continue

        # ====================================================================
        # COLUNA 1 - ORÇAMENTO
        # ====================================================================
        # Mesmos valores do cenário "Real"
        orcamento_receita_mp = dados_real['orcamento']['receita']
        orcamento_despesa_mp = dados_real['orcamento']['despesa']
        orcamento_geral_mp = dados_real['orcamento']['geral']

        # ====================================================================
        # COLUNA 2 - REALIZADO
        # ====================================================================
        # Total Receita = igual ao cenário "Real"
        realizado_receita_mp = dados_real['realizado']['receita']

        # Buscar valores de CUSTO MATERIA PRIMA
        dados_custo_mp = buscar_valores_item(item_custo_mp_nome)
        custo_mp_orcado = 0
        custo_mp_realizado = 0

        if dados_custo_mp:
            for mes_data in dados_custo_mp:
                if mes_data['mes_numero'] == mes_num:
                    custo_mp_orcado = mes_data.get('valor_orcado', 0) or 0
                    custo_mp_realizado = mes_data.get('valor_realizado', 0) or 0
                    break

        # Total Despesa (fórmula complexa):
        # ((CUSTO_MP_ORCADO / RECEITA_ORCADO) * RECEITA_REALIZADO - CUSTO_MP_REALIZADO)
        # + DESPESA_REAL_REALIZADO - CUSTO_MP_REALIZADO

        despesa_real_realizado = dados_real['realizado']['despesa']

        if orcamento_receita_mp != 0:
            parte1 = ((custo_mp_orcado / orcamento_receita_mp) * realizado_receita_mp) - custo_mp_realizado
        else:
            parte1 = 0

        realizado_despesa_mp = parte1 + despesa_real_realizado - custo_mp_realizado
        realizado_geral_mp = realizado_receita_mp - realizado_despesa_mp

        # ====================================================================
        # COLUNA 3 - % ATINGIDO
        # ====================================================================
        # Fórmula: (Realizado / Orçado) * 100
        if orcamento_receita_mp != 0:
            perc_receita_mp = (realizado_receita_mp / orcamento_receita_mp) * 100
        else:
            perc_receita_mp = 0

        if orcamento_despesa_mp != 0:
            perc_despesa_mp = (realizado_despesa_mp / orcamento_despesa_mp) * 100
        else:
            perc_despesa_mp = 0

        if orcamento_geral_mp != 0:
            perc_geral_mp = (realizado_geral_mp / orcamento_geral_mp) * 100
        else:
            perc_geral_mp = 0

        # ====================================================================
        # COLUNA 4 - DIFERENÇA
        # ====================================================================
        # Receita: Realizado - Orçado
        # Despesa: Orçado - Realizado (INVERTIDO!)
        # Geral: Receita + Despesa
        diferenca_receita_mp = realizado_receita_mp - orcamento_receita_mp
        diferenca_despesa_mp = orcamento_despesa_mp - realizado_despesa_mp  # INVERTIDO
        diferenca_geral_mp = diferenca_receita_mp + diferenca_despesa_mp

        # Salvar totais deste mês
        totais['real_mp'][mes_num] = {
            'orcamento': {
                'receita': orcamento_receita_mp,
                'despesa': orcamento_despesa_mp,
                'geral': orcamento_geral_mp
            },
            'realizado': {
                'receita': realizado_receita_mp,
                'despesa': realizado_despesa_mp,
                'geral': realizado_geral_mp
            },
            'perc_atingido': {
                'receita': perc_receita_mp,
                'despesa': perc_despesa_mp,
                'geral': perc_geral_mp
            },
            'diferenca': {
                'receita': diferenca_receita_mp,
                'despesa': diferenca_despesa_mp,
                'geral': diferenca_geral_mp
            }
        }

        # Log apenas do primeiro mês
        if mes_num == 1:
            print(f"\n📅 Mês {mes_num} - Exemplo de cálculo (Resultado Real + Custo MP):")
            print(f"   CUSTO MP   → Orçado: R$ {formatar_numero(custo_mp_orcado)} | Realizado: R$ {formatar_numero(custo_mp_realizado)}")
            print(f"   ORÇAMENTO  → Receita: R$ {formatar_numero(orcamento_receita_mp)} | Despesa: R$ {formatar_numero(orcamento_despesa_mp)} | Geral: R$ {formatar_numero(orcamento_geral_mp)}")
            print(f"   REALIZADO  → Receita: R$ {formatar_numero(realizado_receita_mp)} | Despesa: R$ {formatar_numero(realizado_despesa_mp)} | Geral: R$ {formatar_numero(realizado_geral_mp)}")
            print(f"   % ATINGIDO → Receita: {perc_receita_mp:.2f}% | Despesa: {perc_despesa_mp:.2f}% | Geral: {perc_geral_mp:.2f}%")
            print(f"   DIFERENÇA  → Receita: R$ {formatar_numero(diferenca_receita_mp)} | Despesa: R$ {formatar_numero(diferenca_despesa_mp)} | Geral: R$ {formatar_numero(diferenca_geral_mp)}")

    print(f"\n✅ Totais do Resultado Real + Custo MP calculados para {len(totais['real_mp'])} meses")

    return totais


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

        # ========================================================================
        # CALCULAR TOTAIS (1º CENÁRIO: RESULTADO POR FLUXO DE CAIXA)
        # ========================================================================
        print("\n" + "-"*100)
        print("🧮 CALCULANDO TOTAIS - RESULTADO POR FLUXO DE CAIXA")
        print("-"*100)

        totais_calculados = calcular_totais_fluxo_caixa(itens_hierarquicos, num_meses)

        # Montar estrutura final
        dados_processados = {
            'itens_hierarquicos': itens_hierarquicos,
            'totais_calculados': totais_calculados,
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
