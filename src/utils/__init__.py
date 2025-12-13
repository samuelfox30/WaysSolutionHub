"""
Utils Package
=============

Utilitários da aplicação.
"""

from .logger import (
    setup_logger,
    get_logger,
    log_login_attempt,
    log_database_connection,
    log_database_query,
    log_route_access,
    log_error,
    log_session_created,
    log_session_destroyed,
    app_logger
)

__all__ = [
    'setup_logger',
    'get_logger',
    'log_login_attempt',
    'log_database_connection',
    'log_database_query',
    'log_route_access',
    'log_error',
    'log_session_created',
    'log_session_destroyed',
    'app_logger'
]
