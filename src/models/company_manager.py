from models.auth import DatabaseConnection
import mysql.connector

class CompanyManager(DatabaseConnection):

    def salvar_itens_empresa(self, empresa_id, ano_selecionado, lista_cenarios, dados_especiais):
        """
        Salva dados da empresa para um ANO específico (SEM mês).
        Remove os dados antigos do mesmo ano antes de inserir os novos.
        Agora recebe diretamente o empresa_id ao invés do nome da empresa.
        """
        try:
            # 1. Verificar se a empresa existe
            self.cursor.execute("SELECT id FROM empresas WHERE id = %s", (empresa_id,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa com ID '{empresa_id}' não encontrada na tabela empresas.")

            # ============================
            # 2. Limpar dados existentes do mesmo ANO (para evitar duplicação)
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
                    f"DELETE FROM {tabela} WHERE empresa_id = %s AND ano = %s",
                    (empresa_id, ano_selecionado)
                )
            print(f"[DEBUG] Dados antigos removidos para empresa_id={empresa_id}, ano={ano_selecionado}")

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
            # 4. Inserir Itens Normais (TbItens) - SEM MÊS
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
                            INSERT INTO TbItens (descricao, porcentagem, valor, ano, subgrupo_id, empresa_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        values = (
                            item["descricao"],
                            item.get("percentual"),
                            valor,
                            ano_selecionado,
                            subgrupo_id,
                            empresa_id
                        )
                        self.cursor.execute(sql, values)

            # ============================
            # 5. Inserir Itens Especiais - SEM MÊS
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
                        INSERT INTO TbItensDividas (descricao, valor_parc, valor_juros, valor_total_parc, ano, subgrupo_id, empresa_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["valor_parc"], it["valor_juros"], it["valor_total_parcela"],
                        ano_selecionado, subgrupo_id, empresa_id
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
                        INSERT INTO TbItensInvestimentos (descricao, valor_parc, valor_juros, valor_total_parc, ano, subgrupo_id, empresa_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["valor_parc"], it["valor_juros"], it["valor_total_parcela"],
                        ano_selecionado, subgrupo_id, empresa_id
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
                        INSERT INTO TbItensInvestimentoGeral (descricao, valor, ano, subgrupo_id, empresa_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["valor"],
                        ano_selecionado, subgrupo_id, empresa_id
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
                        INSERT INTO TbItensGastosOperacionais (descricao, valor_custo_km, valor_mensal, ano, subgrupo_id, empresa_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        it["descricao"], it["custo_km"], it["custo_mensal"],
                        ano_selecionado, subgrupo_id, empresa_id
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


    def buscar_dados_empresa(self, empresa_id, ano_selecionado):
        """
        Busca todos os dados de uma empresa para um ANO específico (SEM mês).
        Agora recebe diretamente o empresa_id.
        """
        try:
            # 1. Verificar se a empresa existe
            self.cursor.execute("SELECT id FROM empresas WHERE id = %s", (empresa_id,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa com ID '{empresa_id}' não encontrada na tabela empresas.")

            resultado = {
                "TbItens": [],
                "TbItensInvestimentos": [],
                "TbItensDividas": [],
                "TbItensInvestimentoGeral": [],
                "TbItensGastosOperacionais": []
            }

            # ============================
            # 2. Buscar Itens Normais - SEM MÊS
            # ============================
            sql_itens = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.porcentagem, i.valor
                FROM TbItens i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.empresa_id = %s AND i.ano = %s
            """
            self.cursor.execute(sql_itens, (empresa_id, ano_selecionado))
            resultado["TbItens"] = self.cursor.fetchall()

            # ============================
            # 3. Buscar Itens Investimentos - SEM MÊS
            # ============================
            sql_invest = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor_parc, i.valor_juros, i.valor_total_parc
                FROM TbItensInvestimentos i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.empresa_id = %s AND i.ano = %s
            """
            self.cursor.execute(sql_invest, (empresa_id, ano_selecionado))
            resultado["TbItensInvestimentos"] = self.cursor.fetchall()

            # ============================
            # 4. Buscar Itens Dívidas - SEM MÊS
            # ============================
            sql_dividas = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor_parc, i.valor_juros, i.valor_total_parc
                FROM TbItensDividas i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.empresa_id = %s AND i.ano = %s
            """
            self.cursor.execute(sql_dividas, (empresa_id, ano_selecionado))
            resultado["TbItensDividas"] = self.cursor.fetchall()

            # ============================
            # 5. Buscar Investimento Geral - SEM MÊS
            # ============================
            sql_invest_geral = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor
                FROM TbItensInvestimentoGeral i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.empresa_id = %s AND i.ano = %s
            """
            self.cursor.execute(sql_invest_geral, (empresa_id, ano_selecionado))
            resultado["TbItensInvestimentoGeral"] = self.cursor.fetchall()

            # ============================
            # 6. Buscar Gastos Operacionais - SEM MÊS
            # ============================
            sql_gastos = """
                SELECT g.nome AS grupo, s.nome AS subgrupo, i.descricao, i.valor_custo_km, i.valor_mensal
                FROM TbItensGastosOperacionais i
                JOIN TbSubGrupo s ON i.subgrupo_id = s.id
                JOIN TbGrupo g ON s.grupo_id = g.id
                WHERE i.empresa_id = %s AND i.ano = %s
            """
            self.cursor.execute(sql_gastos, (empresa_id, ano_selecionado))
            resultado["TbItensGastosOperacionais"] = self.cursor.fetchall()

            return resultado

        except mysql.connector.Error as err:
            print(f"Erro ao buscar dados: {err}")
            return None


    def excluir_dados_empresa(self, empresa_id, ano_selecionado):
        """
        Exclui todos os registros de uma empresa para um ANO específico (SEM mês).
        Agora recebe diretamente o empresa_id.
        """
        try:
            # 1. Verificar se a empresa existe
            self.cursor.execute("SELECT id FROM empresas WHERE id = %s", (empresa_id,))
            row = self.cursor.fetchone()
            if not row:
                raise Exception(f"Empresa com ID '{empresa_id}' não encontrada na tabela empresas.")

            # 2. Listar as tabelas que precisam ser limpas
            tabelas = [
                "TbItens",
                "TbItensDividas",
                "TbItensInvestimentos",
                "TbItensInvestimentoGeral",
                "TbItensGastosOperacionais"
            ]

            # 3. Executar exclusão em cada tabela - SEM MÊS
            for tabela in tabelas:
                self.cursor.execute(
                    f"DELETE FROM {tabela} WHERE empresa_id = %s AND ano = %s",
                    (empresa_id, ano_selecionado)
                )

            # 4. Commit final
            self.connection.commit()
            print(f"[DEBUG] Dados excluídos para empresa_id={empresa_id}, ano={ano_selecionado}")
            return True

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao excluir dados: {err}")
            self.connection.rollback()
            return False


    def get_anos_com_dados(self, empresa_id):
        """
        Retorna uma lista com os anos em que existem dados para a empresa.
        Agora busca por empresa_id ao invés de usuario_id.
        """
        try:
            sql = """
                SELECT DISTINCT ano
                FROM TbItens
                WHERE empresa_id = %s
                ORDER BY ano DESC
            """
            self.cursor.execute(sql, (empresa_id,))
            rows = self.cursor.fetchall()

            # rows vem como lista de tuplas [(2025,), (2024,), ...]
            anos = [r[0] for r in rows]
            return anos

        except mysql.connector.Error as err:
            print(f"[ERRO] get_anos_com_dados: {err}")
            return []


    def verificar_dados_existentes(self, empresa_id, ano):
        """
        Verifica se existem dados para uma empresa em um ano específico.
        Retorna True se existir, False caso contrário.
        Agora usa empresa_id ao invés de usuario_id.
        """
        try:
            sql = """
                SELECT COUNT(*) as total
                FROM TbItens
                WHERE empresa_id = %s AND ano = %s
            """
            self.cursor.execute(sql, (empresa_id, ano))
            row = self.cursor.fetchone()

            return row[0] > 0 if row else False

        except mysql.connector.Error as err:
            print(f"[ERRO] verificar_dados_existentes: {err}")
            return False


    # ============================
    # MÉTODOS PARA GERENCIAR EMPRESAS (CRUD)
    # ============================

    def criar_empresa(self, nome, cnpj, telefone, email, cep, complemento, seguimento, website=None):
        """
        Cria uma nova empresa no sistema.
        Retorna o ID da empresa criada ou None em caso de erro.
        """
        try:
            sql = """
                INSERT INTO empresas (nome, cnpj, website, telefone, email, cep, complemento, seguimento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (nome, cnpj, website, telefone, email, cep, complemento, seguimento)
            self.cursor.execute(sql, values)
            self.connection.commit()

            empresa_id = self.cursor.lastrowid
            print(f"[DEBUG] Empresa '{nome}' criada com sucesso. ID: {empresa_id}")
            return empresa_id

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao criar empresa: {err}")
            self.connection.rollback()
            return None

    def buscar_empresa_por_id(self, empresa_id):
        """Busca uma empresa pelo ID e retorna seus dados."""
        try:
            sql = "SELECT * FROM empresas WHERE id = %s"
            self.cursor.execute(sql, (empresa_id,))
            row = self.cursor.fetchone()

            if row:
                return {
                    'id': row[0],
                    'nome': row[1],
                    'cnpj': row[2],
                    'website': row[3],
                    'telefone': row[4],
                    'email': row[5],
                    'cep': row[6],
                    'complemento': row[7],
                    'seguimento': row[8],
                    'created_at': row[9]
                }
            return None

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao buscar empresa: {err}")
            return None

    def buscar_empresa_por_cnpj(self, cnpj):
        """Busca uma empresa pelo CNPJ."""
        try:
            sql = "SELECT * FROM empresas WHERE cnpj = %s"
            self.cursor.execute(sql, (cnpj,))
            row = self.cursor.fetchone()

            if row:
                return {
                    'id': row[0],
                    'nome': row[1],
                    'cnpj': row[2],
                    'website': row[3],
                    'telefone': row[4],
                    'email': row[5],
                    'cep': row[6],
                    'complemento': row[7],
                    'seguimento': row[8],
                    'created_at': row[9]
                }
            return None

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao buscar empresa por CNPJ: {err}")
            return None

    def listar_todas_empresas(self):
        """Retorna uma lista com todas as empresas cadastradas."""
        try:
            sql = "SELECT * FROM empresas ORDER BY nome ASC"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()

            empresas = []
            for row in rows:
                empresas.append({
                    'id': row[0],
                    'nome': row[1],
                    'cnpj': row[2],
                    'website': row[3],
                    'telefone': row[4],
                    'email': row[5],
                    'cep': row[6],
                    'complemento': row[7],
                    'seguimento': row[8],
                    'created_at': row[9]
                })

            return empresas

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao listar empresas: {err}")
            return []

    def atualizar_empresa(self, empresa_id, nome, cnpj, telefone, email, cep, complemento, seguimento, website=None):
        """Atualiza os dados de uma empresa."""
        try:
            sql = """
                UPDATE empresas
                SET nome = %s, cnpj = %s, website = %s, telefone = %s,
                    email = %s, cep = %s, complemento = %s, seguimento = %s
                WHERE id = %s
            """
            values = (nome, cnpj, website, telefone, email, cep, complemento, seguimento, empresa_id)
            self.cursor.execute(sql, values)
            self.connection.commit()

            print(f"[DEBUG] Empresa ID {empresa_id} atualizada com sucesso.")
            return True

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao atualizar empresa: {err}")
            self.connection.rollback()
            return False

    def deletar_empresa(self, empresa_id):
        """
        Deleta uma empresa do sistema.
        ATENÇÃO: Isso também deletará todos os dados relacionados (CASCADE).
        """
        try:
            sql = "DELETE FROM empresas WHERE id = %s"
            self.cursor.execute(sql, (empresa_id,))
            self.connection.commit()

            print(f"[DEBUG] Empresa ID {empresa_id} deletada com sucesso.")
            return True

        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao deletar empresa: {err}")
            self.connection.rollback()
            return False

    # ====================================================================
    # FUNÇÕES BPO (DADOS MENSAIS)
    # ====================================================================

    def salvar_dados_bpo_empresa(self, empresa_id, ano, mes, dados_processados):
        """Salva dados BPO processados para empresa/ano/mês específico"""
        try:
            import json

            # Verificar se empresa existe
            self.cursor.execute("SELECT id FROM empresas WHERE id = %s", (empresa_id,))
            if not self.cursor.fetchone():
                raise Exception(f"Empresa ID {empresa_id} não encontrada")

            # Converter dados para JSON
            dados_json = json.dumps(dados_processados, ensure_ascii=False)

            # Deletar dados antigos do mesmo período
            self.cursor.execute(
                "DELETE FROM TbBpoDados WHERE empresa_id = %s AND ano = %s AND mes = %s",
                (empresa_id, ano, mes)
            )

            # Inserir novos dados
            sql = """
                INSERT INTO TbBpoDados (empresa_id, ano, mes, dados_json)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(sql, (empresa_id, ano, mes, dados_json))
            self.connection.commit()

            print(f"[DEBUG] Dados BPO salvos: empresa_id={empresa_id}, ano={ano}, mes={mes}")
            return True

        except Exception as err:
            print(f"[ERRO] Erro ao salvar dados BPO: {err}")
            self.connection.rollback()
            return False

    def buscar_dados_bpo_empresa(self, empresa_id, ano, mes):
        """Busca dados BPO de empresa/ano/mês específico"""
        try:
            import json

            sql = """
                SELECT dados_json, created_at
                FROM TbBpoDados
                WHERE empresa_id = %s AND ano = %s AND mes = %s
            """
            self.cursor.execute(sql, (empresa_id, ano, mes))
            row = self.cursor.fetchone()

            if row:
                dados_json = json.loads(row[0])
                return {
                    'dados': dados_json,
                    'data_upload': row[1]
                }
            return None

        except Exception as err:
            print(f"[ERRO] Erro ao buscar dados BPO: {err}")
            return None

    def excluir_dados_bpo_empresa(self, empresa_id, ano, mes):
        """Exclui dados BPO de empresa/ano/mês específico"""
        try:
            sql = "DELETE FROM TbBpoDados WHERE empresa_id = %s AND ano = %s AND mes = %s"
            self.cursor.execute(sql, (empresa_id, ano, mes))
            self.connection.commit()

            print(f"[DEBUG] Dados BPO excluídos: empresa_id={empresa_id}, ano={ano}, mes={mes}")
            return True

        except Exception as err:
            print(f"[ERRO] Erro ao excluir dados BPO: {err}")
            self.connection.rollback()
            return False

    # ====================================================================
    # FUNÇÕES RELATÓRIO DE VIABILIDADE
    # ====================================================================

    def salvar_template_relatorio(self, empresa_id, ano, template_texto):
        """Salva template do relatório de viabilidade para empresa/ano específico"""
        try:
            # Verificar se empresa existe
            self.cursor.execute("SELECT id FROM empresas WHERE id = %s", (empresa_id,))
            if not self.cursor.fetchone():
                raise Exception(f"Empresa ID {empresa_id} não encontrada")

            # Deletar template antigo do mesmo período
            self.cursor.execute(
                "DELETE FROM TbRelatorioTemplate WHERE empresa_id = %s AND ano = %s",
                (empresa_id, ano)
            )

            # Inserir novo template
            sql = """
                INSERT INTO TbRelatorioTemplate (empresa_id, ano, template_texto)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(sql, (empresa_id, ano, template_texto))
            self.connection.commit()

            print(f"[DEBUG] Template de relatório salvo: empresa_id={empresa_id}, ano={ano}")
            return True

        except Exception as err:
            print(f"[ERRO] Erro ao salvar template de relatório: {err}")
            self.connection.rollback()
            return False

    def buscar_template_relatorio(self, empresa_id, ano):
        """Busca template do relatório de viabilidade de empresa/ano específico"""
        try:
            sql = """
                SELECT template_texto, created_at
                FROM TbRelatorioTemplate
                WHERE empresa_id = %s AND ano = %s
            """
            self.cursor.execute(sql, (empresa_id, ano))
            row = self.cursor.fetchone()

            if row:
                return {
                    'template': row[0],
                    'data_upload': row[1]
                }
            return None

        except Exception as err:
            print(f"[ERRO] Erro ao buscar template de relatório: {err}")
            return None

    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.close_connection()