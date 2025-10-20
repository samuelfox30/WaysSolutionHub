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

    # Extrair dados para cada cenário
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
                if desc not in (None, "", " ", "RESULTADO REAL"):
                    item = {
                        "cenario": nome_cenario,
                        "subgrupo": nome,
                        "descricao": str(desc).strip(),
                        "percentual": perc,
                        "valor": valr
                    }
                    lista_itens.append(item)
            dados[nome] = lista_itens

        lista_cenarios.append(dados)

    # Printar para conferência
    for dic in lista_cenarios:
        print("\n============================")
        print(f"CENÁRIO: {list(dic.values())[0][0]['cenario'] if list(dic.values())[0] else 'SEM NOME'}")
        for sub, itens in dic.items():
            print(f"\n--- {sub} ---")
            for i in itens:
                print(i)

    return lista_cenarios