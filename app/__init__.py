#app/__init__.py
from flask import Blueprint

app_app = Blueprint('app', __name__)

from app import routes  # Importa las rutas del Blueprint
