from flask import Flask, Blueprint

# Import Páginas
from pages.public.index import app_index
from pages.admin.admin import admin_bp

app = Flask(__name__)
app.secret_key = 'minhasecretkeyemuitodificil'

# Add Páginas
app.register_blueprint(app_index)
app.register_blueprint(admin_bp)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')