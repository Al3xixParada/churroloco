from flask import Blueprint, render_template,session,request,redirect
from admin import admin_app

from app.config import app, mysql

# Tu código en este archivo

@admin_app.route('/login')
def admin_login():
    if "usuario" in session and session["usuario"] in ["Administrador", "Empleado"]:
        return redirect("/admin/")
    if "usuario" in session and session["usuario"] in ["Usuario"]:
        return redirect("/")
    return render_template('admin/login.html')


@admin_app.route('/login', methods=['POST'])
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

        if session["usuario"] in ["Administrador", "Empleado"]:
            return redirect("/admin/")
        elif session["usuario"] == "Usuario":
            return redirect("/")

    return render_template('admin/login.html', mensaje="Acceso denegado")

@admin_app.route('/cerrar')
def admin_login_cerrar(): 
    session.clear()
    return redirect('/admin/login')