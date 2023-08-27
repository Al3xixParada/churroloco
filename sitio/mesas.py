from flask import render_template,session,request,redirect
from sitio import sitio_app

from app.config import app, mysql

@sitio_app.route('/mesas')
def mesas():
    if "usuario" not in session:
        return redirect("/admin/login")
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `mesas` ORDER BY `mesas`.`numero_mesa` ASC")
    mesas = cursor.fetchall()
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT DISTINCT numero_mesa FROM `pedido` WHERE estado = 'Seleccionado'")
    mesas_con_pedidos = [fila[0] for fila in cursor.fetchall()]
    
    # Construir una lista de mesas ocupadas basadas en las mesas con pedidos
    mesas_ocupadas = [mesa[0] for mesa in mesas if mesa[1] in mesas_con_pedidos]
    
    if mesas_ocupadas:
        # Actualiza las mesas ocupadas en la base de datos
        sql_update_mesas_ocupadas = "UPDATE `mesas` SET `estado` = %s WHERE `id` IN %s"
        datos_update_mesas_ocupadas = ("Ocupado", tuple(mesas_ocupadas))
        cursor.execute(sql_update_mesas_ocupadas, datos_update_mesas_ocupadas)
        conexion.commit()
    
    # Actualiza el estado de las mesas restantes (las que no tienen pedidos) en la base de datos
    sql_update_mesas_disponibles = "UPDATE `mesas` SET `estado` = %s WHERE `id` NOT IN %s"
    datos_update_mesas_disponibles = ("Disponible", tuple(mesas_ocupadas))
    cursor.execute(sql_update_mesas_disponibles, datos_update_mesas_disponibles)
    conexion.commit()
    
    return render_template('sitio/mesas.html', mesas=mesas)
