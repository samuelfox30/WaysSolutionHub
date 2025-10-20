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

    blocos = {}

    # Detectar blocos
    for row in range(1, ws.max_row + 1):
        valor = ws[f"A{row}"].value
        if valor in subgrupos and is_merged(ws[f"A{row}"]):
            inicio = row + 1
            fim = inicio
            while fim <= ws.max_row and not is_blank_row(fim):
                fim += 1
            blocos[valor] = (inicio, fim - 1)

    # Agora extrair os dados em dicionários
    dados = {}
    for nome, (ini, fim) in blocos.items():
        lista_itens = []
        for r in range(ini + 1, fim + 1):  # começa 1 linha abaixo do início
            desc = ws[f"A{r}"].value
            perc = ws[f"B{r}"].value
            valr = ws[f"C{r}"].value
            if desc not in (None, "", " "):  # ignora linhas vazias
                item = {
                    "subgrupo": nome,
                    "descricao": str(desc).strip(),
                    "percentual": perc,
                    "valor": valr
                }
                lista_itens.append(item)
        dados[nome] = lista_itens

    # Printar para conferência
    for sub, itens in dados.items():
        print(f"\n--- {sub} ---")
        for i in itens:
            print(i)

    return dados