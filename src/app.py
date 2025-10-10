from flask import Flask, Blueprint, url_for

# Import Páginas
from pages.public.index.index import app_index

app = Flask(__name__)
app.secret_key = 'minhasecretkeyemuitodificil'

# Add Páginas
app.register_blueprint(app_index)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')