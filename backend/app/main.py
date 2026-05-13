from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import Base, engine
from app.models import sala, categoria, usuario, movimiento, insumo
from app.routes import salas, categorias, usuarios, movimientos, insumos, auth, resumen, importar

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hestia",
    description="Sistema de gestion de insumos - DuocUC",
    version="0.1.0"
)


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
# Estas cabeceras HTTP van en TODAS las respuestas de la API y le dicen al
# navegador como protegerse. No requieren ninguna logica de negocio.
#
# X-Content-Type-Options: nosniff
#   El navegador no intenta "adivinar" el tipo de un archivo (MIME sniffing).
#   Sin esto, un archivo .txt con contenido HTML podria ejecutarse como HTML.
#
# X-Frame-Options: DENY
#   La app no puede ser cargada dentro de un <iframe>.
#   Previene clickjacking: un atacante superpone un iframe invisible de Hestia
#   sobre su pagina para que el usuario haga clic en acciones sin saberlo.
#
# X-XSS-Protection: 1; mode=block
#   Activa el filtro XSS de los navegadores mas antiguos (IE, Chrome < 78).
#   Navegadores modernos lo ignoran (tienen CSP), pero no hace dano.
#
# Referrer-Policy: strict-origin-when-cross-origin
#   Cuando el usuario navega de Hestia a otro sitio, el navegador no envia
#   la URL completa de origen (podria contener parametros sensibles).
#   Solo envia el dominio, y solo si el destino usa HTTPS.
#
# Permissions-Policy
#   Deshabilita explicitamente APIs del navegador que Hestia no necesita:
#   camara, microfono y geolocalizacion. Un script malicioso no podria
#   activarlas aunque lo intentara.
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


@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a Hestia", "estado": "activo"}


def custom_openapi():
    """Agrega el esquema BearerAuth al Swagger para pegar el JWT directamente."""
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
        "description": "Pega aqui el access_token obtenido desde /auth/login"
    }

    for path_data in schema.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "security" in operation:
                operation["security"].append({"BearerAuth": []})

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
