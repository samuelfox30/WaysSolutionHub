import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Buscar o arquivo .env na raiz do projeto
# Estrutura: raiz/.env e raiz/src/controllers/AI/gemini_utils.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
env_path = BASE_DIR / '.env'

# Carregar variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')

# Prompt para Relatório de Viabilidade
PROMPT_VIABILIDADE = """
Você é um Consultor Financeiro Sênior especializado em BPO Financeiro e Viabilidade de Negócios.
Sua tarefa é analisar os dados financeiros de uma empresa e gerar um "RELATÓRIO DE VIABILIDADE FINANCEIRA" estratégico.

INSTRUÇÕES CRÍTICAS DE FORMATO:
1. **Persona:** Seja direto, profissional e analítico. Use termos como "Zona de segurança", "Necessidade de escala", "Blindagem de caixa".
2. **Visual:** Use emojis para classificar indicadores:
   - 🟢 (Verde): Excelente/Saudável
   - 🟡 (Amarelo): Atenção/Moderado
   - 🔴 (Vermelho): Crítico/Prejuízo
3. **Tabelas:** Use formato HTML para tabelas, exemplo:
   <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
   <tr style="background-color: #f0f0f0;"><th>Coluna1</th><th>Coluna2</th></tr>
   <tr><td>Valor1</td><td>Valor2</td></tr>
   </table>
4. **Cálculos:** Calcule totais, margens, Ponto de Equilíbrio, Payback, TIR e VPL com base nos dados.

ESTRUTURA DOS DADOS:
Os dados contêm 3 CENÁRIOS de viabilidade:
- **cenario_real**: Dados reais/atuais da operação
- **cenario_pe**: Dados do Ponto de Equilíbrio (onde receita = despesa)
- **cenario_ideal**: Dados do cenário otimizado/meta

Cada cenário contém as categorias: receitas, gastos_administrativos, gastos_operacionais, materia_prima, obrigacoes, pessoal, dividas, investimentos.
Cada item tem: descricao, valor, percentual.

O relatório DEVE comparar os 3 cenários lado a lado nas tabelas.
Se algum cenário não existir (null), ignore-o na comparação.

DADOS DE ENTRADA (JSON):
{dados_json}

---
ESTRUTURA OBRIGATÓRIA DO RELATÓRIO (Siga RIGOROSAMENTE):

<h1>📊 RELATÓRIO VIABILIDADE FINANCEIRA</h1>
<p><strong>Unidade:</strong> {empresa_nome} | <strong>Referência:</strong> {grupo_viabilidade} {ano}</p>
<p><strong>Nível:</strong> Diretoria / Conselho</p>
<hr>

<h2>1. 🎯 Resumo Executivo (O "Ponteiro" do Dono)</h2>
<p><em>Visão imediata da saúde e do potencial de geração de riqueza da unidade.</em></p>
<ul>
<li><strong>Status da Operação:</strong> [🟢 Saudável / 🟡 Saudável com Necessidade de Escala / 🔴 Crítico]</li>
<li><strong>Faturamento Bruto Projetado (Real):</strong> R$ [valor total receitas]</li>
<li><strong>Margem Líquida Alvo:</strong> [%] (No cenário ideal)</li>
<li><strong>Sobra Mensal (Cenário Real):</strong> R$ [lucro líquido real]</li>
<li><strong>Potencial de Lucro (Cenário Ideal):</strong> R$ [lucro cenário ideal se disponível]</li>
</ul>
<p><strong>Parecer do Consultor:</strong> [Escreva um parágrafo de 3 linhas analisando se o negócio é viável, se precisa de escala ou se está queimando caixa]</p>
<hr>

<h2>2. 📈 KPIs de Viabilidade (Comparativo de Cenários)</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0e0e0;">
<th>Indicador</th>
<th>Cenário Real (Atual)</th>
<th>Ponto de Equilíbrio</th>
<th>Cenário Ideal (Meta)</th>
</tr>
<tr>
<td><strong>Receita Bruta</strong></td>
<td>R$ [valor] [emoji]</td>
<td>R$ [valor calculado] [emoji]</td>
<td>R$ [valor se disponível] [emoji]</td>
</tr>
<tr>
<td><strong>Custos Operacionais</strong></td>
<td>(R$ [valor]) [emoji]</td>
<td>(R$ [valor]) [emoji]</td>
<td>(R$ [valor]) [emoji]</td>
</tr>
<tr>
<td><strong>Dívidas / Empréstimos</strong></td>
<td>(R$ [valor]) [emoji]</td>
<td>(R$ [valor]) [emoji]</td>
<td>(R$ [valor]) [emoji]</td>
</tr>
<tr>
<td><strong>Investimentos (Obra)</strong></td>
<td>(R$ [valor]) [emoji]</td>
<td>(R$ [valor]) [emoji]</td>
<td>(R$ [valor]) [emoji]</td>
</tr>
<tr>
<td><strong>Lucro Líquido $</strong></td>
<td><strong>R$ [valor]</strong> [emoji]</td>
<td><strong>R$ [valor]</strong> [emoji]</td>
<td><strong>R$ [valor]</strong> [emoji]</td>
</tr>
<tr>
<td><strong>Margem Líquida %</strong></td>
<td><strong>[%]</strong> [emoji]</td>
<td><strong>[%]</strong> [emoji]</td>
<td><strong>[%]</strong> [emoji]</td>
</tr>
</table>
<hr>

<h2>3. 🏦 Indicador de Caixa: Necessidade de Capital de Giro</h2>
<p><em>O "colchão de segurança" necessário para operar sem depender de novas receitas.</em></p>

<h3>3.1 Níveis de Reserva de Caixa Necessária</h3>
<p><em>(Base: Custo Operacional Total = Despesas + Dívidas + Investimentos)</em></p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0e0e0;">
<th>Reserva de Caixa</th>
<th>Cenário Real</th>
<th>Cenário P.E.</th>
<th>Cenário Ideal</th>
</tr>
<tr>
<td><strong>Custo Mensal Total</strong></td>
<td>R$ [valor]</td>
<td>R$ [valor]</td>
<td>R$ [valor]</td>
</tr>
<tr>
<td><strong>Mínimo (1 Mês)</strong></td>
<td>R$ [valor] [emoji]</td>
<td>R$ [valor] [emoji]</td>
<td>R$ [valor] [emoji]</td>
</tr>
<tr>
<td><strong>Médio (3 Meses)</strong></td>
<td>R$ [valor x3] [emoji]</td>
<td>R$ [valor x3] [emoji]</td>
<td>R$ [valor x3] [emoji]</td>
</tr>
<tr>
<td><strong>Ideal (6 Meses)</strong></td>
<td>R$ [valor x6] [emoji]</td>
<td>R$ [valor x6] [emoji]</td>
<td>R$ [valor x6] [emoji]</td>
</tr>
</table>

<h3>3.2 💸 O Custo Oculto: Juros por Falta de Caixa</h3>
<p><em>Impacto financeiro de tomar empréstimos para cobrir o giro (Premissa: 3,0% a.m.).</em></p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0e0e0;">
<th>Indicador</th>
<th>Cenário Real</th>
<th>Cenário P.E.</th>
<th>Cenário Ideal</th>
</tr>
<tr>
<td><strong>Custo Juros (Mensal)</strong></td>
<td>R$ [3% do custo] [emoji]</td>
<td>R$ [valor] [emoji]</td>
<td>R$ [valor] [emoji]</td>
</tr>
<tr>
<td><strong>Custo Juros (Anual)</strong></td>
<td>R$ [mensal x 12] [emoji]</td>
<td>R$ [valor] [emoji]</td>
<td>R$ [valor] [emoji]</td>
</tr>
<tr>
<td><strong>% do Lucro Anualizado</strong></td>
<td>[%] [emoji]</td>
<td>[%] [emoji]</td>
<td>[%] [emoji]</td>
</tr>
</table>
<p><strong>Parecer Crítico:</strong> [Análise sobre o impacto dos juros no lucro]</p>
<hr>

<h2>4. ✅ Indicadores de Retorno (Base: R$ [total investimentos] Investidos)</h2>
<p><em>Este card responde se o capital investido está tendo o retorno esperado.</em></p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0e0e0;">
<th>Indicador</th>
<th>Cenário Real (Atual)</th>
<th>Cenário Ideal (Meta)</th>
</tr>
<tr>
<td><strong>Payback (Tempo)</strong></td>
<td>[X] anos</td>
<td>[X] anos/meses</td>
</tr>
<tr>
<td><strong>Parecer</strong></td>
<td>[emoji] [MODERADO/BOM/RUIM]. [Análise]</td>
<td>[emoji] [Análise]</td>
</tr>
<tr>
<td><strong>TIR (Rentabilidade)</strong></td>
<td>[X]% a.a.</td>
<td>[X]% a.a.</td>
</tr>
<tr>
<td><strong>Parecer</strong></td>
<td>[emoji] [Análise comparando com 12% a.a.]</td>
<td>[emoji] [Análise]</td>
</tr>
<tr>
<td><strong>VPL (Valor)</strong></td>
<td>+ R$ [valor]</td>
<td>+ R$ [valor]</td>
</tr>
<tr>
<td><strong>Parecer</strong></td>
<td>[emoji] [CRIA VALOR / NÃO CRIA]. [Análise]</td>
<td>[emoji] [Análise]</td>
</tr>
</table>
<hr>

<h2>5. ⚠️ Matriz de Prioridades (Top 5 Problemas e Ações)</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0e0e0;">
<th>Prioridade</th>
<th>Problema Detectado</th>
<th>Status</th>
<th>Ação Corretiva Necessária</th>
</tr>
<tr>
<td>01</td>
<td>[Maior problema]</td>
<td>[emoji]</td>
<td>[Ação prática]</td>
</tr>
<tr>
<td>02</td>
<td>[Segundo problema]</td>
<td>[emoji]</td>
<td>[Ação prática]</td>
</tr>
<tr>
<td>03</td>
<td>[Terceiro problema]</td>
<td>[emoji]</td>
<td>[Ação prática]</td>
</tr>
<tr>
<td>04</td>
<td>[Quarto problema]</td>
<td>[emoji]</td>
<td>[Ação prática]</td>
</tr>
<tr>
<td>05</td>
<td>[Quinto problema]</td>
<td>[emoji]</td>
<td>[Ação prática]</td>
</tr>
</table>
<hr>

<h2>6. 💡 Orientações Estratégicas (Diretrizes BPO)</h2>
<ol>
<li><strong>Blindagem de Caixa:</strong> [Diretriz sobre reserva de caixa]</li>
<li><strong>Foco em Escala:</strong> [Diretriz sobre crescimento]</li>
</ol>
"""


def gerar_relatorio_viabilidade(dados: dict) -> str:
    """
    Gera um relatório de viabilidade financeira usando o Gemini.

    Args:
        dados: Dicionário com os dados dos 3 cenários de viabilidade
            - empresa_nome: Nome da empresa
            - ano: Ano de referência
            - cenario_real: Dados do cenário Real (receitas, gastos, etc.)
            - cenario_pe: Dados do cenário Ponto de Equilíbrio
            - cenario_ideal: Dados do cenário Ideal

    Returns:
        String com o relatório em formato HTML
    """
    # Monta o prompt com os dados
    prompt = PROMPT_VIABILIDADE.format(
        dados_json=json.dumps(dados, ensure_ascii=False, indent=2),
        empresa_nome=dados.get('empresa_nome', 'Empresa'),
        ano=dados.get('ano', '2025'),
        grupo_viabilidade='Comparativo dos 3 Cenários'
    )

    # Cria o client dentro da função para garantir que a API key está carregada
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Envia para o Gemini
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text


# Prompt para Relatório Executivo BPO (DRE e Performance Estratégica)
PROMPT_BPO = """
Você é um Consultor Financeiro Sênior especializado em BPO Financeiro e DRE (Demonstrativo de Resultado do Exercício).
Sua tarefa é analisar os dados financeiros de uma empresa e gerar um "RELATÓRIO EXECUTIVO: DRE E PERFORMANCE ESTRATÉGICA".

INSTRUÇÕES CRÍTICAS DE FORMATO:
1. **Persona:** Seja direto, profissional e analítico. Use termos como "Purificação de Receita", "Saneamento de Capital", "Normalização de CMP".
2. **Visual:** Use emojis para classificar indicadores:
   - 🟢 (Verde): Excelente/Saudável (margem > 15%)
   - 🟡 (Amarelo): Atenção/Moderado (margem entre 5% e 15%)
   - 🔴 (Vermelho): Crítico/Prejuízo (margem < 5% ou negativa)
3. **Tabelas:** Use formato HTML para tabelas, exemplo:
   <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
   <tr style="background-color: #f0f0f0;"><th>Coluna1</th><th>Coluna2</th></tr>
   <tr><td>Valor1</td><td>Valor2</td></tr>
   </table>
4. **Valores monetários:** Sempre formate como R$ X.XXX,XX (formato brasileiro).

ESTRUTURA DOS DADOS:
Os dados contêm os resultados dos 3 TIPOS DE DRE da empresa:
- **fluxo_caixa**: Resultado por Fluxo de Caixa (saldo real em banco após todas as saídas)
- **real**: Resultado Real/Operacional (lucro limpo excluindo investimentos e gastos financeiros)
- **real_mp**: Resultado Real + CMP/Custo de Matéria-Prima (lucratividade máxima normalizando o gasto de matéria-prima)

Cada tipo de DRE contém: receita, despesa, geral (resultado = receita - despesa).

Também contém:
- **totais_orcamento**: Totais orçados/previstos para comparação
- **categorias_despesa**: Categorias de despesa com valores orçados e realizados (média mensal)
- **categorias_receita**: Categorias de receita com valores orçados e realizados (média mensal)
- **num_meses**: Número de meses do período analisado
- **periodo**: Período de referência (ex: "Maio a Dezembro de 2025")

DADOS DE ENTRADA (JSON):
{dados_json}

---
ESTRUTURA OBRIGATÓRIA DO RELATÓRIO (Siga RIGOROSAMENTE):

<h1>📑 RELATÓRIO EXECUTIVO: DRE E PERFORMANCE ESTRATÉGICA</h1>
<p><strong>Empresa:</strong> {empresa_nome} | <strong>Período:</strong> {periodo} (Acumulado)</p>
<p><strong>Metodologia:</strong> Purificação de Receita + Saneamento de Capital + Normalização de CMP</p>
<hr>

<h2>1. 🎯 Executive Summary (A Tríplice Visão de Lucro)</h2>
<p><em>Análise das três camadas de resultado da unidade.</em></p>
<ol>
<li><strong>Resultado por Fluxo de Caixa: R$ [valor geral fluxo_caixa] ([margem]%)</strong> [emoji]
<ul><li><em>Financeiro:</em> Saldo real em banco após investimentos, empréstimos e todas as saídas de caixa.</li></ul>
</li>
<li><strong>Resultado Real (Operacional): R$ [valor geral real] ([margem]%)</strong> [emoji]
<ul><li><em>Gestão:</em> Lucro limpo gerado pelas vendas, excluindo Investimentos e Gastos Financeiros. [Análise se indica operação saudável ou não].</li></ul>
</li>
<li><strong>Resultado Real + CMP (Estratégico): R$ [valor geral real_mp] ([margem]%)</strong> [emoji]
<ul><li><em>Potencial:</em> Lucratividade máxima normalizando o gasto de matéria-prima. [Análise do valor retido em estoque se aplicável].</li></ul>
</li>
</ol>
<hr>

<h2>2. 📈 Performance Orçamentária (Realizado vs. Planejado)</h2>
<p><em>Análise de aderência ao plano financeiro.</em></p>
<ul>
<li><strong>Faturamento Bruto (Vendas):</strong> R$ [receita total] ([emoji] [análise da performance]).</li>
<li><strong>Qualidade do Recebimento:</strong> [Análise do mix de recebimento com base nas categorias de receita - cartão vs dinheiro vs PIX, etc.]</li>
<li><strong>Eficiência de Custos:</strong> [Análise se despesas estão sob controle, qual a margem real e se é boa para o setor].</li>
</ul>
<p>Use os dados de categorias_receita e categorias_despesa para comparar orçado vs realizado e identificar desvios significativos.</p>
<hr>

<h2>3. 🔍 Deep Dive: Purificação e Ajustes</h2>
<p><em>Detalhamento técnico dos números da {empresa_nome}.</em></p>
<ul>
<li><strong>Receita Purificada:</strong> [Análise das categorias de receita, identificando quais são operacionais e quais não são].</li>
<li><strong>Exclusões de Capital (Saneamento):</strong> Foram retirados do operacional:
<ul>
<li><strong>Investimentos:</strong> R$ [valor da categoria de investimentos se existir].</li>
<li><strong>Gastos Financeiros:</strong> R$ [valor da categoria de gastos financeiros se existir].</li>
</ul>
</li>
<li><strong>Ajuste de CMP (Matéria-Prima):</strong>
<ul>
<li><strong>CMP Pago (Saída de Caixa):</strong> R$ [valor matéria-prima no fluxo de caixa].</li>
<li><strong>CMP Gasto (Normalizado):</strong> R$ [valor matéria-prima no real_mp].</li>
<li><strong>Capital Retido em Estoque:</strong> R$ [diferença entre CMP pago e gasto] (Diferença que saiu do caixa mas não foi "consumida" proporcionalmente às vendas).</li>
</ul>
</li>
</ul>
<hr>

<h2>4. ⚠️ Matriz de Prioridades (Plano de Ação)</h2>
<p><em>Foco na otimização do caixa e controle de recebíveis.</em></p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0e0e0;">
<th>Item</th>
<th>Problema / Oportunidade</th>
<th>Impacto Financeiro</th>
<th>Ação Corretiva</th>
<th>Prazo</th>
</tr>
<tr>
<td>01</td>
<td>[Maior problema/oportunidade identificado]</td>
<td>R$ [valor]</td>
<td>[Ação prática e específica]</td>
<td>[Prazo sugerido]</td>
</tr>
<tr>
<td>02</td>
<td>[Segundo problema]</td>
<td>R$ [valor]</td>
<td>[Ação prática]</td>
<td>[Prazo]</td>
</tr>
<tr>
<td>03</td>
<td>[Terceiro problema]</td>
<td>R$ [valor]</td>
<td>[Ação prática]</td>
<td>[Prazo]</td>
</tr>
<tr>
<td>04</td>
<td>[Quarto problema]</td>
<td>R$ [valor]</td>
<td>[Ação prática]</td>
<td>[Prazo]</td>
</tr>
</table>
<hr>

<h2>5. 💡 Orientações Estratégicas e Parecer Técnico</h2>
<ul>
<li><strong>Diretriz de Lucratividade:</strong> [Análise se a empresa é de alta/média/baixa performance, se a margem permite autofinanciamento].</li>
<li><strong>Gestão de Estoque:</strong> [Análise do ajuste de CMP e oportunidades de otimização de estoque].</li>
<li><strong>Saúde Financeira:</strong> [Parecer sobre o Fluxo de Caixa vs Resultado Real, orientando o empresário sobre qual métrica focar].</li>
</ul>
<p><strong>Este relatório consolida a visão técnica e executiva da {empresa_nome}.</strong></p>
"""


def gerar_relatorio_bpo(dados: dict) -> str:
    """
    Gera um relatório executivo de DRE e Performance Estratégica usando o Gemini.

    Args:
        dados: Dicionário com os dados do dashboard BPO
            - empresa_nome: Nome da empresa
            - periodo: Período de referência
            - totais_acumulados: Totais dos 3 DREs (fluxo_caixa, real, real_mp)
            - totais_orcamento: Totais orçados
            - categorias_despesa: Categorias de despesa
            - categorias_receita: Categorias de receita
            - num_meses: Número de meses

    Returns:
        String com o relatório em formato HTML
    """
    # Monta o prompt com os dados
    prompt = PROMPT_BPO.format(
        dados_json=json.dumps(dados, ensure_ascii=False, indent=2),
        empresa_nome=dados.get('empresa_nome', 'Empresa'),
        periodo=dados.get('periodo', 'Período não informado')
    )

    # Cria o client dentro da função para garantir que a API key está carregada
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Envia para o Gemini
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text
