from flask import render_template,redirect
from sitio import sitio_app

@sitio_app.route('/')
def index():
    
    return redirect('admin/login')  # Asegúrate de que la ruta de la plantilla sea correcta
