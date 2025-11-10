#!/usr/bin/env python3
"""
Script para verificar dados BPO no banco de dados
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
from models.company_manager import CompanyManager

def main():
    print("\n=== VERIFICANDO DADOS BPO NO BANCO ===\n")

    cm = CompanyManager()

    # Listar empresas
    print("📋 Empresas cadastradas:")
    empresas = cm.listar_todas_empresas()

    if not empresas:
        print("  ⚠ Nenhuma empresa cadastrada!")
        cm.close()
        return

    for empresa in empresas:
        print(f"\n  ID: {empresa['id']} | Nome: {empresa['nome']}")

        # Verificar se tem dados BPO
        sql = """
            SELECT DISTINCT ano, mes
            FROM TbBpoDados
            WHERE empresa_id = %s
            ORDER BY ano DESC, mes DESC
        """
        cm.cursor.execute(sql, (empresa['id'],))
        periodos = cm.cursor.fetchall()

        if periodos:
            print(f"    ✅ Dados BPO encontrados:")
            for ano, mes in periodos:
                print(f"      - {mes:02d}/{ano}")

                # Buscar um exemplo de dados
                dados = cm.buscar_dados_bpo_empresa(empresa['id'], ano, mes)
                if dados:
                    dados_json = dados['dados']
                    print(f"        Estrutura: {list(dados_json.keys())}")

                    # Verificar se tem resultados_fluxo
                    if 'resultados_fluxo' in dados_json:
                        rf = dados_json['resultados_fluxo']
                        print(f"        resultados_fluxo.secoes: {len(rf.get('secoes', []))} itens")

                        # Mostrar alguns itens
                        for i, item in enumerate(rf.get('secoes', [])[:3]):
                            tipo = item.get('tipo', 'N/A')
                            if tipo == 'titulo':
                                print(f"          [{i}] TÍTULO: {item.get('texto', 'N/A')}")
                            else:
                                nome = item.get('nome', 'N/A')
                                total_real = item.get('resultados_totais', {}).get('total_realizado', 0)
                                print(f"          [{i}] DADOS: {nome} | Total: R$ {total_real}")
                    else:
                        print(f"        ⚠ SEM resultados_fluxo!")

                    # Verificar metadados
                    if 'metadados' in dados_json:
                        meta = dados_json['metadados']
                        print(f"        Meses processados: {meta.get('num_meses', 0)}")
                        print(f"        Total de itens: {meta.get('total_itens', 0)}")
        else:
            print(f"    ⚠ Nenhum dado BPO encontrado")

    cm.close()
    print("\n")

if __name__ == "__main__":
    main()
