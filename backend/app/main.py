from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.database import Base, engine
from app.models import sala, categoria, usuario, movimiento, insumo
from app.routes import salas, categorias, usuarios, movimientos, insumos, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hestia",
    description="Sistema de gestión de insumos — DuocUC",
    version="0.1.0"
)

app.include_router(salas.router)
app.include_router(categorias.router)
app.include_router(usuarios.router)
app.include_router(movimientos.router)
app.include_router(insumos.router)
app.include_router(auth.router)


@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a Hestia", "estado": "activo"}


def custom_openapi():
    """Agrega el esquema BearerAuth al Swagger para poder pegar el JWT directamente.
    Esto coexiste con el formulario OAuth2 existente.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Agregar esquema HTTP Bearer (campo "Value" en el Authorize del Swagger)
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Pega aqui el access_token obtenido desde /auth/login"
    }

    # Aplicar BearerAuth a todos los endpoints protegidos
    for path_data in schema.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "security" in operation:
                operation["security"].append({"BearerAuth": []})

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
