from models.auth import DatabaseConnection
import mysql.connector

# Import do sistema de logging
from utils.logger import get_logger

logger = get_logger('database.user_manager')

class UserManager:
    def __init__(self):
        self.db_connector = DatabaseConnection()
        self.db_connection = self.db_connector.get_connection()
        self.cursor = None
        if self.db_connection:
            self.cursor = self.db_connection.cursor(dictionary=True)
            logger.debug("✅ UserManager inicializado com sucesso")
        else:
            logger.error("❌ UserManager: Falha ao obter conexão com banco de dados")

    def find_user_by_email(self, email):
        if not self.db_connection or not self.db_connection.is_connected():
            logger.error(f"❌ Conexão com banco não está ativa ao buscar usuário: {email}")
            return None

        try:
            query = "SELECT * FROM users WHERE email = %s"
            logger.debug(f"🔍 Executando query: {query} | Param: {email}")
            self.cursor.execute(query, (email,))
            user = self.cursor.fetchone()

            if user:
                logger.debug(f"✅ Usuário encontrado: {email}")
            else:
                logger.debug(f"⚠️ Usuário não encontrado: {email}")

            return user

        except mysql.connector.Error as err:
            logger.error(f"💥 Erro ao buscar usuário {email}: {err}", exc_info=True)
            return None
        finally:
            # Feche a conexão do cursor após a operação, mas não a conexão principal
            if self.cursor:
                self.cursor.close()
                self.cursor = None


    def register_user(self, name, email, telefone, password, role):
        """
        Registers a new user in the database.
        Agora SEM campos de empresa (esses campos foram movidos para a tabela empresas).

        Args:
            name (str): User's full name.
            email (str): User's email address.
            telefone (str): User's phone number.
            password (str): User's plain-text password.
            role (str): User's role (e.g., 'admin', 'user').

        Returns:
            int|bool: user_id on success, False otherwise.
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
                INSERT INTO users (nome, email, telefone, password, role)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (name, email, telefone, hashed_password, role))
            self.db_connection.commit()

            # Retorna o ID do usuário criado
            user_id = self.cursor.lastrowid
            print(f"[DEBUG] Usuário '{name}' criado com sucesso. ID: {user_id}")
            return user_id

        except mysql.connector.Error as err:
            print(f"Erro ao cadastrar usuário: {err}")
            self.db_connection.rollback()
            return False
        finally:
            # It's better to keep the cursor open
            pass


    def get_all_users(self):
        """Retorna todos os usuários (sem campos de empresa)."""
        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = "SELECT id, nome, email, telefone, role, created_at FROM users"
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




    def update_user(self, user_id, nome, email, telefone, perfil):
        """
        Atualiza os dados de um usuário existente no banco de dados.
        Agora SEM campo empresa.

        Args:
            user_id (int): ID do usuário a ser atualizado.
            nome (str): Novo nome do usuário.
            email (str): Novo email do usuário.
            telefone (str): Novo telefone do usuário.
            perfil (str): Novo perfil do usuário (role).

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
                SET nome = %s, email = %s, telefone = %s, role = %s
                WHERE id = %s
            """
            self.cursor.execute(query, (nome, email, telefone, perfil, user_id))
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

    def update_user_password(self, user_id, new_password):
        """
        Atualiza apenas a senha de um usuário existente no banco de dados.

        Args:
            user_id (int): ID do usuário a ter a senha atualizada.
            new_password (str): Nova senha em texto plano (será hasheada).

        Returns:
            bool: True em caso de sucesso, False em caso de falha.
        """
        if not self.db_connection or not self.db_connection.is_connected():
            print("Erro: Conexão com o banco de dados não está ativa.")
            return False

        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            # Hash da nova senha
            from controllers.auth.hash import hash_senha_sha256
            hashed_password = hash_senha_sha256(new_password)

            query = """
                UPDATE users
                SET password = %s
                WHERE id = %s
            """
            self.cursor.execute(query, (hashed_password, user_id))
            self.db_connection.commit()
            print(f"Senha do usuário com ID {user_id} atualizada com sucesso.")
            return True

        except mysql.connector.Error as err:
            print(f"Erro ao atualizar senha do usuário: {err}")
            self.db_connection.rollback()
            return False

        finally:
            # Mantém a conexão ativa para outras operações
            pass


    # ============================
    # MÉTODOS PARA GERENCIAR RELACIONAMENTO USER-EMPRESA (MUITOS PARA MUITOS)
    # ============================

    def vincular_user_empresa(self, user_id, empresa_id):
        """
        Cria um vínculo entre um usuário e uma empresa na tabela user_empresa.

        Args:
            user_id (int): ID do usuário
            empresa_id (int): ID da empresa

        Returns:
            bool: True em caso de sucesso, False em caso de falha
        """
        if not self.db_connection or not self.db_connection.is_connected():
            print("Erro: Conexão com o banco de dados não está ativa.")
            return False

        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            # Verifica se o vínculo já existe
            check_query = "SELECT * FROM user_empresa WHERE user_id = %s AND empresa_id = %s"
            self.cursor.execute(check_query, (user_id, empresa_id))
            if self.cursor.fetchone():
                print(f"[DEBUG] Vínculo entre user_id={user_id} e empresa_id={empresa_id} já existe.")
                return True

            # Cria o vínculo
            insert_query = "INSERT INTO user_empresa (user_id, empresa_id) VALUES (%s, %s)"
            self.cursor.execute(insert_query, (user_id, empresa_id))
            self.db_connection.commit()
            print(f"[DEBUG] Vínculo criado: user_id={user_id} <-> empresa_id={empresa_id}")
            return True

        except mysql.connector.Error as err:
            print(f"Erro ao vincular usuário e empresa: {err}")
            self.db_connection.rollback()
            return False

    def desvincular_user_empresa(self, user_id, empresa_id):
        """
        Remove o vínculo entre um usuário e uma empresa.

        Args:
            user_id (int): ID do usuário
            empresa_id (int): ID da empresa

        Returns:
            bool: True em caso de sucesso, False em caso de falha
        """
        if not self.db_connection or not self.db_connection.is_connected():
            print("Erro: Conexão com o banco de dados não está ativa.")
            return False

        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = "DELETE FROM user_empresa WHERE user_id = %s AND empresa_id = %s"
            self.cursor.execute(query, (user_id, empresa_id))
            self.db_connection.commit()
            print(f"[DEBUG] Vínculo removido: user_id={user_id} <-> empresa_id={empresa_id}")
            return True

        except mysql.connector.Error as err:
            print(f"Erro ao desvincular usuário e empresa: {err}")
            self.db_connection.rollback()
            return False

    def get_empresas_do_usuario(self, user_id):
        """
        Retorna todas as empresas vinculadas a um usuário.

        Args:
            user_id (int): ID do usuário

        Returns:
            list: Lista de empresas vinculadas ao usuário
        """
        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = """
                SELECT e.*
                FROM empresas e
                INNER JOIN user_empresa ue ON e.id = ue.empresa_id
                WHERE ue.user_id = %s
                ORDER BY e.nome ASC
            """
            self.cursor.execute(query, (user_id,))
            empresas = self.cursor.fetchall()
            return empresas

        except mysql.connector.Error as err:
            print(f"Erro ao buscar empresas do usuário: {err}")
            return []

    def get_usuarios_da_empresa(self, empresa_id):
        """
        Retorna todos os usuários vinculados a uma empresa.

        Args:
            empresa_id (int): ID da empresa

        Returns:
            list: Lista de usuários vinculados à empresa
        """
        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = """
                SELECT u.id, u.nome, u.email, u.telefone, u.role, u.created_at
                FROM users u
                INNER JOIN user_empresa ue ON u.id = ue.user_id
                WHERE ue.empresa_id = %s
                ORDER BY u.nome ASC
            """
            self.cursor.execute(query, (empresa_id,))
            users = self.cursor.fetchall()
            return users

        except mysql.connector.Error as err:
            print(f"Erro ao buscar usuários da empresa: {err}")
            return []

    def get_user_by_id(self, user_id):
        """
        Busca um usuário pelo ID.

        Args:
            user_id (int): ID do usuário

        Returns:
            dict|None: Dados do usuário ou None se não encontrado
        """
        try:
            if not self.cursor:
                self.cursor = self.db_connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE id = %s"
            self.cursor.execute(query, (user_id,))
            user = self.cursor.fetchone()
            return user

        except mysql.connector.Error as err:
            print(f"Erro ao buscar usuário por ID: {err}")
            return None

    def close(self):
        self.db_connector.close_connection()