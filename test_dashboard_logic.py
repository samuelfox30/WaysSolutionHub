#!/usr/bin/env python3
"""
Testa a lógica do dashboard BPO localmente
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.company_manager import CompanyManager

def simular_api_dados_bpo(empresa_id, ano_inicio, mes_inicio, ano_fim, mes_fim):
    """Simula a API de dados BPO"""
    cm = CompanyManager()

    meses_data = []
    ano_atual = ano_inicio
    mes_atual = mes_inicio

    while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
        dados = cm.buscar_dados_bpo_empresa(empresa_id, ano_atual, mes_atual)
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

    cm.close()

    print(f"\n✅ Encontrados {len(meses_data)} meses com dados\n")

    # Processar dados para ver a estrutura
    if meses_data:
        primeiro_mes = meses_data[0]
        dados = primeiro_mes['dados']

        print(f"Estrutura do primeiro mês ({primeiro_mes['mes']}/{primeiro_mes['ano']}):")
        print(f"  Chaves: {list(dados.keys())}")

        if 'resultados_fluxo' in dados:
            rf = dados['resultados_fluxo']
            print(f"  resultados_fluxo.secoes: {len(rf.get('secoes', []))} itens")

            # Mostrar primeiros itens
            for i, item in enumerate(rf.get('secoes', [])[:15]):
                tipo = item.get('tipo', 'N/A')
                if tipo == 'titulo':
                    print(f"    [{i}] TÍTULO: {item.get('texto', 'N/A')}")
                else:
                    nome = item.get('nome', 'N/A')
                    total = item.get('resultados_totais', {}).get('total_realizado', 0)
                    print(f"    [{i}] DADOS: {nome} | Total Realizado: R$ {total:,.2f}")

if __name__ == "__main__":
    print("="*60)
    print("TESTE DA LÓGICA DO DASHBOARD BPO")
    print("="*60)

    # Substitua estes valores pelos seus dados reais
    empresa_id = 1
    ano = 2025
    mes_inicio = 1
    mes_fim = 3

    simular_api_dados_bpo(empresa_id, ano, mes_inicio, ano, mes_fim)
