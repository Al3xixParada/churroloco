from flask import Blueprint

admin_app = Blueprint('admin', __name__)

from admin import routes
from admin import login
from admin import mesas
