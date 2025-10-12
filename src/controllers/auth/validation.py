import re

def validar_email(email):
    if not isinstance(email, str) or not email:
        return False
    
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return re.match(regex, email) is not None

def validar_senha(senha):
    if not isinstance(senha, str) or not senha:
        return False

    if len(senha) < 4 or len(senha) > 128:
        return False
        
    return True

def validar_senha_cadastro(senha):
    # 1. Verifica se a entrada é uma string
    if not isinstance(senha, str):
        return False
    
    # 2. Verifica se o comprimento é de no mínimo 8 caracteres
    if len(senha) < 8:
        return False
    
    # 3. Verifica se tem pelo menos uma letra maiúscula
    tem_maiuscula = any(char.isupper() for char in senha)
    if not tem_maiuscula:
        return False

    # 4. Verifica se tem pelo menos uma letra minúscula
    tem_minuscula = any(char.islower() for char in senha)
    if not tem_minuscula:
        return False
    
    # 5. Verifica se tem pelo menos um número
    tem_numero = any(char.isdigit() for char in senha)
    if not tem_numero:
        return False
    
    # 6. Verifica se tem pelo menos um símbolo (caractere não alfanumérico)
    tem_simbolo = any(not char.isalnum() for char in senha)
    if not tem_simbolo:
        return False
    
    # Se todas as condições acima forem atendidas, a senha é válida
    return True

def validar_nome(nome):
    if not isinstance(nome, str) or not nome.strip():
        return False
        
    if len(nome.strip()) < 2 or len(nome.strip()) > 100:
        return False
        
    return True


def validar_tipo_usuario(user_type):
    if not isinstance(user_type, str):
        return False
        
    if user_type.lower() == 'admin' or user_type.lower() == 'user':
        return True
        
    return False


def validar_nome_empresa(nome_empresa):
    """
    Valida o formato do nome da empresa.

    Args:
        nome_empresa (str): O nome da empresa a ser validado.

    Returns:
        bool: True se o nome for válido, False caso contrário.
    """
    if not isinstance(nome_empresa, str) or not nome_empresa.strip():
        return False
        
    # Regex que permite letras, números, espaços, pontos, hífens e vírgulas.
    # Exemplo: "Minha Empresa Ltda.", "Tech-Solutions, Inc."
    regex = r"^[a-zA-Z0-9\s.,-]+$"
    
    # Limita o tamanho para evitar strings muito longas
    if len(nome_empresa) > 100:
        return False

    return re.match(regex, nome_empresa) is not None


def validar_telefone(telefone):
    """
    Valida o formato de um número de telefone brasileiro.

    Args:
        telefone (str): O número de telefone a ser validado.

    Returns:
        bool: True se o telefone for válido, False caso contrário.
    """
    if not isinstance(telefone, str) or not telefone.strip():
        return False
        
    # Regex que permite telefones com ou sem DDD, com 8 ou 9 dígitos e com ou sem formatação.
    # Ex: (99) 99999-9999, 99 999999999, 99999999999
    # Garante que o número tenha de 10 a 11 dígitos, após remover caracteres não numéricos.
    telefone_limpo = re.sub(r'\D', '', telefone)
    
    if not (10 <= len(telefone_limpo) <= 11):
        return False
        
    return True

def validar_seguimento(seguimento):
    """
    Valida o nome do seguimento da empresa.

    Args:
        seguimento (str): O nome do seguimento.

    Returns:
        bool: True se o seguimento for válido, False caso contrário.
    """
    # Verifica se a entrada é uma string e se não está vazia (apenas espaços em branco)
    if not isinstance(seguimento, str) or not seguimento.strip():
        return False
        
    # Limita o tamanho para evitar strings muito longas.
    if len(seguimento) > 50:
        return False

    # Regex que permite letras, números, espaços e hífens.
    regex = r"^[a-zA-Z0-9\s-]+$"
    
    # Retorna True se o segmento corresponder à regex, False caso contrário.
    return re.match(regex, seguimento) is not None