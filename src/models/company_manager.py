from models.auth import DatabaseConnection
import mysql.connector

class CompanyManager(DatabaseConnection):

    def salvar_itens_empresa(self, empresa_selecionada, mes_selecionado, ano_selecionado, lista_cenarios, dados_especiais):
        try:
            # ============================
            # 1. Buscar o ID do usuário pela empresa
            # ============================
            self.cursor.execute("SELECT id FROM users WHERE empresa = %s", (empresa_selecionada,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa '{empresa_selecionada}' não encontrada na tabela users.")
            usuario_id = row[0]

            # ============================
            # 2. Mapeamento de nomes do Excel -> nomes no banco
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

            # ============================
            # 3. Inserir Itens Normais (TbItens)
            # ============================
            for cenario in lista_cenarios:
                for subgrupo_nome, itens in cenario.items():
                    nome_subgrupo_excel = subgrupo_nome.strip().upper()
                    nome_subgrupo_banco = subgrupo_map.get(nome_subgrupo_excel, nome_subgrupo_excel)

                    # Buscar o id do subgrupo
                    self.cursor.execute("SELECT id FROM TbSubGrupo WHERE nome = %s", (nome_subgrupo_banco,))
                    subgrupo_row = self.cursor.fetchone()
                    if not subgrupo_row:
                        print(f"Subgrupo '{nome_subgrupo_excel}' não encontrado (mesmo após mapear), pulando...")
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
            # 4. Inserir Itens Especiais
            # ============================

            # DIVIDAS
            for it in dados_especiais.get("DIVIDAS", []):
                nome_subgrupo_banco = subgrupo_map.get("DIVIDAS", "Dividas")
                self.cursor.execute("SELECT id FROM TbSubGrupo WHERE nome = %s", (nome_subgrupo_banco,))
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
                nome_subgrupo_banco = subgrupo_map.get("INVESTIMENTOS", "Investimentos")
                self.cursor.execute("SELECT id FROM TbSubGrupo WHERE nome = %s", (nome_subgrupo_banco,))
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
                nome_subgrupo_banco = subgrupo_map.get("INVESTIMENTOS GERAL NO NEGOCIO", "InvestimentosGeral")
                self.cursor.execute("SELECT id FROM TbSubGrupo WHERE nome = %s", (nome_subgrupo_banco,))
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
                nome_subgrupo_banco = subgrupo_map.get("GASTOS OPERACIONAIS", "GastosOperacionais")
                self.cursor.execute("SELECT id FROM TbSubGrupo WHERE nome = %s", (nome_subgrupo_banco,))
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
            # 5. Commit final
            # ============================
            self.connection.commit()
            print("Itens salvos com sucesso no banco de dados.")

        except mysql.connector.Error as err:
            print(f"Erro ao salvar itens: {err}")
            self.connection.rollback()




























    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.close_connection()