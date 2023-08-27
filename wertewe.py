from flask import Flask, flash, render_template, request, redirect, session, send_file, send_from_directory
from flaskext.mysql import MySQL
from datetime import datetime
import os
import shutil
from werkzeug.utils import secure_filename
import xlwt
from flask import flash, get_flashed_messages
 
app = Flask(__name__)
app.secret_key = "Churrooo"
mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'sitio'
app.config['MYSQL_DATABASE_PORT'] = 3306
mysql.init_app(app)


@app.route('/img/products/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img/products'), imagen)


@app.route('/img/page/<imagen>')
def img_page(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img/page'), imagen)


@app.route('/img/temp/<imagen>')
def img_temp(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img/temp'), imagen)

@app.route('/img/users/<imagen>')
def img_users(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img/users'), imagen)

@app.route("/css/<archivocss>")
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'), archivocss)


@app.route("/js/<archivojs>")
def js_link(archivojs):
    return send_from_directory(os.path.join('templates/sitio/js'), archivojs)


@app.route("/admin/informes/<archivoxlwt>")
def informes_descargar(archivoxlwt):
    return send_from_directory(os.path.join('templates/admin/informes'), archivoxlwt)


@app.route('/')
def index():
    return render_template('sitio/index.html')


@app.route('/carrito')
def carrito():
    if "usuario" not in session:
        return redirect("/admin/login")

    # Conectarse a la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Obtener el id del usuario de la sesión
    usuario_nombre = session['users']
    sql_usuario_id = "SELECT id FROM usuario WHERE usuario = %s"
    cursor.execute(sql_usuario_id, (usuario_nombre,))
    id_usuario = cursor.fetchone()[0]

    # Consulta SQL para obtener los productos seleccionados por el usuario
    sql_productos_seleccionados = """
        SELECT carrito.id_carrito, productos.id AS id_producto, productos.nombre, productos.descripcion, productos.precio, carrito.cantidad
        FROM productos
        JOIN carrito ON productos.id = carrito.id_producto
        WHERE carrito.estado = 'Seleccionado'
        AND carrito.id_usuario = %s
    """
    cursor.execute(sql_productos_seleccionados, (id_usuario,))
    carritos = cursor.fetchall()

    # Calcular el resultado final (total de productos seleccionados por el usuario)
    resultado_final = sum(carrito[4] * carrito[5] for carrito in carritos)

    # Cerrar la conexión a la base de datos
    cursor.close()
    conexion.close()

    # Renderizar la plantilla HTML con los datos obtenidos
    return render_template('sitio/carrito.html', carritos=carritos, resultado_final=resultado_final)




@app.route('/comprar/carrito', methods=['POST'])
def agregar_carrito():
    if "usuario" not in session:
        return redirect("/admin/login")

    producto_id = int(request.form['txtid_producto'])
    usuario_nombre = request.form['nombre_usuario']
    cantidad_seleccionada = int(request.form['cantidad'])

    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Verificar si el producto ya existe en el carrito para el usuario específico
    sql = "SELECT id_carrito, cantidad FROM `carrito` WHERE `id_producto` = %s AND `id_usuario` = (SELECT id FROM `usuario` WHERE `usuario` = %s)"
    datos = (producto_id, usuario_nombre)
    cursor.execute(sql, datos)
    registro_existente = cursor.fetchone()

    if registro_existente:
        # Si el registro existe, actualizamos la cantidad en el carrito
        id_carrito = registro_existente[0]
        nueva_cantidad_carrito = registro_existente[1] + cantidad_seleccionada
        sql = "UPDATE `carrito` SET `cantidad` = %s, `fecha` = %s WHERE `id_carrito` = %s"
        datos = (nueva_cantidad_carrito, "", id_carrito)
    else:
        # Si el registro no existe, creamos uno nuevo en el carrito
        sql = "INSERT INTO `carrito` (`id_carrito`,`fecha`, `id_producto`, `id_usuario`, `cantidad`, `estado`) VALUES (NULL, %s, %s, (SELECT id FROM `usuario` WHERE `usuario` = %s), %s, %s)"
        datos = ("", producto_id, usuario_nombre, cantidad_seleccionada, "Seleccionado")

    # Ejecutar la consulta correspondiente (actualización o inserción)
    cursor.execute(sql, datos)

    # Actualizar la tabla "productos" restando la cantidad seleccionada por el usuario
    sql = "SELECT cantidad_existente FROM `productos` WHERE `id` = %s"
    cursor.execute(sql, (producto_id,))
    cantidad_actual_producto = cursor.fetchone()[0]

    nueva_cantidad_producto = cantidad_actual_producto - cantidad_seleccionada

    sql = "UPDATE `productos` SET `cantidad_existente` = %s WHERE `id` = %s"
    cursor.execute(sql, (nueva_cantidad_producto, producto_id))

    conexion.commit()
    conexion.close()

    return redirect("/productos")

@app.route('/pago')
def pago():
    return render_template('sitio/pago.html')


@app.route('/carrito/borrar', methods=['POST'])
def eliminar_carrito():
    if "usuario" not in session:
        return redirect("/admin/login")
    
    id_carrito = int(request.form['id_carrito'])
    id_producto = int(request.form['id_producto'])

    conexion = mysql.connect()
    cursor = conexion.cursor()

    id_producto = int(request.form['id_producto'])

    # Consulta SQL para obtener la cantidad del producto en el carrito
    sql_cantidad_carrito = "SELECT cantidad FROM carrito WHERE id_carrito = %s"
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
    sql_eliminar_carrito = "DELETE FROM carrito WHERE id_carrito = %s"
    cursor.execute(sql_eliminar_carrito, (id_carrito,))
    conexion.commit()

    # Cerrar la conexión a la base de datos

    return redirect("/carrito")




@app.route('/comprar', methods=['POST'])
def comprar():
    if "usuario" not in session:
        return redirect("/admin/login")
    
    _id = int(request.form['txtID'])
    sql = "SELECT * FROM `productos` WHERE `id` = %s"
    datos = (_id,)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    result = cursor.fetchall()
    conexion.commit()

    return render_template('sitio/comprar.html', result=result)


@app.route('/productos')
def productos():

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos` ORDER BY `productos`.`id` DESC")
    productos = cursor.fetchall()
    conexion.commit()
    print(productos)

    return render_template('sitio/productos.html', productos=productos)


@app.route('/productos/buscar', methods=['POST'])
def productos_buscar():
    
    _buscar_nombre = request.form['txtbuscar']

    sql = "SELECT * FROM `productos` WHERE `nombre` LIKE %s"
    datos = ("%" + _buscar_nombre + "%",)

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    productos = cursor.fetchall()
    conexion.commit()

    return render_template('sitio/productos.html', productos=productos)

@app.route('/registrarse_usuario')
def crear_usuario():
    
    
    return render_template('sitio/crear_usuario.html')





@app.route('/registrarse_usuario/guardar', methods=['POST'])
def crear_guardar_usuario():
    _extensiones_permitidas = ['.png', '.jpg', '.webp', '.jpeg']
    _nombre = request.form['txtnombre']
    _apellido = request.form['txtapellido']
    _archivo = request.files['txtImagen']
    _usuario = request.form['txtusuario']
    _contraseña = request.form['txtpassword']

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    nuevoNombre = ""

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `temp_img`")
    nombre_base_datos_tupla = cursor.fetchall()
    cursor.execute("SELECT * FROM `usuario` WHERE usuario=%s", (_usuario,))
    verificar_usuario = cursor.fetchall()
    conexion.commit()

    if nombre_base_datos_tupla:
        nombre_base_datos = nombre_base_datos_tupla[0][0]
    else:
        nombre_base_datos = ""

    # Comprobar Extension
    extension = os.path.splitext(_archivo.filename)[1].lower()

    if _archivo.filename != '': 
        if len(nombre_base_datos_tupla) == 1:
            if extension in _extensiones_permitidas:
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM `temp_img` WHERE 1")
                conexion.commit()
                
                if os.path.exists("templates/sitio/img/temp/" + str(nombre_base_datos)):
                    os.unlink("templates/sitio/img/temp/" + str(nombre_base_datos))
                
                nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                _archivo.save("templates/sitio/img/temp/" + nuevoNombre)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO `temp_img`(`nombre_temp`) VALUES (%s)", (nuevoNombre,))
                conexion.commit()
                flash(nuevoNombre, "archivoc")
            else:
                mensaje = "Solo se permiten archivos con extensiones .png, .jpg, .webp o .jpeg"
                flash(mensaje, 'error')
                flash(_nombre, 'nombrec')
                flash(_apellido, 'apellidoc')
                flash(_usuario, 'usuarioc')
                flash(_contraseña,'contraseñac')
                flash(nombre_base_datos, "archivoc")
                return redirect('/registrarse_usuario')
        elif len(nombre_base_datos_tupla) == 0:
            if extension in _extensiones_permitidas:
                nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                _archivo.save("templates/sitio/img/temp/" + nuevoNombre)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO `temp_img`(`nombre_temp`) VALUES (%s)", (nuevoNombre,))
                conexion.commit()
                flash(nuevoNombre, "archivoc")
            else:
                mensaje = "Solo se permiten archivos con extensiones .png, .jpg, .webp o .jpeg"
                flash(mensaje, 'error')
                flash(_nombre, 'nombrec')
                flash(_apellido, 'apellidoc')
                flash(_usuario, 'usuarioc')
                flash(_contraseña,'contraseñac')
                return redirect('/registrarse_usuario')
    else:
        if nombre_base_datos:
            flash(nombre_base_datos, "archivoc")
        else:
            mensaje = "No se ingresó una imagen"
            flash(mensaje, 'error')
            flash(_nombre, 'nombrec')
            flash(_apellido, 'apellidoc')
            flash(_usuario, 'usuarioc')
            flash(_contraseña,'contraseñac')
            return redirect('/registrarse_usuario')
    
    # Agregar el retorno de la función

    if _nombre != "" and _apellido != "" and _usuario != "" and _contraseña !="":
        if len(verificar_usuario)==0:
            if nombre_base_datos:
                sql = "INSERT INTO `usuario` (`id`, `nombre`, `apellido`, `usuario_imagen`, `usuario`,`contraseña`,`tipo_usuario`) VALUES (NULL, %s, %s, %s, %s, %s, %s)"
                datos = (_nombre, _apellido, str(nombre_base_datos), _usuario,_contraseña,"Usuario")
            if nuevoNombre:
                sql = "INSERT INTO `usuario` (`id`, `nombre`, `apellido`, `usuario_imagen`, `usuario`,`contraseña`,`tipo_usuario`) VALUES (NULL, %s, %s, %s, %s, %s, %s)"
                datos = (_nombre, _apellido,nuevoNombre, _usuario,_contraseña,"Usuario")
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute(sql, datos)
            cursor.execute("DELETE FROM `temp_img` WHERE 1")
            conexion.commit()
            if nombre_base_datos:
                ruta_origen = "templates/sitio/img/temp/" + str(nombre_base_datos)
                ruta_destino = "templates/sitio/img/users/" + str(nombre_base_datos)
                # Mover el archivo a la ruta de destino
                shutil.move(ruta_origen, ruta_destino)
            elif nuevoNombre:
                ruta_origen = "templates/sitio/img/temp/" + nuevoNombre
                ruta_destino = "templates/sitio/img/users/" + nuevoNombre
                # Mover el archivo a la ruta de destino
                shutil.move(ruta_origen, ruta_destino)

            carpeta = "templates/sitio/img/temp"
            for borrar_archivo in os.listdir(carpeta):
                ruta_archivo = os.path.join(carpeta, borrar_archivo)
                if os.path.isfile(ruta_archivo):
                    os.remove(ruta_archivo)
            
            #Borra los flash especificos
            tipo_mensaje = 'archivo'
            mensajes = get_flashed_messages()
            mensajes_filtrados = [mensaje for mensaje in mensajes if mensaje[0] != tipo_mensaje]
            for mensaje in mensajes_filtrados:
                flash(mensaje[1], mensaje[0])
                    
            mensaje = "El producto se creó con éxito"
            flash(mensaje, 'success')
            return redirect('/admin/login')

        else:
            mensaje = "El usuario ya existe"
            flash(mensaje, 'error')
            flash(_nombre, 'nombrec')
            flash(_apellido, 'apellidoc')
            flash(_usuario, 'usuarioc')
            flash(_contraseña,'contraseñac')
    else:
        mensaje = "Complete los espacios vacíos"
        flash(mensaje, 'error')
        flash(_nombre, 'nombrec')
        flash(_apellido, 'apellidoc')
        flash(_usuario, 'usuarioc')
        flash(_contraseña,'contraseñac')

    return redirect('/registrarse_usuario')

@app.route('/admin/')
def admin_index():
    if session.get("usuario") in ["Administrador", "Supervisor"]:
        return render_template('admin/index.html')
    
    elif session.get("usuario") == "Usuario":
        return redirect("/")

    else:
        return redirect("/")

@app.route('/admin/login')
def admin_login():
    if "usuario" in session and session["usuario"] in ["Administrador", "Supervisor"]:
        return redirect("/admin/")
    if "usuario" in session and session["usuario"] in ["Usuario"]:
        return redirect("/")
    return render_template('admin/login.html')


@app.route('/admin/login', methods=['POST'])
def admin_login_guardar():
    _usuario = request.form['txtusuario']
    _contraseña = request.form['txtpassword']

    sql = "SELECT * FROM usuario WHERE BINARY usuario = %s AND contraseña = %s;"
    datos = (_usuario, _contraseña)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    result = cursor.fetchone()
    conexion.commit()

    if result:
        session["login"] = True
        session["usuario"] = result[6]
        session["name"]= result[1]
        session["users"]= result[4]
        session["imagen_Login"]=result[3]

        if session["usuario"] in ["Administrador", "Supervisor"]:
            return redirect("/admin/")
        elif session["usuario"] == "Usuario":
            return redirect("/")

    return render_template('admin/login.html', mensaje="Acceso denegado")


@app.route('/admin/productos')
def admin_productos():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos` ORDER BY `productos`.`id` ASC")
    productos = cursor.fetchall()
    conexion.commit()

    return render_template('admin/productos.html', productos=productos)


@app.route('/admin/productos/guardar', methods=['POST'])
def admin_productos_guardar():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    _extensiones_permitidas = ['.png', '.jpg', '.webp', '.jpeg']
    _nombre = request.form['txtNombre']
    _descripcion = request.form['txtdescripcion']
    _precio = request.form['txtPrecio']
    _cantidad = request.form['txtcantidad']
    _archivo = request.files['txtImagen']
    

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    nuevoNombre = ""

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `temp_img`")
    nombre_base_datos_tupla = cursor.fetchall()
    conexion.commit()

    if nombre_base_datos_tupla:
        nombre_base_datos = nombre_base_datos_tupla[0][0]
    else:
        nombre_base_datos = ""

    # Comprobar Extension
    extension = os.path.splitext(_archivo.filename)[1].lower()

    if _archivo.filename != '':
        if len(nombre_base_datos_tupla) == 1:
            if extension in _extensiones_permitidas:
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM `temp_img` WHERE 1")
                conexion.commit()
                
                if os.path.exists("templates/sitio/img/temp/" + str(nombre_base_datos)):
                    os.unlink("templates/sitio/img/temp/" + str(nombre_base_datos))
                
                nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                _archivo.save("templates/sitio/img/temp/" + nuevoNombre)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO `temp_img`(`nombre_temp`) VALUES (%s)", (nuevoNombre,))
                conexion.commit()
                flash(nuevoNombre, "archivo")
            else:
                mensaje = "Solo se permiten archivos con extensiones .png, .jpg, .webp o .jpeg"
                flash(mensaje, 'error')
                flash(_nombre, 'nombre')
                flash(_descripcion, 'descripcion')
                flash(_precio, 'precio')
                flash(_cantidad, 'cantidad')
                flash(nombre_base_datos, "archivo")
                return redirect('/admin/productos')
        elif len(nombre_base_datos_tupla) == 0:
            if extension in _extensiones_permitidas:
                nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                _archivo.save("templates/sitio/img/temp/" + nuevoNombre)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO `temp_img`(`nombre_temp`) VALUES (%s)", (nuevoNombre,))
                conexion.commit()
                flash(nuevoNombre, "archivo")
            else:
                mensaje = "Solo se permiten archivos con extensiones .png, .jpg, .webp o .jpeg"
                flash(mensaje, 'error')
                flash(_nombre, 'nombre')
                flash(_descripcion, 'descripcion')
                flash(_precio, 'precio')
                flash(_cantidad, 'cantidad')

                return redirect('/admin/productos')
    else:
        if nombre_base_datos:
            flash(nombre_base_datos, "archivo")
        else:
            mensaje = "No se ingresó una imagen"
            flash(mensaje, 'error')
            flash(_nombre, 'nombre')
            flash(_descripcion, 'descripcion')
            flash(_precio, 'precio')
            flash(_cantidad, 'cantidad')
            return redirect('/admin/productos')
    
    # Agregar el retorno de la función

    if _nombre != "" and _descripcion != "" and _precio != "" and _cantidad!=0:
        if _precio.isdigit() and  _cantidad.isdigit() :
            if int(_precio) > 0:
                if nombre_base_datos:
                    sql = "INSERT INTO `productos` (`id`, `nombre`, `descripcion`, `imagen`, `precio`, `cantidad_existente`) VALUES (NULL, %s, %s, %s, %s, %s)"
                    datos = (_nombre, _descripcion, str(nombre_base_datos), _precio,_cantidad)
                if nuevoNombre:
                    sql = "INSERT INTO `productos` (`id`, `nombre`, `descripcion`, `imagen`, `precio`, `cantidad_existente`) VALUES (NULL, %s, %s, %s, %s, %s)"
                    datos = (_nombre, _descripcion,nuevoNombre , _precio,_cantidad)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute(sql, datos)
                cursor.execute("DELETE FROM `temp_img` WHERE 1")
                conexion.commit()
                if nombre_base_datos:
                    ruta_origen = "templates/sitio/img/temp/" + str(nombre_base_datos)
                    ruta_destino = "templates/sitio/img/products/" + str(nombre_base_datos)
                    # Mover el archivo a la ruta de destino
                    shutil.move(ruta_origen, ruta_destino)
                elif nuevoNombre:
                    ruta_origen = "templates/sitio/img/temp/" + nuevoNombre
                    ruta_destino = "templates/sitio/img/products/" + nuevoNombre
                    # Mover el archivo a la ruta de destino
                    shutil.move(ruta_origen, ruta_destino)

                carpeta = "templates/sitio/img/temp"
                for borrar_archivo in os.listdir(carpeta):
                    ruta_archivo = os.path.join(carpeta, borrar_archivo)
                    if os.path.isfile(ruta_archivo):
                        os.remove(ruta_archivo)
                        
                #Borra los flash especificos
                tipo_mensaje = 'archivo'
                mensajes = get_flashed_messages()
                mensajes_filtrados = [mensaje for mensaje in mensajes if mensaje[0] != tipo_mensaje]
                for mensaje in mensajes_filtrados:
                    flash(mensaje[1], mensaje[0])

                mensaje = "El producto se creó con éxito"
                flash(mensaje, 'success')
            else:
                mensaje = "El precio debe ser mayor a cero"
                flash(mensaje, 'error')
                flash(_nombre, 'nombre')
                flash(_descripcion, 'descripcion')
                flash(_precio, 'precio')
                flash(_cantidad, 'cantidad')

        else:
            if _precio.isdigit():
                mensaje = "El precio debe ser un número entero"
            elif _cantidad.isdigit():
                mensaje = "El la cantidad de productos debe ser un numero entero"

            flash(mensaje, 'error')
            flash(_nombre, 'nombre')
            flash(_descripcion, 'descripcion')
            flash(_precio, 'precio')
            flash(_cantidad, 'cantidad')

    else:
        mensaje = "Complete los espacios vacíos"
        flash(mensaje, 'error')
        flash(_nombre, 'nombre')
        flash(_descripcion, 'descripcion')
        flash(_precio, 'precio')
        flash(_cantidad, 'cantidad')


    return redirect('/admin/productos')


@app.route('/admin/productos/borrar', methods=['POST'])
def admin_productos_borrar():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    _id = request.form['txtID']
    print(_id)

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT imagen FROM `productos` WHERE id=%s", (_id,))
    producto = cursor.fetchall()
    conexion.commit()
    print(producto)

    if os.path.exists("templates/sitio/img/products/" + str(producto[0][0])):
        os.unlink("templates/sitio/img/products/" + str(producto[0][0]))

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM `productos` WHERE id=%s", (_id,))
    cursor.execute("DELETE FROM `carrito` WHERE id_producto=%s",(_id,))
    conexion.commit()

    return redirect('/admin/productos')


@app.route('/admin/registro')
def admin_registro():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    conexion = mysql.connect()
    cursor = conexion.cursor()
    usuario_actual = session["users"]
    consulta = "SELECT * FROM `usuario` WHERE `tipo_usuario` = 'Administrador' AND `usuario` != %s ORDER BY `id` ASC"
    datos = (usuario_actual,)

    cursor.execute(consulta, datos)

    # Obtener los resultados
    usuario = cursor.fetchall()

    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `usuario` WHERE `tipo_usuario` = 'Supervisor' ORDER BY `usuario`.`id` ASC")
    registro = cursor.fetchall()
    conexion.commit()
    print(usuario)
    print(registro)

    return render_template('admin/registro.html', usuario=usuario, registro=registro)


@app.route('/admin/registro/guardar', methods=['POST'])
def admin_registro_guardar():
    
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    _extensiones_permitidas = ['.png', '.jpg', '.webp', '.jpeg']
    _nombre = request.form['txtnombre']
    _apellido = request.form['txtapellido']
    _archivo = request.files['txtImagen']
    _usuario = request.form['txtusuario']
    _contraseña = request.form['txtpassword']
    _tipo_usuario = request.form['txttipo_usuario']

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    nuevoNombre = ""

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `temp_img`")
    nombre_base_datos_tupla = cursor.fetchall()
    cursor.execute("SELECT * FROM `usuario` WHERE usuario=%s", (_usuario,))
    verificar_usuario = cursor.fetchall()
    conexion.commit()

    if nombre_base_datos_tupla:
        nombre_base_datos = nombre_base_datos_tupla[0][0]
    else:
        nombre_base_datos = ""

    # Comprobar Extension
    extension = os.path.splitext(_archivo.filename)[1].lower()

    if _archivo.filename != '': 
        if len(nombre_base_datos_tupla) == 1:
            if extension in _extensiones_permitidas:
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM `temp_img` WHERE 1")
                conexion.commit()
                
                if os.path.exists("templates/sitio/img/temp/" + str(nombre_base_datos)):
                    os.unlink("templates/sitio/img/temp/" + str(nombre_base_datos))
                
                nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                _archivo.save("templates/sitio/img/temp/" + nuevoNombre)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO `temp_img`(`nombre_temp`) VALUES (%s)", (nuevoNombre,))
                conexion.commit()
                flash(nuevoNombre, "archivor")
            else:
                mensaje = "Solo se permiten archivos con extensiones .png, .jpg, .webp o .jpeg"
                flash(mensaje, 'error')
                flash(_nombre, 'nombrer')
                flash(_apellido, 'apellidor')
                flash(_usuario, 'usuarior')
                flash(_contraseña,'contraseñar')
                flash(nombre_base_datos, "archivor")
                return redirect('/admin/registro')
        elif len(nombre_base_datos_tupla) == 0:
            if extension in _extensiones_permitidas:
                nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                _archivo.save("templates/sitio/img/temp/" + nuevoNombre)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO `temp_img`(`nombre_temp`) VALUES (%s)", (nuevoNombre,))
                conexion.commit()
                flash(nuevoNombre, "archivor")
            else:
                mensaje = "Solo se permiten archivos con extensiones .png, .jpg, .webp o .jpeg"
                flash(mensaje, 'error')
                flash(_nombre, 'nombrer')
                flash(_apellido, 'apellidor')
                flash(_usuario, 'usuarior')
                flash(_contraseña,'contraseñar')
                return redirect('/admin/registro')
    else:
        if nombre_base_datos:
            flash(nombre_base_datos, "archivor")
        else:
            mensaje = "No se ingresó una imagen"
            flash(mensaje, 'error')
            flash(_nombre, 'nombrer')
            flash(_apellido, 'apellidor')
            flash(_usuario, 'usuarior')
            flash(_contraseña,'contraseñar')
            return redirect('/admin/registro')
    
    # Agregar el retorno de la función

    if _nombre != "" and _apellido != "" and _usuario != "" and _contraseña !="" and _tipo_usuario !="vacio" :
        if len(verificar_usuario)==0:
            if nombre_base_datos:
                sql = "INSERT INTO `usuario` (`id`, `nombre`, `apellido`, `usuario_imagen`, `usuario`,`contraseña`,`tipo_usuario`) VALUES (NULL, %s, %s, %s, %s, %s, %s)"
                datos = (_nombre, _apellido, str(nombre_base_datos), _usuario,_contraseña,_tipo_usuario)
            if nuevoNombre:
                sql = "INSERT INTO `usuario` (`id`, `nombre`, `apellido`, `usuario_imagen`, `usuario`,`contraseña`,`tipo_usuario`) VALUES (NULL, %s, %s, %s, %s, %s, %s)"
                datos = (_nombre, _apellido,nuevoNombre, _usuario,_contraseña,_tipo_usuario)
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute(sql, datos)
            cursor.execute("DELETE FROM `temp_img` WHERE 1")
            conexion.commit()
            if nombre_base_datos:
                ruta_origen = "templates/sitio/img/temp/" + str(nombre_base_datos)
                ruta_destino = "templates/sitio/img/users/" + str(nombre_base_datos)
                # Mover el archivo a la ruta de destino
                shutil.move(ruta_origen, ruta_destino)
            elif nuevoNombre:
                ruta_origen = "templates/sitio/img/temp/" + nuevoNombre
                ruta_destino = "templates/sitio/img/users/" + nuevoNombre
                # Mover el archivo a la ruta de destino
                shutil.move(ruta_origen, ruta_destino)

            carpeta = "templates/sitio/img/temp"
            for borrar_archivo in os.listdir(carpeta):
                ruta_archivo = os.path.join(carpeta, borrar_archivo)
                if os.path.isfile(ruta_archivo):
                    os.remove(ruta_archivo)
            
            #Borra los flash especificos
            tipo_mensaje = 'archivo'
            mensajes = get_flashed_messages()
            mensajes_filtrados = [mensaje for mensaje in mensajes if mensaje[0] != tipo_mensaje]
            for mensaje in mensajes_filtrados:
                flash(mensaje[1], mensaje[0])
                    
            mensaje = "El producto se creó con éxito"
            flash(mensaje, 'success')
        else:
            mensaje = "El usuario ya existe"
            flash(mensaje, 'error')
            flash(_nombre, 'nombrer')
            flash(_apellido, 'apellidor')
            flash(_usuario, 'usuarior')
            flash(_contraseña,'contraseñar')
    else:
        mensaje = "Complete los espacios vacíos"
        flash(mensaje, 'error')
        flash(_nombre, 'nombrer')
        flash(_apellido, 'apellidor')
        flash(_usuario, 'usuarior')
        flash(_contraseña,'contraseñar')

    return redirect('/admin/registro')


@app.route('/admin/cerrar')
def admin_login_cerrar(): 
    session.clear()
    return redirect('/admin/login')


@app.route('/admin/modificar', methods=['POST'])
def admin_registro_modificar():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")
    _id = request.form['txtid']

    if _id :
        _id = request.form['txtid']
        sql = "SELECT * FROM `usuario` WHERE id=%s"
        datos = (_id,)
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute(sql, datos)
        resultado = cursor.fetchall()
        conexion.commit()
        flash(resultado[0][0], 'idm')
        flash(resultado[0][1], 'nombrem')
        flash(resultado[0][2], 'apellidom')
        flash(resultado[0][3], 'archivom')
        flash(resultado[0][4], 'usuariom')
        flash(resultado[0][5], 'contraseñam')
        flash(resultado[0][6], 'tipo_usuariom')
        return render_template('admin/modificar.html')
    
    return redirect('/admin/registro')


@app.route('/admin/modificar/guardar', methods=['POST'])
def admin_registro_modificar_guardar():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")
    
    _id = request.form['txtid']
    _extensiones_permitidas = ['.png', '.jpg', '.webp', '.jpeg']
    _nombre = request.form['txtnombre']
    _apellido = request.form['txtapellido']
    _archivo = request.files['txtImagen']
    _usuario = request.form['txtusuario']
    _contraseña = request.form['txtpassword']
    _tipo_usuario = request.form['txttipo_usuario'] 

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    nuevoNombre = ""

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT usuario_imagen FROM `usuario` WHERE id=%s", (_id,))
    _guarda_imagen_tupla = cursor.fetchall()
    
    if _guarda_imagen_tupla:
        _guarda_imagen_datos = _guarda_imagen_tupla[0][0]
    else:
        _guarda_imagen_datos = ""
        
    cursor.execute("SELECT * FROM `usuario` WHERE usuario=%s AND id!=%s", (_usuario, _id))
    verificar_usuario = cursor.fetchall()

    if _nombre != "" and _apellido != "" and _usuario != "" and _contraseña != "" and _tipo_usuario != "vacio":
        if len(verificar_usuario) == 0:
            if _archivo.filename:
                extension = os.path.splitext(_archivo.filename)[1].lower()
                if extension in _extensiones_permitidas:
                    if _guarda_imagen_datos and os.path.exists("templates/sitio/img/users/" + _guarda_imagen_datos):
                        os.unlink("templates/sitio/img/users/" + _guarda_imagen_datos)
                    nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                    _archivo.save("templates/sitio/img/users/" + nuevoNombre)
                    sql = "UPDATE usuario SET nombre = %s, apellido = %s, usuario_imagen = %s, usuario = %s, contraseña = %s, tipo_usuario = %s WHERE id = %s"
                    datos = (_nombre, _apellido, nuevoNombre, _usuario, _contraseña, _tipo_usuario, _id)
                    cursor.execute(sql, datos)
                    conexion.commit()
                    
                    mensaje = "El usuario se modificó con éxito"
                    flash(mensaje, 'success')
                else:
                    mensaje = "La imagen seleccionada no está permitida"
                    flash(mensaje, 'error')
            elif _guarda_imagen_datos:
                sql = "UPDATE usuario SET nombre = %s, apellido = %s, usuario_imagen = %s, usuario = %s, contraseña = %s, tipo_usuario = %s WHERE id = %s"
                datos = (_nombre, _apellido, _guarda_imagen_datos, _usuario, _contraseña, _tipo_usuario, _id)
                cursor.execute(sql, datos)
                conexion.commit()

                mensaje = "El usuario se modificó con éxito"
                flash(mensaje, 'success')
        else:
            mensaje = "El usuario ya existe"
            flash(mensaje, 'error')
    else:
        mensaje = "No se ingresaron todos los datos requeridos, no se hicieron modificaciones"
        flash(mensaje, 'error')
    
    return redirect('/admin/registro')



@app.route('/admin/registro/borrar', methods=['POST'])
def admin_registro_borrar():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    _id = request.form['txtid']
    print(_id)

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT usuario_imagen FROM `usuario` WHERE id=%s", (_id,))
    producto = cursor.fetchall()
    conexion.commit()
    print(producto)

    if os.path.exists("templates/sitio/img/users/" + str(producto[0][0])):
        os.unlink("templates/sitio/img/users/" + str(producto[0][0]))

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM `usuario` WHERE id=%s", (_id,))
    conexion.commit()

    return redirect('/admin/registro')

@app.route('/admin/usuario')
def admin_usuario():
    if "login" not in session:
        return redirect("/admin/login")

    sql = "SELECT * FROM `usuario` WHERE `usuario` = %s"
    datos = (session["users"],)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    result = cursor.fetchall()
    conexion.commit()
    print(result)
    flash(result[0][0], 'idu')
    flash(result[0][1], 'nombreu')
    flash(result[0][2], 'apellidou')
    flash(result[0][3], 'usuario_imagenu')
    flash(result[0][4], 'usuariou')
    flash(result[0][5], 'contraseñau')
    flash(result[0][6], 'tipo_usuariou')

    return render_template('admin/usuario.html')

@app.route('/admin/usuario/guardar', methods=['POST'])
def admin_usuaio_guardar():
    if "usuario" not in session:
        return redirect("/admin/login")
    
    _id = request.form['txtid']
    _extensiones_permitidas = ['.png', '.jpg', '.webp', '.jpeg']
    _nombre = request.form['txtnombre']
    _apellido = request.form['txtapellido']
    _archivo = request.files['txtImagen']
    _usuario = request.form['txtusuario']
    _contraseña = request.form['txtpassword']
    if session["usuario"]=="Administrador" or session["usuario"]=="Supervisor":
        _tipo_usuario = request.form['txttipo_usuario'] 

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    nuevoNombre = ""

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT usuario_imagen FROM `usuario` WHERE id=%s", (_id,))
    _guarda_imagen_tupla = cursor.fetchall()
    
    if _guarda_imagen_tupla:
        _guarda_imagen_datos = _guarda_imagen_tupla[0][0]
    else:
        _guarda_imagen_datos = ""
        
    cursor.execute("SELECT * FROM `usuario` WHERE usuario=%s AND id!=%s", (_usuario, _id))
    verificar_usuario = cursor.fetchall()

    if _nombre != "" and _apellido != "" and _usuario != "" and _contraseña != "":
        if session["usuario"]=="Administrador" or session["usuario"]=="Supervisor":
            if _tipo_usuario != "vacio":
                if len(verificar_usuario) == 0:
                    if _archivo.filename:
                        extension = os.path.splitext(_archivo.filename)[1].lower()
                        if extension in _extensiones_permitidas:
                            if _guarda_imagen_datos and os.path.exists("templates/sitio/img/users/" + _guarda_imagen_datos):
                                os.unlink("templates/sitio/img/users/" + _guarda_imagen_datos)
                            nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                            _archivo.save("templates/sitio/img/users/" + nuevoNombre)
                            sql = "UPDATE usuario SET nombre = %s, apellido = %s, usuario_imagen = %s, usuario = %s, contraseña = %s, tipo_usuario = %s WHERE id = %s"
                            datos = (_nombre, _apellido, nuevoNombre, _usuario, _contraseña, _tipo_usuario, _id)
                            cursor.execute(sql, datos)
                            conexion.commit()
                            
                            mensaje = "El usuario se modificó con éxito"
                            flash(mensaje, 'success')
                        else:
                            mensaje = "La imagen seleccionada no está permitida"
                            flash(mensaje, 'error')
                    elif _guarda_imagen_datos:
                        sql = "UPDATE usuario SET nombre = %s, apellido = %s, usuario_imagen = %s, usuario = %s, contraseña = %s, tipo_usuario = %s WHERE id = %s"
                        datos = (_nombre, _apellido, _guarda_imagen_datos, _usuario, _contraseña, _tipo_usuario, _id)
                        cursor.execute(sql, datos)
                        conexion.commit()

                        mensaje = "El usuario se modificó con éxito"
                        flash(mensaje, 'success')
                else:
                    mensaje = "El usuario ya existe"
                    flash(mensaje, 'error')
            else:
                mensaje = "El tipo de usuario no fue seleccionado"
                flash(mensaje, 'error')
        else:
            if len(verificar_usuario) == 0:
                    if _archivo.filename:
                        extension = os.path.splitext(_archivo.filename)[1].lower()
                        if extension in _extensiones_permitidas:
                            if _guarda_imagen_datos and os.path.exists("templates/sitio/img/users/" + _guarda_imagen_datos):
                                os.unlink("templates/sitio/img/users/" + _guarda_imagen_datos)
                            nuevoNombre = horaActual + "_" + secure_filename(_archivo.filename)
                            _archivo.save("templates/sitio/img/users/" + nuevoNombre)
                            sql = "UPDATE usuario SET nombre = %s, apellido = %s, usuario_imagen = %s, usuario = %s, contraseña = %s, tipo_usuario = %s WHERE id = %s"
                            datos = (_nombre, _apellido, nuevoNombre, _usuario, _contraseña, "Usuario", _id)
                            cursor.execute(sql, datos)
                            conexion.commit()
                            
                            mensaje = "El usuario se modificó con éxito"
                            flash(mensaje, 'success')
                        else:
                            mensaje = "La imagen seleccionada no está permitida"
                            flash(mensaje, 'error')
                    elif _guarda_imagen_datos:
                        sql = "UPDATE usuario SET nombre = %s, apellido = %s, usuario_imagen = %s, usuario = %s, contraseña = %s, tipo_usuario = %s WHERE id = %s"
                        datos = (_nombre, _apellido, _guarda_imagen_datos, _usuario, _contraseña, "Usuario", _id)
                        cursor.execute(sql, datos)
                        conexion.commit()

                        mensaje = "El usuario se modificó con éxito"
                        flash(mensaje, 'success')
            else:
                mensaje = "El usuario ya existe"
                flash(mensaje, 'error')
    else:
        mensaje = "No se ingresaron todos los datos requeridos, no se hicieron modificaciones"
        flash(mensaje, 'error')
    return redirect('/admin/')

@app.route('/admin/informes')
def admin_informes():
    if "usuario" not in session or session["usuario"] not in ["Administrador", "Supervisor"]:
        return redirect("/admin/login")

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `informes`")
    informes = cursor.fetchall()
    conexion.commit()
    print(informes)

    return render_template('admin/informes.html', informes=informes)


@app.route('/admin/informes/borrar', methods=['POST'])
def admin_informe_borrar():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    _id = request.form['txtIDInforme']
    print(_id)

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM `informes` WHERE id_informes=%s", (_id,))
    informe = cursor.fetchall()
    conexion.commit()
    print(informe)

    if os.path.exists("templates/admin/informes/" + str(informe[0][0])):
        os.unlink("templates/admin/informes/" + str(informe[0][0]))

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM `informes` WHERE id_informes=%s", (_id,))
    conexion.commit()

    return redirect('/admin/informes')

@app.route('/generar_informe_excel', methods=['GET'])
def generar_informe_excel():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos`")
    resultados = cursor.fetchall()

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Informe')

    headers = ['Id', 'Nombre', 'Imagen', 'Precio']
    for col_idx, header in enumerate(headers):
        sheet.write(0, col_idx, header)

    for row_idx, resultado in enumerate(resultados, start=1):
        for col_idx, dato in enumerate(resultado):
            sheet.write(row_idx, col_idx, dato)

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y-%m-%d__%H_%M_%S')
    fechaActual = tiempo.strftime('%Y-%m-%d')
    hActual = tiempo.strftime('%H:%M:%S')
    fechamostrada = fechaActual + " " + hActual

    informe_excel_path = horaActual + "_" + 'Informe_Ventas.xls'
    workbook.save("templates/admin/informes/" + informe_excel_path)

    sql = "INSERT INTO `informes` (`id_informes`, `fecha`, `nombre`) VALUES (NULL, %s, %s)"
    datos = (fechamostrada, informe_excel_path)
    cursor.execute(sql, datos)
    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect('/admin/informes')


@app.route('/descargar_generar_informe_excel', methods=['GET'])
def descargar_generar_informe_excel():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos`")
    resultados = cursor.fetchall()

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Informe')

    headers = ['Id', 'Nombre', 'Imagen', 'Precio']
    for col_idx, header in enumerate(headers):
        sheet.write(0, col_idx, header)

    for row_idx, resultado in enumerate(resultados, start=1):
        for col_idx, dato in enumerate(resultado):
            sheet.write(row_idx, col_idx, dato)

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y-%m-%d__%H_%M_%S')
    fechaActual = tiempo.strftime('%Y-%m-%d')
    hActual = tiempo.strftime('%H:%M:%S')
    fechamostrada = fechaActual + " " + hActual

    informe_excel_path = horaActual + "_" + 'Informe_Ventas.xls'
    workbook.save("templates/admin/informes/" + informe_excel_path)

    sql = "INSERT INTO `informes` (`id_informes`, `fecha`, `nombre`) VALUES (NULL, %s, %s)"
    datos = (fechamostrada, informe_excel_path)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    conexion.commit()

    cursor.close()
    conexion.commit()

    return send_file("templates/admin/informes/" + informe_excel_path, as_attachment=True)






@app.route('/<path:vista>')
def dynamic_route(vista):
    vistas_permitidas = ['admin']

    if vista not in vistas_permitidas:
        return render_template('sitio/404.html')

    return render_template(f'sitio/{vista}.html')


if __name__ == '__main__':
    app.run(debug=True)




#     Limpiar cadenas de texto//Seguridad 
#     Evitar injeccion sql
# def limpiar_cadena(cadena):
#     cadena = cadena.strip()
#     cadena = cadena.replace("/", "")#Eliminar
#     cadena = cadena.replace("<script>", "")
#     cadena = cadena.replace("</script>", "")
#     cadena = cadena.replace("<script src", "")
#     cadena = cadena.replace("<script type=", "")
#     cadena = cadena.replace("DELETE FROM", "")
#     cadena = cadena.replace("INSERT INTO", "")
#     cadena = cadena.replace("DROP TABLE", "")
#     cadena = cadena.replace("DROP DATABASE", "")
#     cadena = cadena.replace("TRUNCATE TABLE", "")
#     cadena = cadena.replace("SHOW TABLES", "")
#     cadena = cadena.replace("SHOW DATABASES", "")
#     cadena = cadena.replace("<?php", "")
#     cadena = cadena.replace("?>", "")
#     cadena = cadena.replace("--", "")
#     cadena = cadena.replace("^", "")
#     cadena = cadena.replace("<", "")
#     cadena = cadena.replace("[", "")
#     cadena = cadena.replace("]", "")
#     cadena = cadena.replace("==", "")
#     cadena = cadena.replace(";", "")
#     cadena = cadena.replace("::", "")
#     cadena = cadena.strip()
#     return cadena

#     Renombrar nombre de las fotos
# def renombrar_fotos(nombre):
#     fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
#     nombre = nombre + "_" + fecha_actual
#     nombre = nombre.replace("  ", "")
#     nombre = nombre.replace(" ", "_")
#     nombre = nombre.replace("/", "_")
#     nombre = nombre.replace("#", "_")
#     nombre = nombre.replace("-", "_")
#     nombre = nombre.replace("$", "_")
#     nombre = nombre.replace(".", "_")
#     nombre = nombre.replace(",", "_")
#     return nombre



