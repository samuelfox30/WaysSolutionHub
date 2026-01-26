import os
from dotenv import load_dotenv
from google import genai

# Carrega variáveis do .env
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')

client = genai.Client(api_key=GEMINI_API_KEY)

def gerar_analise(dados):
    prompt = f"""
    Você é um estrategista sênior de Tráfego Pago. Gere um relatório profissional com base nestes dados brutos:

    {dados}

    REGRAS DE FORMATAÇÃO (RIGOROSO):
    1. CABEÇALHO: Nome da empresa e período.
    2. RESUMO GERAL: Apresente os números principais de forma clara.
    3. AJUSTES E OTIMIZAÇÕES: Liste o que foi feito, mas principalmente explique o "PORQUÊ" e o impacto esperado. Use o contexto fornecido para justificar variações (como aumento de CPA).
    4. CONCLUSÃO: Veredito final e próximos passos.

    TOM DE VOZ:
    Profissional, direto e transparente. Não use floreios desnecessários.
    Se o CPA estiver acima da meta, aponte isso como ponto de atenção.
    """

    # Envia para o Google
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    return response.text

dados_do_sistema = {
    "empresa": "Sua Empresa Exemplo",
    "periodo": "20/01 a 26/01",
    "metricas": {
        "investimento": 1500.00,
        "cliques": 450,
        "impressoes": 12000,
        "cpa_atual": 3.33,
        "cpa_meta": 3.00
    },
    "acoes_feitas": [
        "Pausada palavra-chave 'grátis'",
        "Aumentado lance em mobile em 10%"
    ],
    "contexto_interno": "A concorrência aumentou no fim de semana."
}

resultado = gerar_analise(dados_do_sistema)

print(resultado)