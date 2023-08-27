from flask import Flask
from sitio.routes import *
from admin import admin_app
from app.routes import *

app = Flask(__name__)
app.secret_key = "Churrooo"

# Registrar los Blueprints
app.register_blueprint(sitio_app)
app.register_blueprint(admin_app, url_prefix='/admin/')
app.register_blueprint(app_app)

if __name__ == '__main__':
    app.run(debug=True)
