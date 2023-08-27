from flask import render_template,send_from_directory
from app import app_app
import os
@app_app.route('/img/products/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('static/img/products'), imagen)


@app_app.route('/img/page/<imagen>')
def img_page(imagen):
    print(imagen)
    return send_from_directory(os.path.join('static/img/page'), imagen)


@app_app.route('/img/temp/<imagen>')
def img_temp(imagen):
    print(imagen)
    return send_from_directory(os.path.join('static/img/temp'), imagen)

@app_app.route('/img/users/<imagen>')
def img_users(imagen):
    print(imagen)
    return send_from_directory(os.path.join('static/img/users'), imagen)

@app_app.route("/css/<archivocss>")
def css_link(archivocss):
    return send_from_directory(os.path.join('static/css'), archivocss)


@app_app.route("/js/<archivojs>")
def js_link(archivojs):
    return send_from_directory(os.path.join('static/js'), archivojs)


@app_app.route("/admin/informes/<archivoxlwt>")
def informes_descargar(archivoxlwt):
    return send_from_directory(os.path.join('static/informes'), archivoxlwt)

