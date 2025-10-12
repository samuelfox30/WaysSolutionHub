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

    def close(self):
        self.db_connector.close_connection()