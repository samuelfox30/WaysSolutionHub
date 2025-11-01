# 📊 Como Testar o Processamento de Planilha BPO Financeiro

## 🎯 O que foi implementado

A função `process_bpo_file()` no arquivo `src/controllers/data_processing/bpo_file_processing.py` processa planilhas Excel de BPO Financeiro com a seguinte estrutura:

### Estrutura da Planilha Esperada:

- **Linha 4+**: Início dos dados
- **Coluna A**: Código hierárquico + Nome (ex: "1.01.06 - PMW RECEITA VENDA SERVIÇO")
- **Coluna B**: % Viabilidade
- **Coluna C**: Valor Viabilidade (R$)
- **Colunas D+**: Dados mensais (4 colunas por mês)
  - Coluna 1: % Realizado
  - Coluna 2: Valor Realizado
  - Coluna 3: % Atingido
  - Coluna 4: Valor Diferença
- **Últimas 7 colunas**: Resultados totais
  1. Previsão Total
  2. Total Realizado
  3. Diferença Total
  4. Média % Realizado
  5. Média Valor Realizado
  6. Média % Diferença
  7. Média Valor Diferença

### Seção Especial no Final:

A planilha termina com a seção **"RESULTADO POR FLUXO DE CAIXA"** contendo:
- TOTAL RECEITA (com dados)
- TOTAL DESPESA (com dados)
- TOTAL GERAL (com dados)
- RESULTADO REAL (título)
- Mais 3 linhas de totais
- RESULTADO REAL + CUSTO MATERIA PRIMA PROPORCIONAL (título)
- Mais 3 linhas de totais

---

## 🚀 Como Testar

### Método 1: Via Script de Teste (Recomendado)

```bash
# No diretório raiz do projeto
python3 test_bpo_processing.py caminho/para/sua_planilha.xlsx
```

**O que o script faz:**
1. ✅ Carrega a planilha
2. ✅ Processa todos os dados
3. ✅ Exibe resumo visual no terminal
4. ✅ Salva dados completos em `bpo_dados_processados.json`

**Exemplo de saída:**
```
================================================================================
INICIANDO PROCESSAMENTO DA PLANILHA BPO FINANCEIRO
================================================================================

📊 Total de colunas encontradas: 18
📅 Número de meses detectados: 2
📈 Estrutura: 3 fixas + 8 mensais (2 meses) + 7 resultados

🔍 Processando itens hierárquicos...
✅ Total de itens hierárquicos processados: 250

🔍 Processando seção RESULTADO POR FLUXO DE CAIXA...
  📌 Título encontrado: RESULTADO POR FLUXO DE CAIXA
✅ Total de linhas na seção de resultados: 12

================================================================================
RESUMO DO PROCESSAMENTO
================================================================================

📊 METADADOS:
   • Total de colunas: 18
   • Número de meses: 2
   • Meses: Janeiro, Fevereiro
   • Total de itens hierárquicos: 250
   • Total de linhas de resultados: 12

📋 PRIMEIROS 5 ITENS HIERÁRQUICOS:
   1. [1] RECEITA
      └─ Viabilidade: 100.0% | R$ 50000.0
   2.   [1.01] RECEITA VENDA SERVIÇO
      └─ Viabilidade: 60.0% | R$ 30000.0
   ...

✅ Dados completos salvos em: bpo_dados_processados.json
```

### Método 2: Via Interface Web (Após integração completa)

1. Inicie o servidor Flask:
   ```bash
   python3 src/app.py
   ```

2. Acesse: http://localhost:5000

3. Vá em **Empresas** → **Upload** → Tab **BPO Financeiro**

4. Selecione:
   - Mês
   - Ano
   - Arquivo Excel

5. Clique em **Enviar Dados de BPO**

---

## 📄 Estrutura de Dados Retornada

A função retorna um dicionário com:

```python
{
    'itens_hierarquicos': [
        {
            'codigo': '1.01.06',
            'nome': 'PMW RECEITA VENDA SERVIÇO',
            'nivel_hierarquia': 3,
            'linha': 6,
            'viabilidade': {
                'percentual': 15.5,
                'valor': 7750.0
            },
            'dados_mensais': [
                {
                    'mes_numero': 1,
                    'mes_nome': 'Janeiro',
                    'perc_realizado': 12.3,
                    'valor_realizado': 6150.0,
                    'perc_atingido': 79.4,
                    'valor_diferenca': -1600.0
                },
                # ... mais meses
            ],
            'resultados_totais': {
                'previsao_total': 93000.0,
                'total_realizado': 85000.0,
                'diferenca_total': -8000.0,
                'media_perc_realizado': 91.4,
                'media_valor_realizado': 42500.0,
                'media_perc_diferenca': -8.6,
                'media_valor_diferenca': -4000.0
            }
        },
        # ... mais itens
    ],
    'resultados_fluxo': {
        'secoes': [
            {
                'tipo': 'titulo',
                'texto': 'RESULTADO POR FLUXO DE CAIXA',
                'linha': 273
            },
            {
                'tipo': 'dados',
                'nome': 'TOTAL RECEITA',
                'linha': 274,
                'viabilidade': {...},
                'dados_mensais': [...],
                'resultados_totais': {...}
            },
            # ... mais linhas
        ],
        'total_linhas': 12
    },
    'metadados': {
        'total_colunas': 18,
        'num_meses': 2,
        'meses': ['Janeiro', 'Fevereiro'],
        'total_itens': 250,
        'total_resultados': 12
    }
}
```

---

## 🔍 Validações Implementadas

A função automaticamente:

- ✅ Detecta número de meses baseado no total de colunas
- ✅ Identifica hierarquia (níveis 1, 2, 3, 4, etc.) contando pontos no código
- ✅ Converte valores para float (ou None se vazio)
- ✅ Diferencia títulos de dados na seção de resultados
- ✅ Para ao encontrar linha vazia
- ✅ Identifica automaticamente a seção "RESULTADO POR FLUXO DE CAIXA"

---

## ⚠️ Próximos Passos (Para Integração Completa)

Para integrar com o banco de dados, você precisará:

### 1. Criar Tabelas no Banco de Dados

Sugestão de estrutura:

```sql
-- Tabela principal de itens BPO
CREATE TABLE TbBpoItens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    ano INT NOT NULL,
    codigo VARCHAR(50),
    nome VARCHAR(255) NOT NULL,
    nivel_hierarquia INT,
    linha_planilha INT,
    perc_viabilidade DECIMAL(10,2),
    valor_viabilidade DECIMAL(15,2),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    INDEX idx_empresa_ano (empresa_id, ano)
);

-- Tabela de dados mensais
CREATE TABLE TbBpoDadosMensais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_bpo_id INT NOT NULL,
    mes_numero INT NOT NULL,
    mes_nome VARCHAR(20),
    perc_realizado DECIMAL(10,2),
    valor_realizado DECIMAL(15,2),
    perc_atingido DECIMAL(10,2),
    valor_diferenca DECIMAL(15,2),
    FOREIGN KEY (item_bpo_id) REFERENCES TbBpoItens(id) ON DELETE CASCADE,
    INDEX idx_item_mes (item_bpo_id, mes_numero)
);

-- Tabela de resultados totais
CREATE TABLE TbBpoResultados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_bpo_id INT NOT NULL,
    previsao_total DECIMAL(15,2),
    total_realizado DECIMAL(15,2),
    diferenca_total DECIMAL(15,2),
    media_perc_realizado DECIMAL(10,2),
    media_valor_realizado DECIMAL(15,2),
    media_perc_diferenca DECIMAL(10,2),
    media_valor_diferenca DECIMAL(15,2),
    FOREIGN KEY (item_bpo_id) REFERENCES TbBpoItens(id) ON DELETE CASCADE
);

-- Tabela da seção RESULTADO POR FLUXO DE CAIXA
CREATE TABLE TbBpoResultadosFluxo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    ano INT NOT NULL,
    tipo ENUM('titulo', 'dados') NOT NULL,
    nome VARCHAR(255),
    linha_planilha INT,
    -- Mesmos campos de TbBpoResultados para linhas tipo 'dados'
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);
```

### 2. Implementar Salvamento no CompanyManager

No arquivo `src/models/company_manager.py`, adicione:

```python
def salvar_dados_bpo_empresa(self, empresa_id, ano, dados_bpo):
    """
    Salva dados processados de BPO no banco de dados

    Args:
        empresa_id: ID da empresa
        ano: Ano dos dados
        dados_bpo: Dicionário retornado por process_bpo_file()
    """
    try:
        # 1. Limpar dados antigos do mesmo ano
        self.excluir_dados_bpo_empresa(empresa_id, ano)

        # 2. Inserir itens hierárquicos
        for item in dados_bpo['itens_hierarquicos']:
            # INSERT em TbBpoItens
            # Pegar o ID gerado
            # INSERT em TbBpoDadosMensais (para cada mês)
            # INSERT em TbBpoResultados
            pass

        # 3. Inserir seção de resultados de fluxo
        for secao in dados_bpo['resultados_fluxo']['secoes']:
            # INSERT em TbBpoResultadosFluxo
            pass

        return True
    except Exception as e:
        print(f"Erro ao salvar dados BPO: {e}")
        return False
```

### 3. Descomentar Código nas Rotas

No arquivo `src/pages/admin/admin.py`, descomente as linhas comentadas nas rotas:
- `upload_dados_bpo()` (linhas 610-624)
- `consultar_dados_bpo()` (linhas 697-708)
- `deletar_dados_bpo_empresa()` (linhas 773-787)

---

## 📞 Suporte

Se encontrar erros ou comportamentos inesperados:

1. Verifique o arquivo `bpo_dados_processados.json` gerado
2. Observe os prints no terminal durante o processamento
3. Verifique se a planilha segue exatamente a estrutura esperada

---

**Criado em**: 2025-10-31
**Versão**: 1.0.0
