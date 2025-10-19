import mysql.connector
from mysql.connector import errorcode

# Credenciais do banco de dados centralizadas
DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': "root",
    'database': "WaysDb"
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
            self.cursor = self.connection.cursor()
            
            self.create_database_if_not_exists()
            self.connection.database = self.database_name
            self.create_user_table_if_not_exists()
            self.create_empresa_tables_if_not_exists()

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
        table_schema = (
            "CREATE TABLE IF NOT EXISTS users ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  nome VARCHAR(255) NOT NULL,"
            "  email VARCHAR(255) NOT NULL UNIQUE,"
            "  telefone VARCHAR(20) NOT NULL,"
            "  empresa VARCHAR(255),"
            "  seguimento VARCHAR(255),"
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

    def create_empresa_tables_if_not_exists(self):
        try:
            # Tabela de Grupos
            grupo_schema = (
                "CREATE TABLE IF NOT EXISTS TbGrupo ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  nome VARCHAR(255) NOT NULL"
                ")"
            )
            self.cursor.execute(grupo_schema)

            # Tabela de SubGrupos
            subgrupo_schema = (
                "CREATE TABLE IF NOT EXISTS TbSubGrupo ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  nome VARCHAR(255) NOT NULL,"
                "  grupo_id INT NOT NULL,"
                "  FOREIGN KEY (grupo_id) REFERENCES TbGrupo(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(subgrupo_schema)

            # Tabela de Itens
            itens_schema = (
                "CREATE TABLE IF NOT EXISTS TbItens ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  descricao VARCHAR(255) NOT NULL,"
                "  porcentagem DECIMAL(10,2),"
                "  valor DECIMAL(15,2) NOT NULL,"
                "  mes INT NOT NULL,"
                "  ano INT NOT NULL,"
                "  subgrupo_id INT NOT NULL,"
                "  usuario_id INT NOT NULL,"
                "  FOREIGN KEY (subgrupo_id) REFERENCES TbSubGrupo(id) ON DELETE CASCADE,"
                "  FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE CASCADE"
                ")"
            )
            self.cursor.execute(itens_schema)

            self.connection.commit()
            print("Tabelas 'TbGrupo', 'TbSubGrupo' e 'TbItens' verificadas/criadas com sucesso.")

        except mysql.connector.Error as err:
            print(f"Erro ao criar as tabelas de empresas: {err}")

    def get_connection(self):
        return self.connection

    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Conexão com o banco de dados fechada.")