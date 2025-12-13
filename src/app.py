from flask import Flask, Blueprint, request
import sys
import traceback

# Import do sistema de logging
from utils.logger import get_logger, log_error, app_logger

# Import Páginas
from pages.public.index import app_index
from pages.admin.admin import admin_bp
from pages.user.user import user_bp

app = Flask(__name__)
app.secret_key = 'minhasecretkeyemuitodificil'

# Configurar logging do Flask para usar nosso logger
logger = get_logger('flask')
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

# Add Páginas
app.register_blueprint(app_index)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

# Handler global para erros não tratados
@app.errorhandler(Exception)
def handle_exception(e):
    """Captura todos os erros não tratados e registra no log"""
    # Log completo do erro
    logger.error(f"💥 ERRO NÃO TRATADO: {str(e)}")
    logger.error(f"📍 Rota: {request.method} {request.path}")
    logger.error(f"🔍 Query String: {request.query_string.decode()}")
    logger.error(f"📦 Form Data: {request.form}")
    logger.error(f"🌐 IP: {request.remote_addr}")
    logger.error(f"📋 Stacktrace completo:")
    logger.error(traceback.format_exc())

    # Retornar erro 500
    return f"Internal Server Error - Erro registrado nos logs. ID: {id(e)}", 500

# Handler para 404
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 - Página não encontrada: {request.method} {request.path}")
    return "Página não encontrada", 404

# Hook antes de cada requisição
@app.before_request
def log_request():
    """Loga todas as requisições"""
    # Não logar requisições de arquivos estáticos para não poluir o log
    if not request.path.startswith('/static'):
        logger.debug(f"🌐 [{request.method}] {request.path} - IP: {request.remote_addr}")

if __name__ == '__main__':
    app_logger.info("🚀 Iniciando servidor Flask...")
    app_logger.info(f"🌍 Host: 0.0.0.0")
    app_logger.info(f"🔧 Debug: True")

    try:
        app.run(debug=True, host='0.0.0.0')
    except Exception as e:
        app_logger.critical(f"💀 ERRO CRÍTICO ao iniciar servidor: {str(e)}")
        app_logger.critical(traceback.format_exc())
        sys.exit(1)