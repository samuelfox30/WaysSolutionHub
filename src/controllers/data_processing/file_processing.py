from openpyxl import load_workbook

def process_uploaded_file(file):
    print("\n\nINICIANDO ANÁLISE DO ARQUIVO UPLOAD... \n\n")

    wb = load_workbook(file, data_only=True)
    ws = wb.active

    def is_merged(cell):
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                return True
        return False

    def is_blank_row(row_number):
        for cell in ws[row_number]:
            if cell.value not in (None, "", " "):
                return False
        return True

    def normalizar_percentual(valor):
        """
        Normaliza valores de porcentagem para o formato correto.
        Se o valor absoluto for < 1, assume que está em formato decimal (ex: 0.8 = 80%)
        e mantém como está. Se for muito pequeno (< 0.01), multiplica por 100.
        """
        if valor is None or valor == 0:
            return valor
        
        # Se o valor absoluto for muito pequeno (< 0.01), provavelmente
        # não está no formato de porcentagem do Excel, então multiplica por 100
        if abs(valor) < 0.01:
            return valor * 100
        
        # Caso contrário, mantém o valor original (já está correto)
        return valor

    subgrupos = [
        "RECEITA",
        "CONTROLE DESPESAS POR NATURESAS SINTETICAS",
        "OBRIGAÇÕES",
        "GASTOS ADM",
        "MATERIA PRIMA",
        "GASTOS OPERACIONAIS",
        "PESSOAL"
    ]

    # Colunas de cada cenário
    cenarios = [
        {"nome": ws["A1"].value, "cols": ("A", "B", "C")},
        {"nome": ws["E1"].value, "cols": ("E", "F", "G")},
        {"nome": ws["I1"].value, "cols": ("I", "J", "K")},
    ]

    # Detectar blocos nomeados (usando col A)
    blocos = {}
    for row in range(1, ws.max_row + 1):
        valor = ws[f"A{row}"].value
        if valor in subgrupos and is_merged(ws[f"A{row}"]):
            inicio = row + 1
            fim = inicio
            while fim <= ws.max_row and not is_blank_row(fim):
                fim += 1
            blocos[valor] = (inicio, fim - 1)

    # Adicionar o bloco GERAL antes do primeiro subgrupo
    if blocos:
        primeiro_inicio = min(v[0] for v in blocos.values())
        blocos = {"GERAL": (3, primeiro_inicio - 2), **blocos}

    # Palavras-chave a ignorar
    ignorar_descricoes = {
        "RESULTADO REAL",
        "RESULTADO IDEAL",
        "PONTO DE EQUILIBRIO",
        "0"
    }

    # Extrair dados para cada cenário (os blocos normais)
    lista_cenarios = []
    for cenario in cenarios:
        nome_cenario = cenario["nome"]
        col_desc, col_perc, col_val = cenario["cols"]

        dados = {}
        for nome, (ini, fim) in blocos.items():
            lista_itens = []
            for r in range(ini, fim + 1):
                desc = ws[f"{col_desc}{r}"].value
                perc = ws[f"{col_perc}{r}"].value
                valr = ws[f"{col_val}{r}"].value

                if desc is None:
                    continue

                desc_str = str(desc).strip().upper()
                if desc_str in ignorar_descricoes:
                    continue

                # Normalizar o percentual
                perc_normalizado = normalizar_percentual(perc)

                item = {
                    "cenario": nome_cenario,
                    "subgrupo": nome,
                    "descricao": str(desc).strip(),
                    "percentual": perc_normalizado,
                    "valor": valr
                }
                lista_itens.append(item)
            dados[nome] = lista_itens

        lista_cenarios.append(dados)

    # ============================
    # Captura dos SUBGRUPOS ESPECIAIS
    # ============================

    especiais = {}

    # Procurar onde começa cada um
    especiais_nomes = [
        "DIVIDAS",
        "INVESTIMENTOS",
        "INVESTIMENTOS GERAL NO NEGOCIO",
        "GASTOS OPERACIONAIS"
    ]

    for row in range(1, ws.max_row + 1):
        valor = ws[f"A{row}"].value
        if valor in especiais_nomes:
            inicio = row + 2  # pula uma linha após o título
            fim = inicio
            while fim <= ws.max_row and not is_blank_row(fim):
                fim += 1
            especiais[valor] = (inicio, fim - 1)

    # Extrair dados dos especiais
    dados_especiais = {}
    for nome, (ini, fim) in especiais.items():
        lista_itens = []
        for r in range(ini, fim + 1):
            desc = ws[f"A{r}"].value
            if desc is None:
                continue

            desc_str = str(desc).strip()
            if desc_str == "" or desc_str == "0":
                continue

            if nome in ("DIVIDAS", "INVESTIMENTOS"):
                parc = ws[f"B{r}"].value
                juros = ws[f"E{r}"].value
                total = ws[f"F{r}"].value

                # Ignorar se todos os valores forem 0 ou None
                if all(v in (None, 0, 0.0) for v in (parc, juros, total)):
                    continue

                item = {
                    "subgrupo": nome,
                    "descricao": desc_str,
                    "valor_parc": parc,
                    "valor_juros": juros,
                    "valor_total_parcela": total
                }

            elif nome == "INVESTIMENTOS GERAL NO NEGOCIO":
                val = ws[f"B{r}"].value
                if val in (None, 0, 0.0):
                    continue
                item = {
                    "subgrupo": nome,
                    "descricao": desc_str,
                    "valor": val
                }

            elif nome == "GASTOS OPERACIONAIS":
                custo_km = ws[f"B{r}"].value
                custo_mensal = ws[f"C{r}"].value

                # Ignorar se ambos forem 0 ou None
                if all(v in (None, 0, 0.0) for v in (custo_km, custo_mensal)):
                    continue

                item = {
                    "subgrupo": nome,
                    "descricao": desc_str,
                    "custo_km": custo_km,
                    "custo_mensal": custo_mensal
                }

            lista_itens.append(item)
        dados_especiais[nome] = lista_itens

    # ============================
    # PRINTS PARA CONFERÊNCIA
    # ============================

    for dic in lista_cenarios:
        print("\n============================")
        print(f"CENÁRIO: {list(dic.values())[0][0]['cenario'] if list(dic.values())[0] else 'SEM NOME'}")
        for sub, itens in dic.items():
            print(f"\n--- {sub} ---")
            for i in itens:
                print(i)

    print("\n============================")
    print("SUBGRUPOS ESPECIAIS (únicos, replicar depois para os 3 cenários):")
    for sub, itens in dados_especiais.items():
        print(f"\n--- {sub} ---")
        for i in itens:
            print(i)

    return lista_cenarios, dados_especiais