# 🔍 Diagnóstico: Por que os dados BPO não aparecem no dashboard?

## ✅ Checklist de Verificação

### 1. MySQL está rodando?

```bash
# Verificar se MySQL está rodando
sudo service mysql status

# Se não estiver, iniciar:
sudo service mysql start
```

### 2. Há dados BPO no banco?

Execute o script de verificação:

```python
python3 check_bpo_data.py
```

**Se não houver dados:**
- Você precisa fazer upload de uma planilha BPO primeiro
- Vá em: `/admin/empresas` → Botão "Upload BPO" → Selecione ano, arquivo e envie

### 3. Verificar logs do servidor

Quando acessar o dashboard BPO, a função `processar_dados_bpo_dashboard()` imprime MUITOS logs de debug no console do servidor.

**Como ver os logs:**

```bash
# Iniciar servidor Flask em modo debug
python3 src/app.py
```

Depois acesse o dashboard BPO no navegador e veja o console do terminal. Você verá algo como:

```
=== DEBUG processar_dados_bpo_dashboard ===
Tipo DRE: fluxo_caixa
Número de meses recebidos: 2

--- Processando Jan/2025 ---
Total de seções: 12
  [0] tipo=titulo | nome=RESULTADO POR FLUXO DE CAIXA
  [1] tipo=dados | nome=TOTAL RECEITA
  [2] tipo=dados | nome=TOTAL DESPESA
  [3] tipo=dados | nome=TOTAL GERAL
  ...

✓ Encontrado: RESULTADO POR FLUXO DE CAIXA no índice 0
  Receita (i+1): 150000.0
  Despesa (i+2): -80000.0
  Geral (i+3): 70000.0
...

=== RESULTADO FINAL ===
Totais acumulados: {...}
Receitas array: [150000.0, 180000.0]
Despesas array: [-80000.0, -95000.0]
Gerais array: [70000.0, 85000.0]
```

## 🐛 Problemas Comuns e Soluções

### Problema 1: "Número de meses recebidos: 0"

**Causa:** Não há dados no banco para o período selecionado

**Solução:**
1. Verifique se fez upload dos dados BPO
2. Verifique se o ano/mês selecionado corresponde aos dados salvos
3. Teste com período mais amplo (Janeiro a Dezembro do ano atual)

### Problema 2: "⚠ Sem resultados_fluxo neste mês"

**Causa:** A estrutura JSON salva não tem a seção `resultados_fluxo`

**Solução:**
1. Verifique se a planilha tem a seção "RESULTADO POR FLUXO DE CAIXA"
2. Refaça o upload da planilha
3. Verifique se o processamento foi bem-sucedido (veja logs do upload)

### Problema 3: "Total de seções: 0"

**Causa:** A seção `resultados_fluxo.secoes` está vazia

**Solução:**
1. A planilha não tem a estrutura esperada
2. Verifique se a planilha tem ao final:
   - RESULTADO POR FLUXO DE CAIXA (título)
   - TOTAL RECEITA (linha com dados)
   - TOTAL DESPESA (linha com dados)
   - TOTAL GERAL (linha com dados)
   - RESULTADO REAL (título)
   - ... (mais 3 linhas)
   - RESULTADO REAL + CUSTO MATERIA PRIMA... (título)
   - ... (mais 3 linhas)

### Problema 4: Valores aparecem como R$ 0,00

**Causa:** Os campos `total_realizado` estão vazios ou null

**Solução:**
1. Verifique se a planilha tem valores nas últimas colunas (colunas de totais)
2. A coluna esperada é "TOTAL REALIZADO" (2ª das 7 colunas finais)
3. Verifique se os valores não são fórmulas que retornam erro

## 📊 Estrutura Esperada da Planilha BPO

A planilha deve ter:

```
Linha 1-3: Cabeçalhos
Linha 4+: Dados hierárquicos
...
Linha X: "RESULTADO POR FLUXO DE CAIXA"
Linha X+1: TOTAL RECEITA [com dados nas colunas mensais e totais]
Linha X+2: TOTAL DESPESA [com dados nas colunas mensais e totais]
Linha X+3: TOTAL GERAL [com dados nas colunas mensais e totais]
Linha X+4: "RESULTADO REAL"
Linha X+5: TOTAL RECEITA [com dados]
Linha X+6: TOTAL DESPESA [com dados]
Linha X+7: TOTAL GERAL [com dados]
Linha X+8: "RESULTADO REAL + CUSTO MATERIA PRIMA PROPORCIONAL"
Linha X+9: TOTAL RECEITA [com dados]
Linha X+10: TOTAL DESPESA [com dados]
Linha X+11: TOTAL GERAL [com dados]
```

## 🎯 Teste Rápido

Execute este teste para simular o processamento:

```python
# No console Python
import sys
sys.path.insert(0, 'src')

from models.company_manager import CompanyManager

cm = CompanyManager()
dados = cm.buscar_dados_bpo_empresa(1, 2025, 1)  # empresa_id=1, ano=2025, mes=1

if dados:
    print("✅ Dados encontrados!")
    print("Chaves:", list(dados['dados'].keys()))

    if 'resultados_fluxo' in dados['dados']:
        rf = dados['dados']['resultados_fluxo']
        print(f"Seções: {len(rf.get('secoes', []))}")

        for i, item in enumerate(rf['secoes'][:5]):
            print(f"[{i}] tipo={item.get('tipo')} | nome={item.get('nome', item.get('texto'))}")
else:
    print("❌ Nenhum dado encontrado!")

cm.close()
```

## 🚀 Próximos Passos

1. Execute as verificações acima na ordem
2. Compartilhe os logs que aparecerem no console do servidor
3. Se necessário, podemos ajustar a lógica de processamento

---

**Dica:** A função `processar_dados_bpo_dashboard()` já está muito bem instrumentada com logs de debug. Os logs vão te dizer exatamente o que está acontecendo!
