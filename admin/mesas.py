from flask import flash, render_template, request, redirect, session, send_file, send_from_directory
from datetime import datetime
import os
import shutil
from werkzeug.utils import secure_filename
import xlwt
from flask import flash, get_flashed_messages

from admin import admin_app

from app.config import app, mysql


@admin_app.route('/mesas')
def admin_productos():
    if "usuario" not in session or session["usuario"] != "Administrador":
        return redirect("/admin/login")
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos` ORDER BY `productos`.`id` ASC")
    productos = cursor.fetchall()
    conexion.commit()

    return render_template('admin/administrar_mesas.html', productos=productos)




@admin_app.route('/mesas/guardar', methods=['POST'])
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
                return redirect('/admin/mesas')
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

                return redirect('/admin/mesas')
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
            return redirect('/admin/mesas')
    
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


    return redirect('/admin/mesas')




@admin_app.route('/mesas/borrar', methods=['POST'])
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

    return redirect('/admin/mesas')