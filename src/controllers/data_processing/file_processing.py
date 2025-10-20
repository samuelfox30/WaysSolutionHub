from openpyxl import load_workbook

def process_uploaded_file(file):
    print("\n\nINICIANDO ANÁLISE DO ARQUIVO UPLOAD... \n\n")

    # Carregar o arquivo Excel
    wb = load_workbook(file, data_only=True)
    ws = wb.active  # ou ws["NomeDaAba"]

    # Função auxiliar para checar se uma célula está mesclada
    def is_merged(cell):
        for merged_range in ws.merged_cells.ranges:
            if cell.coordinate in merged_range:
                return True
        return False

    # Função auxiliar para checar se uma linha está totalmente em branco
    def is_blank_row(row_number):
        for cell in ws[row_number]:
            if cell.value not in (None, "", " "):
                return False
        return True

    # Subgrupos que você quer rastrear (na ordem correta)
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

    # Percorrer todas as linhas da coluna A
    for row in range(1, ws.max_row + 1):
        valor = ws[f"A{row}"].value
        if valor in subgrupos and is_merged(ws[f"A{row}"]):
            inicio = row + 1  # dados começam logo abaixo do título
            fim = inicio

            # Avança até achar uma linha em branco
            while fim <= ws.max_row and not is_blank_row(fim):
                fim += 1

            blocos[valor] = (inicio, fim - 1)

    # Log amigável
    print("Blocos detectados (linhas do Excel):")
    for k, (ini, fim) in blocos.items():
        print(f"- {k}: linhas {ini} até {fim}")

    return blocos