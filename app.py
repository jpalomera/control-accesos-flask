import os
from datetime import datetime, timezone

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "solo-desarrollo-cambiar-en-produccion")

mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) if mongo_uri else None
db = client[os.getenv("MONGODB_DB", "control_accesos")] if client is not None else None


def collection(name):
    if db is None:
        raise RuntimeError("MONGODB_URI no está configurada")
    return db[name]


def serialize(document):
    result = dict(document)
    if "_id" in result:
        result["_id"] = str(result["_id"])
    return result


@app.get("/health")
def health():
    if client is None:
        return jsonify(status="error", message="MONGODB_URI no configurada"), 503
    try:
        client.admin.command("ping")
        return jsonify(status="ok", database=db.name)
    except PyMongoError as exc:
        return jsonify(status="error", message=str(exc)), 503


@app.get("/")
def dashboard():
    error = None
    usuarios = []
    puntos = []
    registros = []
    try:
        usuarios = list(collection("usuarios").find().sort("usuario_id", 1))
        puntos = list(collection("puntos_acceso").find().sort("punto_id", 1))
        registros = list(collection("registros_acceso").find().sort("fecha", -1).limit(50))
    except (RuntimeError, PyMongoError) as exc:
        error = str(exc)

    permitidos = sum(1 for item in registros if item.get("resultado") == "permitido")
    denegados = sum(1 for item in registros if item.get("resultado") == "denegado")
    return render_template(
        "dashboard.html",
        usuarios=usuarios,
        puntos=puntos,
        registros=registros,
        permitidos=permitidos,
        denegados=denegados,
        error=error,
    )


@app.post("/registros")
def crear_registro():
    documento = {
        "registro_id": f"WEB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "usuario_id": request.form.get("usuario_id", "").strip(),
        "punto_id": request.form.get("punto_id", "").strip(),
        "fecha": datetime.now(timezone.utc).isoformat(),
        "resultado": request.form.get("resultado", "denegado"),
        "motivo": request.form.get("motivo", "registro_manual").strip(),
        "origen": "panel_flask",
    }
    if not documento["usuario_id"] or not documento["punto_id"]:
        flash("Selecciona un usuario y un punto de acceso.", "error")
        return redirect(url_for("dashboard"))
    try:
        collection("registros_acceso").insert_one(documento)
        flash("Registro guardado correctamente.", "success")
    except (RuntimeError, PyMongoError) as exc:
        flash(f"No fue posible guardar: {exc}", "error")
    return redirect(url_for("dashboard"))


@app.get("/api/usuarios")
def api_usuarios():
    try:
        return jsonify([serialize(item) for item in collection("usuarios").find()])
    except (RuntimeError, PyMongoError) as exc:
        return jsonify(error=str(exc)), 503


@app.get("/api/puntos-acceso")
def api_puntos():
    try:
        return jsonify([serialize(item) for item in collection("puntos_acceso").find()])
    except (RuntimeError, PyMongoError) as exc:
        return jsonify(error=str(exc)), 503


@app.get("/api/registros")
def api_registros():
    try:
        cursor = collection("registros_acceso").find().sort("fecha", -1).limit(100)
        return jsonify([serialize(item) for item in cursor])
    except (RuntimeError, PyMongoError) as exc:
        return jsonify(error=str(exc)), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
