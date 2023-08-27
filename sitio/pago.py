from flask import render_template, session, request, redirect
from sitio import sitio_app
from app.config import mysql
from datetime import datetime

@sitio_app.route('/mesa_seleccionada/<vista>/pago',methods=['POST'])
def pago(vista):
    if "usuario" not in session:
        return redirect("/admin/login")

    vista_numero = int(vista)

    # Obtén la fecha y hora actual en el formato deseado
    now = datetime.now()
    fecha_pago = now.strftime("%d/%m/%Y %H:%M:%S")

    # Conecta a la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Actualiza el estado de los pedidos de la mesa a "pago" y agrega la fecha de pago
    sql_actualizar_estado = "UPDATE pedido SET estado = 'Pago', fecha = %s WHERE numero_mesa = %s"
    cursor.execute(sql_actualizar_estado, (fecha_pago, vista))
    conexion.commit()

    # Cierra la conexión a la base de datos
    cursor.close()
    conexion.close()

    return redirect(f"/mesa_seleccionada/{vista_numero}")
