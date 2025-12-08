"""
Módulo para cálculo de indicadores financeiros do relatório de viabilidade
"""
try:
    import numpy_financial as npf
except ImportError:
    # Fallback para numpy antigo
    import numpy as np
    npf = np

from typing import Dict, Any


def format_money(valor):
    """Formata valor para formato brasileiro R$ X.XXX,XX"""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(valor):
    """Formata percentual com 2 casas decimais"""
    if valor is None:
        return "0,00%"
    return f"{valor:.2f}%".replace(".", ",")


def calcular_indicadores_viabilidade(dados_empresa):
    """
    Calcula todos os indicadores necessários para o relatório de viabilidade

    Args:
        dados_empresa: Dict com dados retornados por buscar_dados_empresa()

    Returns:
        Dict com todos os indicadores calculados e formatados
    """

    # Dicionário para armazenar os indicadores
    indicadores = {}

    # ====================================================================
    # 1. EXTRAIR DADOS BRUTOS POR CENÁRIO
    # ====================================================================

    cenarios = {
        'Viabilidade Real': {'receita': 0, 'despesas': 0, 'dividas': 0, 'investimentos': 0},
        'Viabilidade PE': {'receita': 0, 'despesas': 0, 'dividas': 0, 'investimentos': 0},
        'Viabilidade Ideal': {'receita': 0, 'despesas': 0, 'dividas': 0, 'investimentos': 0}
    }

    # Mapear nomes dos grupos
    mapa_grupos = {
        'Viabilidade Real': 'Viabilidade Real',
        'Viabilidade PE': 'Viabilidade PE',
        'Viabilidade Ideal': 'Viabilidade Ideal'
    }

    # Extrair receitas e despesas de TbItens
    for item in dados_empresa.get('TbItens', []):
        grupo, subgrupo, descricao, percentual, valor = item

        if grupo in mapa_grupos:
            cenario_key = mapa_grupos[grupo]

            # Receita
            if subgrupo == 'Receita':
                cenarios[cenario_key]['receita'] += abs(valor) if valor else 0

            # Despesas (todos os subgrupos exceto Receita e Geral)
            elif subgrupo not in ['Receita', 'Geral']:
                cenarios[cenario_key]['despesas'] += abs(valor) if valor else 0

    # Extrair dívidas de TbItensDividas
    for item in dados_empresa.get('TbItensDividas', []):
        grupo, subgrupo, descricao, parcela, juros, total = item

        if grupo in mapa_grupos:
            cenario_key = mapa_grupos[grupo]
            cenarios[cenario_key]['dividas'] += abs(total) if total else 0

    # Extrair investimentos de TbItensInvestimentos
    for item in dados_empresa.get('TbItensInvestimentos', []):
        grupo, subgrupo, descricao, parcela, juros, total = item

        if grupo in mapa_grupos:
            cenario_key = mapa_grupos[grupo]
            cenarios[cenario_key]['investimentos'] += abs(total) if total else 0

    # Extrair capital investido total de TbItensInvestimentoGeral
    capital_investido = 0
    for item in dados_empresa.get('TbItensInvestimentoGeral', []):
        grupo, subgrupo, descricao, valor = item
        capital_investido += abs(valor) if valor else 0

    # Se não houver dados de investimento geral, usar um valor padrão
    if capital_investido == 0:
        capital_investido = 500000.00  # Valor padrão do exemplo

    # ====================================================================
    # 2. CALCULAR INDICADORES BÁSICOS POR CENÁRIO
    # ====================================================================

    for nome_cenario, dados in cenarios.items():
        # Ajustar nome para as chaves
        sufixo = nome_cenario.split()[-1].lower()  # 'real', 'pe', 'ideal'

        # Receita
        indicadores[f'receita_{sufixo}'] = format_money(dados['receita'])
        indicadores[f'receita_{sufixo}_num'] = dados['receita']

        # Despesas totais (despesas + dívidas + investimentos)
        despesas_totais = dados['despesas'] + dados['dividas'] + dados['investimentos']
        indicadores[f'despesas_{sufixo}'] = format_money(despesas_totais)
        indicadores[f'despesas_{sufixo}_num'] = despesas_totais

        # Lucro líquido mensal
        lucro = dados['receita'] - despesas_totais
        indicadores[f'lucro_{sufixo}'] = format_money(lucro)
        indicadores[f'lucro_{sufixo}_num'] = lucro

        # Margem líquida
        margem = (lucro / dados['receita'] * 100) if dados['receita'] > 0 else 0
        indicadores[f'margem_{sufixo}'] = format_percent(margem)
        indicadores[f'margem_{sufixo}_num'] = margem

        # Lucro anualizado
        lucro_anual = lucro * 12
        indicadores[f'lucro_anual_{sufixo}'] = format_money(lucro_anual)
        indicadores[f'lucro_anual_{sufixo}_num'] = lucro_anual

    # ====================================================================
    # 3. CAPITAL INVESTIDO
    # ====================================================================

    indicadores['capital_investido'] = format_money(capital_investido)
    indicadores['capital_investido_num'] = capital_investido

    # ====================================================================
    # 4. PONTO DE EQUILÍBRIO E MARGEM DE SEGURANÇA
    # ====================================================================

    # Ponto de equilíbrio = despesas totais do cenário PE
    ponto_equilibrio = indicadores['despesas_pe_num']
    indicadores['ponto_equilibrio'] = format_money(ponto_equilibrio)
    indicadores['ponto_equilibrio_num'] = ponto_equilibrio

    # Margem de segurança = receita real - ponto de equilíbrio
    margem_seguranca = indicadores['receita_real_num'] - ponto_equilibrio
    indicadores['margem_seguranca'] = format_money(margem_seguranca)
    indicadores['margem_seguranca_num'] = margem_seguranca

    # ====================================================================
    # 5. NECESSIDADE DE CAPITAL DE GIRO
    # ====================================================================

    for sufixo in ['real', 'pe', 'ideal']:
        custo_mensal = indicadores[f'despesas_{sufixo}_num']

        # Reservas (1, 3, 6 meses)
        indicadores[f'reserva_1mes_{sufixo}'] = format_money(custo_mensal)
        indicadores[f'reserva_1mes_{sufixo}_num'] = custo_mensal

        indicadores[f'reserva_3meses_{sufixo}'] = format_money(custo_mensal * 3)
        indicadores[f'reserva_3meses_{sufixo}_num'] = custo_mensal * 3

        indicadores[f'reserva_6meses_{sufixo}'] = format_money(custo_mensal * 6)
        indicadores[f'reserva_6meses_{sufixo}_num'] = custo_mensal * 6

        # Custo de juros (3% a.m. sobre reserva mínima)
        taxa_juros_mensal = 0.03
        custo_juros_mensal = custo_mensal * taxa_juros_mensal
        custo_juros_anual = custo_juros_mensal * 12

        indicadores[f'custo_juros_mensal_{sufixo}'] = format_money(custo_juros_mensal)
        indicadores[f'custo_juros_mensal_{sufixo}_num'] = custo_juros_mensal

        indicadores[f'custo_juros_anual_{sufixo}'] = format_money(custo_juros_anual)
        indicadores[f'custo_juros_anual_{sufixo}_num'] = custo_juros_anual

        # % do lucro anualizado consumido por juros
        lucro_anual = indicadores[f'lucro_anual_{sufixo}_num']
        if lucro_anual > 0:
            perc_juros = (custo_juros_anual / lucro_anual) * 100
        else:
            perc_juros = 0  # Evita divisão por zero

        indicadores[f'perc_juros_lucro_{sufixo}'] = format_percent(perc_juros)
        indicadores[f'perc_juros_lucro_{sufixo}_num'] = perc_juros

    # ====================================================================
    # 6. INDICADORES DE RETORNO (VPL, TIR, Payback)
    # ====================================================================

    # Taxa Mínima de Atratividade (TMA)
    tma = 0.12  # 12% a.a.

    # Para cada cenário (Real e Ideal)
    for sufixo in ['real', 'ideal']:
        lucro_anual = indicadores[f'lucro_anual_{sufixo}_num']

        # Fluxo de caixa: investimento inicial negativo + lucros anuais por 5 anos
        fluxo_caixa = [-capital_investido] + [lucro_anual] * 5

        # VPL (Valor Presente Líquido)
        try:
            vpl = npf.npv(tma, fluxo_caixa)
            indicadores[f'vpl_{sufixo}'] = format_money(vpl)
            indicadores[f'vpl_{sufixo}_num'] = vpl
        except:
            indicadores[f'vpl_{sufixo}'] = "N/A"
            indicadores[f'vpl_{sufixo}_num'] = 0

        # TIR (Taxa Interna de Retorno)
        try:
            tir = npf.irr(fluxo_caixa)
            # Verifica se é um número válido
            import math
            if math.isnan(tir) or math.isinf(tir):
                tir = 0
            tir_percent = tir * 100
            indicadores[f'tir_{sufixo}'] = format_percent(tir_percent)
            indicadores[f'tir_{sufixo}_num'] = tir_percent
        except:
            indicadores[f'tir_{sufixo}'] = "N/A"
            indicadores[f'tir_{sufixo}_num'] = 0

        # Payback (Tempo de retorno)
        if lucro_anual > 0:
            payback_anos = capital_investido / lucro_anual
            indicadores[f'payback_{sufixo}'] = f"{payback_anos:.2f} anos".replace(".", ",")
            indicadores[f'payback_{sufixo}_num'] = payback_anos
        else:
            indicadores[f'payback_{sufixo}'] = "N/A"
            indicadores[f'payback_{sufixo}_num'] = 0

    # ====================================================================
    # 7. VARIÁVEIS AUXILIARES PARA TEXTOS DINÂMICOS
    # ====================================================================

    # Status da viabilidade (baseado no VPL)
    if indicadores.get('vpl_real_num', 0) < 0:
        indicadores['status_viabilidade_real'] = "inviável financeiramente"
    elif indicadores.get('vpl_real_num', 0) < 100000:
        indicadores['status_viabilidade_real'] = "viável, mas com baixa rentabilidade"
    else:
        indicadores['status_viabilidade_real'] = "altamente viável e lucrativo"

    if indicadores.get('vpl_ideal_num', 0) > 0:
        indicadores['status_viabilidade_ideal'] = "altamente viável e lucrativo"
    else:
        indicadores['status_viabilidade_ideal'] = "necessita ajustes"

    # Conclusão automática
    if margem_seguranca < 5000:
        indicadores['conclusao'] = "alta vulnerabilidade operacional"
    elif margem_seguranca < 20000:
        indicadores['conclusao'] = "risco moderado"
    else:
        indicadores['conclusao'] = "margem de segurança adequada"

    return indicadores
