# Sistema de control de accesos

Aplicación Flask conectada a MongoDB Atlas para consultar usuarios, puntos de acceso y eventos de seguridad, además de registrar accesos manuales.

## Colecciones

- `usuarios`
- `puntos_acceso`
- `registros_acceso`

## Configuración local

```bash
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` y define `MONGODB_URI`. La credencial nunca debe subirse a GitHub.

```bash
flask --app app run --debug
```

Abre `http://127.0.0.1:5000`.

## Producción

Ejecuta con:

```bash
gunicorn app:app
```

Configura `MONGODB_URI`, `MONGODB_DB` y `FLASK_SECRET_KEY` como variables secretas del proveedor donde despliegues el backend.
