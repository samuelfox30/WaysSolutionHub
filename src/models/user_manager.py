from models.auth import DatabaseConnection
import mysql.connector

class UserManager:
    def __init__(self):
        self.db_connector = DatabaseConnection()
        self.db_connection = self.db_connector.get_connection()
        self.cursor = None
        if self.db_connection:
            self.cursor = self.db_connection.cursor(dictionary=True)

    def find_user_by_email(self, email):
        if not self.db_connection or not self.db_connection.is_connected():
            print("Conexão com o banco de dados não está ativa.")
            return None
            
        try:
            query = "SELECT * FROM users WHERE email = %s"
            self.cursor.execute(query, (email,))
            user = self.cursor.fetchone()
            
            return user
            
        except mysql.connector.Error as err:
            print(f"Erro ao buscar usuário: {err}")
            return None
        finally:
            # Feche a conexão do cursor após a operação, mas não a conexão principal
            if self.cursor:
                self.cursor.close()
                self.cursor = None


    def register_user(self, name, email, telefone, company, seguimento, password, role):
        """
        Registers a new user in the database.

        Args:
            name (str): User's full name.
            email (str): User's email address.
            telefone (str): User's phone number.
            company (str): User's company name.
            seguimento (str): User's business segment.
            password (str): User's plain-text password.
            role (str): User's role (e.g., 'admin', 'client').

        Returns:
            bool: True on success, False otherwise.
        """
        if not self.db_connection or not self.db_connection.is_connected():
            print("Conexão com o banco de dados não está ativa.")
            return False

        try:
            # Reopen cursor if it was closed
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            # Hash the password before storing it in the database
            from controllers.auth.hash import hash_senha_sha256
            hashed_password = hash_senha_sha256(password)

            query = """
                INSERT INTO users (nome, email, telefone, empresa, seguimento, password, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (name, email, telefone, company, seguimento, hashed_password, role))
            self.db_connection.commit()
            return True

        except mysql.connector.Error as err:
            print(f"Erro ao cadastrar usuário: {err}")
            self.db_connection.rollback()
            return False
        finally:
            # It's better to keep the cursor open
            pass


    def get_all_users(self):
        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = "SELECT id, nome, email, empresa, role FROM users"
            self.cursor.execute(query)
            users = self.cursor.fetchall()
            return users

        except mysql.connector.Error as err:
            print(f"Erro ao buscar todos os usuários: {err}")
            return []


    def delete_user(self, user_id):
        """
        Exclui um usuário do banco de dados com base no ID.

        Args:
            user_id (int): O ID do usuário a ser excluído.

        Returns:
            bool: True em caso de sucesso, False em caso de falha.
        """
        if not self.db_connection or not self.db_connection.is_connected():
            print("Erro: Conexão com o banco de dados não está ativa.")
            return False
        
        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = "DELETE FROM users WHERE id = %s"
            self.cursor.execute(query, (user_id,))
            
            # Confirma a operação de exclusão no banco de dados
            self.db_connection.commit()
            print(f"Usuário com ID {user_id} excluído com sucesso.")
            return True

        except mysql.connector.Error as err:
            print(f"Erro ao tentar excluir usuário: {err}")
            # Desfaz a operação em caso de erro
            self.db_connection.rollback()
            return False
        finally:
            # Nota: O ideal é que a conexão seja fechada na classe principal,
            # ou após várias operações para evitar abrir e fechar a todo momento.
            # Por isso, o 'pass' aqui.
            pass




    def update_user(self, user_id, nome, email, empresa, perfil):
        """
        Atualiza os dados de um usuário existente no banco de dados.

        Args:
            user_id (int): ID do usuário a ser atualizado.
            nome (str): Novo nome do usuário.
            email (str): Novo email do usuário.
            empresa (str): Nova empresa do usuário.
            perfil (str): Novo perfil do usuário.

        Returns:
            bool: True em caso de sucesso, False em caso de falha.
        """
        if not self.db_connection or not self.db_connection.is_connected():
            print("Erro: Conexão com o banco de dados não está ativa.")
            return False

        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = """
                UPDATE users
                SET nome = %s, email = %s, empresa = %s, role = %s
                WHERE id = %s
            """
            self.cursor.execute(query, (nome, email, empresa, perfil, user_id))
            self.db_connection.commit()
            print(f"Usuário com ID {user_id} atualizado com sucesso.")
            return True

        except mysql.connector.Error as err:
            print(f"Erro ao atualizar usuário: {err}")
            self.db_connection.rollback()
            return False

        finally:
            # Mantém a conexão ativa para outras operações
            pass


    def close(self):
        self.db_connector.close_connection()