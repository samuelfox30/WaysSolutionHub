from flask import Flask, Blueprint

# Import Páginas
from pages.public.index import app_index
from pages.admin.admin import admin_bp
from pages.user.user import user_bp

# Import Sistema de Logging
from utils.logger import Logger

app = Flask(__name__)
app.secret_key = 'minhasecretkeyemuitodificil'

# Inicializar sistema de logging
logger = Logger.setup_app_logger(app)
# Add Páginas
app.register_blueprint(app_index)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

logger.info("Aplicação Flask inicializada com sucesso")
logger.info("Blueprints registrados: index, admin, user")

if __name__ == '__main__':
    logger.info("Iniciando servidor Flask em modo debug")
    logger.info("Host: 0.0.0.0, Debug: True")
    app.run(debug=True, host='0.0.0.0')


# oii