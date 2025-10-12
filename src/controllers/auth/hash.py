import hashlib

def hash_senha_sha256(senha):
    """
    Gera um hash SHA256 de uma senha.
    
    Args:
        senha (str): A senha em texto puro.
    
    Returns:
        str: O hash da senha em formato hexadecimal.
    """
    # Cria um objeto hash SHA256
    hash_obj = hashlib.sha256()
    
    # Codifica a senha em bytes e a atualiza no objeto hash
    hash_obj.update(senha.encode('utf-8'))
    
    # Retorna o hash em formato hexadecimal
    return hash_obj.hexdigest()