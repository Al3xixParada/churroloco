from flask import render_template, session, request, redirect
from sitio import sitio_app
from app.config import mysql
from collections import defaultdict
from datetime import datetime


@sitio_app.route('/pedidos')
def pedidos():
    if "usuario" not in session:
        return redirect("/admin/login")

    # Conectarse a la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Consulta SQL para obtener los pedidos activos de cada mesa
    sql_pedidos_activos = """
    SELECT pd.numero_mesa, p.nombre, p.precio, pd.cantidad
    FROM mesas m
    LEFT JOIN pedido pd ON m.numero_mesa = pd.numero_mesa
    LEFT JOIN productos p ON pd.id_producto = p.id
    WHERE pd.estado = 'Seleccionado'
    ORDER BY m.numero_mesa, p.nombre
    """

    cursor.execute(sql_pedidos_activos)
    pedidos_activos = cursor.fetchall()

    conexion.close()

    return render_template("sitio/pedidos.html", pedidos_activos=pedidos_activos)


@sitio_app.route('/facturas')
def facturas():
    if "usuario" not in session:
        return redirect("/admin/login")

    # Conectarse a la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Realiza la consulta SQL para obtener las facturas con detalles de productos en estado "Pago"
    cursor.execute("""
    SELECT pd.fecha, pd.numero_mesa, p.nombre, pd.cantidad, p.precio
    FROM pedido pd
    JOIN productos p ON pd.id_producto = p.id
    WHERE pd.estado = 'Pago'
    ORDER BY pd.fecha
    """)

    resultados = cursor.fetchall()

    # ... Tu código previo ...

    facturas_por_pedido = defaultdict(lambda: defaultdict(list))  # Usamos un diccionario anidado

    for resultado in resultados:
        fecha_pago_str = resultado[0]  # Obtiene la cadena de texto de la fecha
        fecha_pago = datetime.strptime(fecha_pago_str, "%d/%m/%Y %H:%M:%S")  # Convierte a datetime
        fecha_pago_formateada = fecha_pago.strftime("%d/%m/%Y")  # Formatea la fecha como cadena de texto

        # Obtén los otros datos, incluyendo detalle[5] (que llamaremos grupo)
        numero_mesa = resultado[1]
        nombre_producto = resultado[2]
        cantidad = resultado[3]
        precio = resultado[4]
        grupo = resultado[0]

        # Calcula el total para esta factura
        total_factura = cantidad * precio

        # Organiza los detalles en grupos dentro de la fecha
        facturas_por_pedido[fecha_pago_formateada][grupo].append((numero_mesa, nombre_producto, cantidad, precio, total_factura))
        
    # ... Resto de tu código ...


    return render_template("sitio/facturas.html", facturas_por_pedido=facturas_por_pedido)







@sitio_app.route('/mesa_seleccionada/<vista>/borrar', methods=['POST'])
def eliminar_carrito(vista):
    if "usuario" not in session:
        return redirect("/admin/login")

    vista_numero = int(vista)
    id_carrito = int(request.form['id_carrito'])
    id_producto = int(request.form['id_producto'])

    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Consulta SQL para obtener la cantidad del producto en el carrito
    sql_cantidad_carrito = "SELECT cantidad FROM pedido WHERE id_carrito = %s"
    cursor.execute(sql_cantidad_carrito, (id_carrito,))
    cantidad_carrito = cursor.fetchone()[0]

    # Consulta SQL para obtener la cantidad_existente actual del producto en la tabla productos
    sql_cantidad_existente = "SELECT cantidad_existente FROM productos WHERE id = %s"
    cursor.execute(sql_cantidad_existente, (id_producto,))
    cantidad_existente = cursor.fetchone()[0]

    # Calcular la nueva cantidad_existente luego de cancelar el pedido
    nueva_cantidad_existente = cantidad_existente + cantidad_carrito

    # Actualizar la cantidad_existente en la tabla productos
    sql_actualizar_cantidad_existente = "UPDATE productos SET cantidad_existente = %s WHERE id = %s"
    cursor.execute(sql_actualizar_cantidad_existente, (nueva_cantidad_existente, id_producto))
    conexion.commit()

    # Eliminar el pedido del carrito
    sql_eliminar_carrito = "DELETE FROM pedido WHERE id_carrito = %s"
    cursor.execute(sql_eliminar_carrito, (id_carrito,))
    conexion.commit()

    # Cerrar la conexión a la base de datos
    conexion.close()

    return redirect(f"/mesa_seleccionada/{vista_numero}")
