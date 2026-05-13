from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import Base, engine
# Importar todos los modelos para que SQLAlchemy registre sus tablas.
# create_all() necesita conocer TODOS los modelos antes de ejecutarse.
from app.models import sala, categoria, usuario, movimiento, insumo  # noqa
from app.models import audit_log  # noqa
from app.routes import (
    salas, categorias, usuarios, movimientos, insumos, auth, resumen, importar
)
from app.routes import audit_log as audit_log_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hestia",
    description="Sistema de gestion de insumos - DuocUC",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
# X-Content-Type-Options: nosniff     -> evita MIME sniffing
# X-Frame-Options: DENY               -> evita clickjacking via iframe
# X-XSS-Protection: 1; mode=block    -> filtro XSS en navegadores viejos
# Referrer-Policy                     -> no filtra URL completa al navegar
# Permissions-Policy                  -> deshabilita camara/mic/geolocalizacion
# ---------------------------------------------------------------------------

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(salas.router)
app.include_router(categorias.router)
app.include_router(usuarios.router)
app.include_router(movimientos.router)
app.include_router(insumos.router)
app.include_router(auth.router)
app.include_router(resumen.router)
app.include_router(importar.router)
app.include_router(audit_log_routes.router)


@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a Hestia", "estado": "activo"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Pega aqui el access_token obtenido desde /auth/login",
    }
    for path_data in schema.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "security" in operation:
                operation["security"].append({"BearerAuth": []})
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
