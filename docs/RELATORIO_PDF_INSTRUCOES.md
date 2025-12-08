# Instruções: Relatório PDF de Viabilidade

## 📋 Visão Geral

O sistema agora permite gerar relatórios PDF personalizados de viabilidade financeira com cálculos automáticos de indicadores como VPL, TIR, Payback, entre outros.

---

## 🛠️ Configuração Inicial

### 1. Criar a Tabela no Banco de Dados

Execute o SQL em `/database/create_relatorio_template_table.sql`:

```sql
CREATE TABLE IF NOT EXISTS TbRelatorioTemplate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    ano INT NOT NULL,
    template_texto TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    UNIQUE KEY unique_empresa_ano (empresa_id, ano)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 2. Instalar Bibliotecas Python Necessárias

```bash
pip install weasyprint numpy-financial
```

**Obs:** WeasyPrint requer dependências do sistema:
- **Ubuntu/Debian:** `sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`
- **macOS:** `brew install cairo pango gdk-pixbuf libffi`
- **Windows:** Instale o GTK+ Runtime

---

## 📝 Como Preparar o Relatório no Excel

### Passo 1: Criar a Aba "Relatório"

No arquivo Excel de viabilidade, crie uma nova aba chamada **"Relatório"** (com acento).

### Passo 2: Colar o Texto do Relatório na Célula A1

Cole todo o texto do relatório na célula **A1**. Exemplo:

```
Diagnóstico Executivo (Visão Geral)

A análise compara três cenários operacionais (Real, Ponto de Equilíbrio e Ideal) para avaliar a saúde financeira e o retorno sobre o capital já investido, estimado em {{capital_investido}}.

O Cenário Real ({{receita_real}} de receita) opera em um estado de alto risco. O faturamento está perigosamente próximo ao Ponto de Equilíbrio ({{ponto_equilibrio}}), e o lucro líquido de {{lucro_real}} é insuficiente para remunerar o capital investido.

O ponto mais crítico é o Custo da Falta de Capital de Giro: a análise demonstra que a necessidade de financiar a operação mínima ({{despesas_pe}}) gera um custo financeiro (juros) de {{custo_juros_mensal_pe}} por mês.

A migração para o Cenário Ideal ({{receita_ideal}} de receita) é a única solução estratégica, transformando o negócio em uma operação altamente lucrativa (TIR de {{tir_ideal}}) e criando valor real (VPL de {{vpl_ideal}}).
```

### Passo 3: Substituir Valores por Variáveis

Substitua os valores reais do seu relatório pelas variáveis listadas abaixo. Use o formato `{{nome_variavel}}`.

---

## 🔢 Variáveis Disponíveis

### Informações Básicas
- `{{empresa_nome}}` - Nome da empresa
- `{{ano}}` - Ano do relatório
- `{{grupo_viabilidade}}` - Nome do grupo selecionado (Real, PE, Ideal)
- `{{capital_investido}}` - Capital total investido (formatado em R$)

### Cenário Real
- `{{receita_real}}` - Receita mensal
- `{{despesas_real}}` - Despesas totais (despesas + dívidas + investimentos)
- `{{lucro_real}}` - Lucro líquido mensal
- `{{margem_real}}` - Margem líquida (%)
- `{{lucro_anual_real}}` - Lucro anualizado (lucro * 12)

### Cenário Ponto de Equilíbrio (PE)
- `{{receita_pe}}` - Receita mensal
- `{{despesas_pe}}` - Despesas totais
- `{{lucro_pe}}` - Lucro líquido mensal
- `{{margem_pe}}` - Margem líquida (%)
- `{{lucro_anual_pe}}` - Lucro anualizado

### Cenário Ideal
- `{{receita_ideal}}` - Receita mensal
- `{{despesas_ideal}}` - Despesas totais
- `{{lucro_ideal}}` - Lucro líquido mensal
- `{{margem_ideal}}` - Margem líquida (%)
- `{{lucro_anual_ideal}}` - Lucro anualizado

### Indicadores de Risco
- `{{ponto_equilibrio}}` - Faturamento mínimo necessário
- `{{margem_seguranca}}` - Diferença entre receita real e ponto de equilíbrio

### Capital de Giro (por cenário: real, pe, ideal)
- `{{reserva_1mes_real}}` - Reserva para 1 mês
- `{{reserva_3meses_real}}` - Reserva para 3 meses
- `{{reserva_6meses_real}}` - Reserva para 6 meses
- `{{custo_juros_mensal_real}}` - Custo mensal de juros (3% sobre reserva mínima)
- `{{custo_juros_anual_real}}` - Custo anual de juros
- `{{perc_juros_lucro_real}}` - % do lucro consumido por juros

### Indicadores de Retorno
- `{{vpl_real}}` / `{{vpl_ideal}}` - Valor Presente Líquido
- `{{tir_real}}` / `{{tir_ideal}}` - Taxa Interna de Retorno (%)
- `{{payback_real}}` / `{{payback_ideal}}` - Tempo de retorno do investimento

### Variáveis Auxiliares (Textos Dinâmicos)
- `{{status_viabilidade_real}}` - Texto automático sobre status (ex: "inviável financeiramente")
- `{{status_viabilidade_ideal}}` - Texto automático sobre status
- `{{conclusao}}` - Conclusão automática baseada na margem de segurança

---

## 🚀 Como Usar

### 1. Fazer Upload do Excel

1. Acesse **Admin → Gerenciar Empresas**
2. Clique em **Upload de Dados** para a empresa desejada
3. Selecione o ano
4. Faça upload do arquivo Excel que contém a aba "Relatório"
5. O sistema lerá automaticamente a aba e salvará o template

### 2. Gerar o PDF

1. Acesse o **Dashboard de Viabilidade** da empresa
2. Selecione o **ano**
3. Selecione o **grupo de viabilidade** (Real, PE ou Ideal)
4. Clique no botão **"Baixar Relatório PDF"** que aparecerá
5. O PDF será gerado e baixado automaticamente

---

## 📊 Exemplo de Template Completo

Veja o arquivo de exemplo que você forneceu, mas com as variáveis substituídas:

```
Diagnóstico Executivo (Visão Geral)

A análise compara três cenários operacionais (Real, Ponto de Equilíbrio e Ideal) para avaliar a saúde financeira e o retorno sobre o capital já investido, estimado em {{capital_investido}}.

O Cenário Real ({{receita_real}} de receita) opera em um estado de alto risco. O faturamento está perigosamente próximo ao Ponto de Equilíbrio ({{ponto_equilibrio}}), e o lucro líquido de {{lucro_real}} é insuficiente para remunerar o capital investido.

O ponto mais crítico é o Custo da Falta de Capital de Giro: a análise (item 3.1) demonstra que a necessidade de financiar a operação mínima ({{despesas_pe}}) gera um custo financeiro (juros) de {{custo_juros_mensal_pe}} por mês. Este custo consome {{custo_juros_anual_pe}} por ano, o que representa {{perc_juros_lucro_pe}} do lucro anualizado. A empresa está, literalmente, trabalhando para pagar juros.

A migração para o Cenário Ideal ({{receita_ideal}} de receita) é a única solução estratégica, transformando o negócio em uma operação altamente lucrativa (TIR de {{tir_ideal}}) e criando valor real (VPL de {{vpl_ideal}}).

KPIs: Comparativo de Cenários

| Indicador | Cenário Real | Cenário PE | Cenário Ideal |
|-----------|--------------|------------|---------------|
| Receita Total | {{receita_real}} | {{receita_pe}} | {{receita_ideal}} |
| Despesas + Dívidas | {{despesas_real}} | {{despesas_pe}} | {{despesas_ideal}} |
| Lucro Líquido (Mês) | {{lucro_real}} | {{lucro_pe}} | {{lucro_ideal}} |
| Margem Líquida | {{margem_real}} | {{margem_pe}} | {{margem_ideal}} |
| Lucro Anualizado | {{lucro_anual_real}} | {{lucro_anual_pe}} | {{lucro_anual_ideal}} |

⚠️ Indicador de Risco: Ponto de Equilíbrio (Break-Even)

Ponto de Equilíbrio: {{ponto_equilibrio}}
Faturamento Real: {{receita_real}}
Margem de Segurança: {{margem_seguranca}}

Parecer: Atenção. A empresa opera com uma margem de segurança baixíssima.

✅ Indicadores de Retorno

| Indicador | Cenário Real | Cenário Ideal |
|-----------|--------------|---------------|
| Payback | {{payback_real}} | {{payback_ideal}} |
| TIR | {{tir_real}} | {{tir_ideal}} |
| VPL | {{vpl_real}} | {{vpl_ideal}} |

💡 Conclusão e Recomendação Estratégica

Diagnóstico: A operação no Cenário Real é {{status_viabilidade_real}}. A empresa apresenta {{conclusao}}.

Meta Absoluta: Atingir o Cenário Ideal (Receita de {{receita_ideal}}) é a única forma de reverter este quadro.
```

---

## 🔧 Solução de Problemas

### Erro: "Template de relatório não encontrado"
- Certifique-se que a aba "Relatório" existe no Excel
- Verifique se a célula A1 não está vazia
- Faça novo upload do arquivo

### Erro: "WeasyPrint not found"
- Instale: `pip install weasyprint`
- Instale as dependências do sistema (Cairo, Pango, etc.)

### PDF com valores "N/A"
- Verifique se todos os dados de viabilidade foram carregados corretamente
- Confirme que o ano selecionado tem dados no banco

### Variáveis não substituídas (aparecem como {{variavel}})
- Verifique se escreveu o nome da variável corretamente
- Use exatamente o formato `{{nome_variavel}}` (com duas chaves)
- Consulte a lista de variáveis disponíveis acima

---

## 📦 Bibliotecas Novas Necessárias

Adicione ao `requirements.txt`:

```
weasyprint==60.2
numpy-financial==1.0.0
```

E instale:

```bash
pip install -r requirements.txt
```

---

## 💡 Dicas

1. **Formatação**: O PDF suporta quebras de linha. Use Alt+Enter no Excel para adicionar linhas dentro da célula A1.

2. **Tabelas**: Você pode usar Markdown para criar tabelas no template. O sistema converte automaticamente.

3. **Vários Templates**: Cada empresa pode ter um template diferente por ano. Isso permite personalizar relatórios conforme necessário.

4. **Segurança**: Usuários comuns só podem baixar relatórios da própria empresa. Administradores podem baixar de qualquer empresa.

5. **Atualização Dinâmica**: Se você atualizar os dados da empresa (fazer novo upload do Excel de viabilidade), o PDF será gerado com os novos valores automaticamente, sem precisar atualizar o template.

---

## 📞 Suporte

Se tiver dúvidas ou problemas, consulte os logs do servidor para mais detalhes sobre erros.
