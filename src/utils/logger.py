"""
Sistema de Logging Centralizado
Autor: Sistema Ways Solution Hub
Data: 2025-12-15

Este módulo fornece um sistema de logging profissional com:
- Rotação automática de arquivos de log
- Múltiplos níveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Formatação padronizada com timestamp
- Logs organizados por data
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    """
    Classe para gerenciar o sistema de logging da aplicação.
    """

    _loggers = {}

    @staticmethod
    def get_logger(name='app', log_level=logging.INFO):
        """
        Obtém ou cria um logger configurado.

        Args:
            name (str): Nome do logger (geralmente o nome do módulo)
            log_level (int): Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            logging.Logger: Instância configurada do logger
        """

        # Retorna logger existente se já foi criado
        if name in Logger._loggers:
            return Logger._loggers[name]

        # Cria novo logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        # Remove handlers existentes para evitar duplicação
        logger.handlers = []

        # Define diretório de logs
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # Define formato do log
        log_format = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler para arquivo com rotação (10MB por arquivo, mantém 5 backups)
        log_file = os.path.join(log_dir, f'{name}.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        # Handler para console (opcional - apenas em desenvolvimento)
        # Descomente as linhas abaixo se quiser ver logs no console também
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.WARNING)  # Apenas warnings e erros no console
        # console_handler.setFormatter(log_format)
        # logger.addHandler(console_handler)

        # Salva logger no cache
        Logger._loggers[name] = logger

        return logger

    @staticmethod
    def setup_app_logger(app=None):
        """
        Configura o logger principal da aplicação Flask.

        Args:
            app: Instância do Flask (opcional)
        """
        logger = Logger.get_logger('app', log_level=logging.INFO)

        if app:
            # Desabilita o logger padrão do Flask para evitar duplicação
            app.logger.handlers = []

            # Redireciona logs do Flask para nosso logger
            app.logger.addHandler(logger.handlers[0])
            app.logger.setLevel(logging.INFO)

        logger.info("="*80)
        logger.info("Sistema de Logging Inicializado")
        logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)

        return logger


# Atalhos para uso direto (facilita a migração dos prints)
def get_logger(name='app'):
    """Atalho para obter um logger"""
    return Logger.get_logger(name)


# Logger padrão da aplicação
app_logger = Logger.get_logger('app')
