#sitio/__init__.py
from flask import Blueprint

sitio_app = Blueprint('sitio', __name__)

from sitio import routes  # Importa las rutas del Blueprint
from sitio import mesas
from sitio import mesas_numero
from sitio import pedidos
from sitio import pago