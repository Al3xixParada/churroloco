from flask import render_template, session, redirect, request
from sitio import sitio_app
from app.config import mysql

# Función para obtener los números de mesa permitidos desde la base de datos
def obtener_numeros_de_mesa_permitidos():
    consulta_sql = "SELECT `numero_mesa` FROM `mesas`"
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(consulta_sql)
    numeros_permitidos = [fila[0] for fila in cursor.fetchall()]
    conexion.close()
    return numeros_permitidos

@sitio_app.route('/mesa_seleccionada/<vista>', methods=['GET', 'POST'])
def dynamic_route(vista):
    if "usuario" not in session:
        return redirect("/admin/login")
    
    vista_numero = int(vista)
    numeros_permitidos = obtener_numeros_de_mesa_permitidos()

    sql_tipo_producto = "SELECT * FROM `tipo_producto`"
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql_tipo_producto)
    tipo_producto = cursor.fetchall()
    conexion.close()

    sql_mesa = "SELECT * FROM `mesas` WHERE `numero_mesa` = %s"
    datos_mesa = (vista_numero,)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql_mesa, datos_mesa)
    infom_mesa = cursor.fetchone()
    conexion.close()

    sql_productos = "SELECT * FROM `productos`"
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql_productos)
    productos = cursor.fetchall()
    
    
    usuario_nombre = session['users']
    sql_usuario_id = "SELECT id FROM usuario WHERE usuario = %s"
    cursor.execute(sql_usuario_id, (usuario_nombre,))
    id_usuario = cursor.fetchone()[0]
    

    carritos = []
    resultado_final = 0

    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    sql_productos_seleccionados = """
        SELECT pedido.id_carrito, productos.id AS id_producto, productos.nombre, productos.descripcion, productos.precio, pedido.cantidad
        FROM productos
        JOIN pedido ON productos.id = pedido.id_producto
        WHERE pedido.estado = 'Seleccionado'
        AND pedido.id_usuario = %s AND pedido.numero_mesa=%s
    """
    cursor.execute(sql_productos_seleccionados, (id_usuario,vista_numero,))
    carritos = cursor.fetchall()

    resultado_final = sum(carrito[4] * carrito[5] for carrito in carritos)

    cursor.close()
    conexion.close()


    if request.method == 'POST':
        datos_formulario = request.form
                
        conexion = mysql.connect()
        cursor = conexion.cursor()

        productos_seleccionados = []
        for key, value in datos_formulario.items():
            if key.startswith("cantidad_"):
                id_producto = key.replace("cantidad_", "")
                cantidad = int(value)

                if cantidad > 0:
                    productos_seleccionados.append((id_producto, cantidad))

        for id_producto, cantidad in productos_seleccionados:
            sql_pedido = "SELECT id_carrito, cantidad FROM `pedido` WHERE `id_producto` = %s AND `id_usuario` = %s AND `numero_mesa` = %s AND `estado` = 'Seleccionado'"
            datos_pedido = (id_producto, id_usuario, vista_numero)
            cursor.execute(sql_pedido, datos_pedido)
            registro_existente = cursor.fetchone()

            if registro_existente:
                id_carrito = registro_existente[0]
                nueva_cantidad_carrito = registro_existente[1] + cantidad
                sql_update_pedido = "UPDATE `pedido` SET `cantidad` = %s, `fecha` = %s WHERE `id_carrito` = %s"
                datos_update_pedido = (nueva_cantidad_carrito, "", id_carrito)
                cursor.execute(sql_update_pedido, datos_update_pedido)
                conexion.commit()
                    
            else:
                sql_insert_pedido = "INSERT INTO `pedido` (`id_carrito`, `fecha`, `id_producto`, `id_usuario`, `cantidad`, `estado`, `numero_mesa`) VALUES (NULL, %s, %s, %s, %s, %s, %s)"
                datos_insert_pedido = ("", id_producto, id_usuario, cantidad, "Seleccionado", vista_numero)
                cursor.execute(sql_insert_pedido, datos_insert_pedido)
                conexion.commit()
                
            # Ahora, actualiza la cantidad en la tabla `productos`
            sql_cantidad_producto = "SELECT cantidad_existente FROM `productos` WHERE `id` = %s"
            cursor.execute(sql_cantidad_producto, (id_producto,))
            cantidad_actual_producto = cursor.fetchone()[0]

            nueva_cantidad_producto = cantidad_actual_producto - cantidad

            sql_update_producto = "UPDATE `productos` SET `cantidad_existente` = %s WHERE `id` = %s"
            cursor.execute(sql_update_producto, (nueva_cantidad_producto, id_producto))

            conexion.commit()

        cursor.close()
        conexion.close()

        # Redirige al usuario de nuevo a la misma página para que el formulario esté en blanco
        return redirect(request.url)




    if vista_numero in numeros_permitidos:
        return render_template('sitio/mesa_seleccionada.html', tipo_producto=tipo_producto, infom_mesas=infom_mesa, productos=productos, carritos=carritos, resultado_final=resultado_final)
    else:
        return render_template('sitio/404.html')
