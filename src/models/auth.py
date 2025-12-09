import mysql.connector
from mysql.connector import errorcode

# Credenciais do banco de dados centralizadas
# DB_CONFIG = {
#     'host': "localhost",
#     'user': "root",
#     'password': "root",
#     'database': "WaysDb"
# }

DB_CONFIG = {
    'host': "mysql.wayssolution.kinghost.net",
    'user': "wayssolution",
    'password': "DS6tgb8yaHB67",
    'database': "wayssolution"
}

class DatabaseConnection:
    def __init__(self):
        self.host = DB_CONFIG['host']
        self.user = DB_CONFIG['user']
        self.password = DB_CONFIG['password']
        self.database_name = DB_CONFIG['database']
        self.connection = None

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor(buffered=True)
            
            self.create_database_if_not_exists()
            self.connection.database = self.database_name
            self.create_user_table_if_not_exists()
            self.create_empresa_table_if_not_exists()
            self.create_user_empresa_table_if_not_exists()
            self.create_empresa_tables_if_not_exists()
            self.create_bpo_tables_if_not_exists()
            self.insert_default_grupos_subgrupos()

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Erro de autenticação: Verifique seu usuário ou senha.")
            else:
                print(f"Erro ao conectar ao banco de dados: {err}")
            self.connection = None

    def create_database_if_not_exists(self):
        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name}")
            self.connection.commit()
            print(f"Banco de dados '{self.database_name}' verificado/criado com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao criar o banco de dados: {err}")

    def create_user_table_if_not_exists(self):
        """Cria a tabela de usuários (sem campos de empresa)"""
        table_schema = (
            "CREATE TABLE IF NOT EXISTS users ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  nome VARCHAR(255) NOT NULL,"
            "  email VARCHAR(255) NOT NULL UNIQUE,"
            "  telefone VARCHAR(20) NOT NULL,"
            "  password VARCHAR(255) NOT NULL,"
            "  role ENUM('admin', 'user') NOT NULL,"
            "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        try:
            self.cursor.execute(table_schema)
            self.connection.commit()
            print("Tabela 'users' verificada/criada com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao criar a tabela de usuários: {err}")

    def create_empresa_table_if_not_exists(self):
        """Cria a tabela de empresas"""
        table_schema = (
            "CREATE TABLE IF NOT EXISTS empresas ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  nome VARCHAR(255) NOT NULL,"
            "  cnpj VARCHAR(18) NOT NULL UNIQUE,"
            "  website VARCHAR(255),"
            "  telefone VARCHAR(20) NOT NULL,"
            "  email VARCHAR(255) NOT NULL,"
            "  cep VARCHAR(10) NOT NULL,"
            "  complemento TEXT,"
            "  seguimento VARCHAR(255) NOT NULL,"
            "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        try:
            self.cursor.execute(table_schema)
            self.connection.commit()
            print("Tabela 'empresas' verificada/criada com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao criar a tabela de empresas: {err}")

    def create_user_empresa_table_if_not_exists(self):
        """Cria a tabela de relacionamento muitos-para-muitos entre users e empresas"""
        table_schema = (
            "CREATE TABLE IF NOT EXISTS user_empresa ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  user_id INT NOT NULL,"
            "  empresa_id INT NOT NULL,"
            "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
            "  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,"
            "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,"
            "  UNIQUE KEY unique_user_empresa (user_id, empresa_id)"
            ")"
        )
        try:
            self.cursor.execute(table_schema)
            self.connection.commit()
            print("Tabela 'user_empresa' verificada/criada com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao criar a tabela de relacionamento user_empresa: {err}")

    def create_empresa_tables_if_not_exists(self):
        try:
            # =========================
            # Tabela de Grupos
            # =========================
            grupo_schema = (
                "CREATE TABLE IF NOT EXISTS TbGrupo ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  nome VARCHAR(255) NOT NULL"
                ")"
            )
            self.cursor.execute(grupo_schema)

            # =========================
            # Tabela de SubGrupos
            # =========================
            subgrupo_schema = (
                "CREATE TABLE IF NOT EXISTS TbSubGrupo ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  nome VARCHAR(255) NOT NULL,"
                "  grupo_id INT NOT NULL,"
                "  FOREIGN KEY (grupo_id) REFERENCES TbGrupo(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(subgrupo_schema)

            # =========================
            # Tabela de Itens (cenários normais) - SEM MÊS - FK EMPRESA
            # =========================
            itens_schema = (
                "CREATE TABLE IF NOT EXISTS TbItens ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  descricao VARCHAR(255) NOT NULL,"
                "  porcentagem DECIMAL(10,2),"
                "  valor DECIMAL(15,2) NOT NULL,"
                "  ano INT NOT NULL,"
                "  subgrupo_id INT NOT NULL,"
                "  empresa_id INT NOT NULL,"
                "  FOREIGN KEY (subgrupo_id) REFERENCES TbSubGrupo(id) ON DELETE CASCADE,"
                "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(itens_schema)

            # =========================
            # Tabela de Itens Investimentos - SEM MÊS - FK EMPRESA
            # =========================
            investimentos_schema = (
                "CREATE TABLE IF NOT EXISTS TbItensInvestimentos ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  descricao VARCHAR(255) NOT NULL,"
                "  valor_parc DECIMAL(15,2),"
                "  valor_juros DECIMAL(15,2),"
                "  valor_total_parc DECIMAL(15,2),"
                "  ano INT NOT NULL,"
                "  subgrupo_id INT NOT NULL,"
                "  empresa_id INT NOT NULL,"
                "  FOREIGN KEY (subgrupo_id) REFERENCES TbSubGrupo(id) ON DELETE CASCADE,"
                "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(investimentos_schema)

            # =========================
            # Tabela de Itens Dívidas - SEM MÊS - FK EMPRESA
            # =========================
            dividas_schema = (
                "CREATE TABLE IF NOT EXISTS TbItensDividas ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  descricao VARCHAR(255) NOT NULL,"
                "  valor_parc DECIMAL(15,2),"
                "  valor_juros DECIMAL(15,2),"
                "  valor_total_parc DECIMAL(15,2),"
                "  ano INT NOT NULL,"
                "  subgrupo_id INT NOT NULL,"
                "  empresa_id INT NOT NULL,"
                "  FOREIGN KEY (subgrupo_id) REFERENCES TbSubGrupo(id) ON DELETE CASCADE,"
                "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(dividas_schema)

            # =========================
            # Tabela de Investimento Geral - SEM MÊS - FK EMPRESA
            # =========================
            investimento_geral_schema = (
                "CREATE TABLE IF NOT EXISTS TbItensInvestimentoGeral ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  descricao VARCHAR(255) NOT NULL,"
                "  valor DECIMAL(15,2),"
                "  ano INT NOT NULL,"
                "  subgrupo_id INT NOT NULL,"
                "  empresa_id INT NOT NULL,"
                "  FOREIGN KEY (subgrupo_id) REFERENCES TbSubGrupo(id) ON DELETE CASCADE,"
                "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(investimento_geral_schema)

            # =========================
            # Tabela de Gastos Operacionais - SEM MÊS - FK EMPRESA
            # =========================
            gastos_operacionais_schema = (
                "CREATE TABLE IF NOT EXISTS TbItensGastosOperacionais ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  descricao VARCHAR(255) NOT NULL,"
                "  valor_custo_km DECIMAL(15,2),"
                "  valor_mensal DECIMAL(15,2),"
                "  ano INT NOT NULL,"
                "  subgrupo_id INT NOT NULL,"
                "  empresa_id INT NOT NULL,"
                "  FOREIGN KEY (subgrupo_id) REFERENCES TbSubGrupo(id) ON DELETE CASCADE,"
                "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(gastos_operacionais_schema)

            # Commit final
            self.connection.commit()
            print("Todas as tabelas de dados verificadas/criadas com sucesso (FK EMPRESA, SEM coluna MÊS).")

        except mysql.connector.Error as err:
            print(f"Erro ao criar as tabelas de empresas: {err}")

    def create_bpo_tables_if_not_exists(self):
        """Cria tabelas para armazenar dados BPO (mensal)"""
        try:
            # Tabela principal BPO - armazena snapshot completo mensal em JSON
            bpo_schema = (
                "CREATE TABLE IF NOT EXISTS TbBpoDados ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  empresa_id INT NOT NULL,"
                "  ano INT NOT NULL,"
                "  mes INT NOT NULL,"
                "  dados_json LONGTEXT NOT NULL,"
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                "  FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,"
                "  UNIQUE KEY unique_empresa_ano_mes (empresa_id, ano, mes)"
                ")"
            )
            self.cursor.execute(bpo_schema)
            self.connection.commit()
            print("Tabela 'TbBpoDados' verificada/criada com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao criar tabelas BPO: {err}")

    def insert_default_grupos_subgrupos(self):
        try:
            # Grupos padrão
            grupos = ["Viabilidade Real", "Viabilidade PE", "Viabilidade Ideal"]

            # Subgrupos padrão
            subgrupos = [
                "Geral",
                "Receita",
                "Controle",
                "Obrigacoes",
                "GastosAdm",
                "MateriaPrima",
                "GastosOperacionais",
                "Pessoal",
                "Dividas",
                "Investimentos",
                "InvestimentosGeral",
                "GastosOperacionais"  # aparece duas vezes na sua lista
            ]

            # Inserir grupos se não existirem
            grupo_ids = {}
            for g in grupos:
                self.cursor.execute("SELECT id FROM TbGrupo WHERE nome = %s", (g,))
                row = self.cursor.fetchone()
                if row:
                    grupo_id = row[0]
                else:
                    self.cursor.execute("INSERT INTO TbGrupo (nome) VALUES (%s)", (g,))
                    self.connection.commit()
                    grupo_id = self.cursor.lastrowid
                grupo_ids[g] = grupo_id

            # Inserir subgrupos para cada grupo
            for g, grupo_id in grupo_ids.items():
                for s in subgrupos:
                    # Verifica se já existe
                    self.cursor.execute(
                        "SELECT id FROM TbSubGrupo WHERE nome = %s AND grupo_id = %s",
                        (s, grupo_id)
                    )
                    row = self.cursor.fetchone()
                    if not row:
                        self.cursor.execute(
                            "INSERT INTO TbSubGrupo (nome, grupo_id) VALUES (%s, %s)",
                            (s, grupo_id)
                        )
            self.connection.commit()
            print("Grupos e subgrupos padrão inseridos/verificados com sucesso.")

        except mysql.connector.Error as err:
            print(f"Erro ao inserir grupos/subgrupos padrão: {err}")

    def get_connection(self):
        return self.connection

    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Conexão com o banco de dados fechada.")