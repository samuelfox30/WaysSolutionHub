"""
Sistema de Logging Centralizado
================================

Configuração de logs para toda a aplicação.
Registra erros, tentativas de login, conexões com banco, etc.

Níveis de log:
- DEBUG: Informações detalhadas para diagnóstico
- INFO: Confirmações de que tudo está funcionando
- WARNING: Algo inesperado mas não crítico
- ERROR: Erro que impediu uma funcionalidade
- CRITICAL: Erro grave que pode parar o sistema
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Diretório de logs (relativo à raiz do projeto)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

# Criar diretório se não existir
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Arquivo de log principal
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Formato do log
LOG_FORMAT = '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(name='WaysSolutionHub', level=logging.DEBUG):
    """
    Configura e retorna um logger com handlers para arquivo e console.

    Args:
        name (str): Nome do logger
        level: Nível mínimo de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Logger configurado
    """
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Handler para arquivo (com rotação)
    # Máximo 10MB por arquivo, mantém 5 backups
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler para console (apenas INFO e acima)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Adicionar handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name=None):
    """
    Retorna um logger configurado.

    Args:
        name (str): Nome do módulo/componente (opcional)

    Returns:
        logging.Logger: Logger configurado
    """
    if name:
        return logging.getLogger(f'WaysSolutionHub.{name}')
    return logging.getLogger('WaysSolutionHub')


# Logger padrão da aplicação
app_logger = setup_logger()


# Funções auxiliares para logs específicos
def log_login_attempt(email, success=False, error=None):
    """Loga tentativa de login"""
    logger = get_logger('auth')
    if success:
        logger.info(f"✅ Login bem-sucedido: {email}")
    else:
        logger.warning(f"❌ Login falhou: {email} - Erro: {error}")


def log_database_connection(host, database, success=True, error=None):
    """Loga conexão com banco de dados"""
    logger = get_logger('database')
    if success:
        logger.info(f"🗄️ Conectado ao banco: {database}@{host}")
    else:
        logger.error(f"🗄️ Falha ao conectar: {database}@{host} - Erro: {error}")


def log_database_query(query, params=None, error=None):
    """Loga queries do banco de dados"""
    logger = get_logger('database')
    if error:
        logger.error(f"🔍 Erro na query: {query[:100]}... - Erro: {error}")
    else:
        logger.debug(f"🔍 Query executada: {query[:100]}...")


def log_route_access(route, method, user=None):
    """Loga acesso a rotas"""
    logger = get_logger('routes')
    user_info = f" por {user}" if user else ""
    logger.info(f"🌐 [{method}] {route}{user_info}")


def log_error(error, context=None):
    """Loga erro com contexto"""
    logger = get_logger('error')
    context_info = f" | Contexto: {context}" if context else ""
    logger.error(f"💥 Erro: {str(error)}{context_info}", exc_info=True)


def log_session_created(user_email, session_id):
    """Loga criação de sessão"""
    logger = get_logger('session')
    logger.info(f"🔐 Sessão criada: {user_email} (ID: {session_id[:8]}...)")


def log_session_destroyed(user_email):
    """Loga destruição de sessão"""
    logger = get_logger('session')
    logger.info(f"🔓 Sessão destruída: {user_email}")


# Log de inicialização
app_logger.info("=" * 80)
app_logger.info(f"🚀 Sistema de Logging Inicializado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
app_logger.info(f"📁 Arquivo de log: {LOG_FILE}")
app_logger.info("=" * 80)
