#!/usr/bin/env python3
"""
Script de teste para processamento de planilha BPO Financeiro

Uso:
    python3 test_bpo_processing.py caminho/para/planilha.xlsx
"""

import sys
import os

# Adicionar src ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from controllers.data_processing.bpo_file_processing import process_bpo_file
import json


def main():
    if len(sys.argv) < 2:
        print("❌ Erro: Forneça o caminho da planilha BPO")
        print("\nUso:")
        print(f"    python3 {sys.argv[0]} caminho/para/planilha.xlsx")
        print("\nExemplo:")
        print(f"    python3 {sys.argv[0]} src/data_examples/planilha_bpo.xlsx")
        sys.exit(1)

    arquivo_path = sys.argv[1]

    # Verificar se arquivo existe
    if not os.path.exists(arquivo_path):
        print(f"❌ Erro: Arquivo não encontrado: {arquivo_path}")
        sys.exit(1)

    print(f"\n🔍 Testando processamento de: {arquivo_path}")
    print("="*80)

    try:
        # Abrir arquivo
        with open(arquivo_path, 'rb') as f:
            # Criar objeto similar ao que Flask envia
            class FileWrapper:
                def __init__(self, file_obj, filename):
                    self._file = file_obj
                    self.filename = filename

                def __getattr__(self, name):
                    return getattr(self._file, name)

            file_wrapper = FileWrapper(f, os.path.basename(arquivo_path))

            # Processar arquivo
            dados = process_bpo_file(file_wrapper)

        # Exibir estrutura JSON completa (apenas metadados)
        print("\n" + "="*80)
        print("ESTRUTURA DE DADOS RETORNADA (JSON)")
        print("="*80)
        print(json.dumps(dados['metadados'], indent=2, ensure_ascii=False))

        # Salvar dados completos em arquivo JSON
        output_file = 'bpo_dados_processados.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n✅ Dados completos salvos em: {output_file}")
        print(f"   Você pode abrir este arquivo para ver TODOS os dados processados!")

        print("\n" + "="*80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERRO durante o teste:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
