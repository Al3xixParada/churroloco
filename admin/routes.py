from flask import Blueprint, render_template,session,redirect
from admin import admin_app


@admin_app.route('/')
def admin_index():
    if session.get("usuario") in ["Administrador", "Empleado"]:
        return render_template('admin/index.html')
    
    elif session.get("usuario") == "Usuario":
        return redirect("/")
    else:
        return redirect("/")