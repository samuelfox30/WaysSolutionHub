from models.auth import DatabaseConnection
import mysql.connector

class CompanyManager(DatabaseConnection):

    def salvar_itens_empresa(self, empresa_selecionada, mes_selecionado, ano_selecionado, lista_cenarios, dados_especiais):
        try:
            # 1. Buscar o ID do usuário pela empresa
            self.cursor.execute("SELECT id FROM users WHERE empresa = %s", (empresa_selecionada,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa '{empresa_selecionada}' não encontrada na tabela users.")
            usuario_id = row[0]

            # ============================
            # 2. Limpar dados existentes (para evitar duplicação)
            # ============================
            tabelas = [
                "TbItens",
                "TbItensDividas",
                "TbItensInvestimentos",
                "TbItensInvestimentoGeral",
                "TbItensGastosOperacionais"
            ]
            for tabela in tabelas:
                self.cursor.execute(
                    f"DELETE FROM {tabela} WHERE usuario_id = %s AND mes = %s AND ano = %s",
                    (usuario_id, mes_selecionado, ano_selecionado)
                )
            print(f"[DEBUG] Dados antigos removidos para empresa={empresa_selecionada}, mes={mes_selecionado}, ano={ano_selecionado}")

            # ============================
            # 3. Mapeamento de nomes do Excel -> nomes no banco
            # ============================
            subgrupo_map = {
                "GERAL": "Geral",
                "RECEITA": "Receita",
                "CONTROLE DESPESAS POR NATURESAS SINTETICAS": "Controle",
                "OBRIGAÇÕES": "Obrigacoes",
                "GASTOS ADM": "GastosAdm",
                "MATERIA PRIMA": "MateriaPrima",
                "GASTOS OPERACIONAIS": "GastosOperacionais",
                "PESSOAL": "Pessoal",
                "DIVIDAS": "Dividas",
                "INVESTIMENTOS": "Investimentos",
                "INVESTIMENTOS GERAL NO NEGOCIO": "InvestimentosGeral"
            }

            grupo_map = {
                "VIABILIADE FINANCEIRA REAL": 1,
                "VIABILIADE FINANCEIRA PONTO DE EQUILIBRIO": 2,
                "VIABILIADE FINANCEIRA IDEAL": 3
            }

            # ============================
            # 4. Inserir Itens Normais (TbItens)
            # ============================
            for cenario in lista_cenarios:
                # Descobrir o nome do cenário olhando o primeiro item de qualquer subgrupo
                nome_cenario = None
                for itens in cenario.values():
                    if itens:
                        nome_cenario = itens[0].get("cenario", "").strip().upper()
                        break

                if not nome_cenario:
                    continue

                grupo_id = grupo_map.get(nome_cenario)
                if not grupo_id:
                    continue

                for subgrupo_nome, itens in cenario.items():
                    nome_subgrupo_excel = subgrupo_nome.strip().upper()
                    nome_subgrupo_banco = subgrupo_map.get(nome_subgrupo_excel, nome_subgrupo_excel)

                    self.cursor.execute(
                        "SELECT id FROM TbSubGrupo WHERE nome = %s AND grupo_id = %s",
                        (nome_subgrupo_banco, grupo_id)
                    )
                    subgrupo_row = self.cursor.fetchone()
                    if not subgrupo_row:
                        continue
                    subgrupo_id = subgrupo_row[0]

                    for item in itens:
                        valor = item.get("valor") if item.get("valor") is not None else 0.00
                        sql = """
                            INSERT INTO TbItens (descricao, porcentagem, valor, mes, ano, subgrupo_id, usuario_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        values = (
                            item["descricao"],
                            item.get("percentual"),
                            valor,
                            mes_selecionado,
                            ano_selecionado,
                            subgrupo_id,
                            usuario_id
                        )
                        self.cursor.execute(sql, values)

            # ============================
            # 5. Inserir Itens Especiais
            # ============================
            for grupo_id in [1, 2, 3]:
                # DIVIDAS
                for it in dados_especiais.get("DIVIDAS", []):
                    self.cursor.execute(
                        "SELECT id FROM TbSubGrupo WHERE nome = %s AND grupo_id = %s",
                        ("Dividas", grupo_id)
                    )
                    subgrupo_id = self.cursor.fetchone()[0]
                    sql = """
                        INSERT INTO TbItensDividas (descricao, valor_parc, valor_juros, valor_total_parc, mes, ano, subgrupo_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["valor_parc"], it["valor_juros"], it["valor_total_parcela"],
                        mes_selecionado, ano_selecionado, subgrupo_id, usuario_id
                    )
                    self.cursor.execute(sql, values)

                # INVESTIMENTOS
                for it in dados_especiais.get("INVESTIMENTOS", []):
                    self.cursor.execute(
                        "SELECT id FROM TbSubGrupo WHERE nome = %s AND grupo_id = %s",
                        ("Investimentos", grupo_id)
                    )
                    subgrupo_id = self.cursor.fetchone()[0]
                    sql = """
                        INSERT INTO TbItensInvestimentos (descricao, valor_parc, valor_juros, valor_total_parc, mes, ano, subgrupo_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["valor_parc"], it["valor_juros"], it["valor_total_parcela"],
                        mes_selecionado, ano_selecionado, subgrupo_id, usuario_id
                    )
                    self.cursor.execute(sql, values)

                # INVESTIMENTOS GERAL
                for it in dados_especiais.get("INVESTIMENTOS GERAL NO NEGOCIO", []):
                    self.cursor.execute(
                        "SELECT id FROM TbSubGrupo WHERE nome = %s AND grupo_id = %s",
                        ("InvestimentosGeral", grupo_id)
                    )
                    subgrupo_id = self.cursor.fetchone()[0]
                    sql = """
                        INSERT INTO TbItensInvestimentoGeral (descricao, valor, mes, ano, subgrupo_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["valor"],
                        mes_selecionado, ano_selecionado, subgrupo_id, usuario_id
                    )
                    self.cursor.execute(sql, values)

                # GASTOS OPERACIONAIS
                for it in dados_especiais.get("GASTOS OPERACIONAIS", []):
                    self.cursor.execute(
                        "SELECT id FROM TbSubGrupo WHERE nome = %s AND grupo_id = %s",
                        ("GastosOperacionais", grupo_id)
                    )
                    subgrupo_id = self.cursor.fetchone()[0]
                    sql = """
                        INSERT INTO TbItensGastosOperacionais (descricao, valor_custo_km, valor_mensal, mes, ano, subgrupo_id, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["custo_km"], it["custo_mensal"],
                        mes_selecionado, ano_selecionado, subgrupo_id, usuario_id
                    )
                    self.cursor.execute(sql, values)

            # ============================
            # 6. Commit final
            # ============================
            self.connection.commit()
            print("Itens salvos com sucesso no banco de dados (dados antigos sobrescritos).")

        except mysql.connector.Error as err:
            print(f"Erro ao salvar itens: {err}")
            self.connection.rollback()


    def buscar_dados_empresa(self, empresa_selecionada, mes_selecionado, ano_selecionado):
        try:
            # 1. Buscar o ID do usuário pela empresa
            self.cursor.execute("SELECT id FROM users WHERE empresa = %s", (empresa_selecionada,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa '{empresa_selecionada}' não encontrada na tabela users.")
            usuario_id = row[0]

            resultado = {
                "TbItens": [],
                "TbItensInvestimentos": [],
                "TbItensDividas": [],
                "TbItensInvestimentoGeral": [],
                "TbItensGastosOperacionais": []
            }

            # ============================
            # 2. Buscar Itens Normais
            # ============================
            sql_itens = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.porcentagem, i.valor
                FROM TbItens i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.usuario_id = %s AND i.mes = %s AND i.ano = %s
            """
            self.cursor.execute(sql_itens, (usuario_id, mes_selecionado, ano_selecionado))
            resultado["TbItens"] = self.cursor.fetchall()

            # ============================
            # 3. Buscar Itens Investimentos
            # ============================
            sql_invest = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor_parc, i.valor_juros, i.valor_total_parc
                FROM TbItensInvestimentos i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.usuario_id = %s AND i.mes = %s AND i.ano = %s
            """
            self.cursor.execute(sql_invest, (usuario_id, mes_selecionado, ano_selecionado))
            resultado["TbItensInvestimentos"] = self.cursor.fetchall()

            # ============================
            # 4. Buscar Itens Dívidas
            # ============================
            sql_dividas = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor_parc, i.valor_juros, i.valor_total_parc
                FROM TbItensDividas i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.usuario_id = %s AND i.mes = %s AND i.ano = %s
            """
            self.cursor.execute(sql_dividas, (usuario_id, mes_selecionado, ano_selecionado))
            resultado["TbItensDividas"] = self.cursor.fetchall()

            # ============================
            # 5. Buscar Investimento Geral
            # ============================
            sql_invest_geral = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor
                FROM TbItensInvestimentoGeral i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.usuario_id = %s AND i.mes = %s AND i.ano = %s
            """
            self.cursor.execute(sql_invest_geral, (usuario_id, mes_selecionado, ano_selecionado))
            resultado["TbItensInvestimentoGeral"] = self.cursor.fetchall()

            # ============================
            # 6. Buscar Gastos Operacionais
            # ============================
            sql_gastos = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor_custo_km, i.valor_mensal
                FROM TbItensGastosOperacionais i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.usuario_id = %s AND i.mes = %s AND i.ano = %s
            """
            self.cursor.execute(sql_gastos, (usuario_id, mes_selecionado, ano_selecionado))
            resultado["TbItensGastosOperacionais"] = self.cursor.fetchall()

            return resultado

        except mysql.connector.Error as err:
            print(f"Erro ao buscar dados: {err}")
            return None


    def excluir_dados_empresa(self, empresa_selecionada, mes_selecionado, ano_selecionado):
        """
        Exclui todos os registros de uma empresa em um determinado mês e ano
        em todas as tabelas de itens.
        """
        try:
            # 1. Buscar o ID do usuário pela empresa
            self.cursor.execute("SELECT id FROM users WHERE empresa = %s", (empresa_selecionada,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa '{empresa_selecionada}' não encontrada na tabela users.")
            usuario_id = row[0]

            # 2. Listar as tabelas que precisam ser limpas
            tabelas = [
                "TbItens",
                "TbItensDividas",
                "TbItensInvestimentos",
                "TbItensInvestimentoGeral",
                "TbItensGastosOperacionais"
            ]

            # 3. Executar exclusão em cada tabela
            for tabela in tabelas:
                self.cursor.execute(
                    f"DELETE FROM {tabela} WHERE usuario_id = %s AND mes = %s AND ano = %s",
                    (usuario_id, mes_selecionado, ano_selecionado)
                )

            # 4. Commit final
            self.connection.commit()
            print(f"[DEBUG] Dados excluídos para empresa={empresa_selecionada}, mes={mes_selecionado}, ano={ano_selecionado}")
            return True

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao excluir dados: {err}")
            self.connection.rollback()
            return False


    def get_meses_com_dados(self, usuario_id, ano):
        """
        Retorna uma lista com os meses (1..12) em que já existem dados
        para o usuário e ano especificados.
        """
        try:
            sql = """
                SELECT DISTINCT mes
                FROM TbItens
                WHERE usuario_id = %s AND ano = %s
            """
            self.cursor.execute(sql, (usuario_id, ano))
            rows = self.cursor.fetchall()

            # rows vem como lista de tuplas [(1,), (3,), (7,)...]
            meses = [r[0] for r in rows]
            return meses

        except mysql.connector.Error as err:
            print(f"[ERRO] get_meses_com_dados: {err}")
            return []






















    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.close_connection()