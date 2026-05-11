from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import csv
import io
import pyotp

from app.database import get_db
from app.models.insumo import Insumo
from app.models.sala import Sala
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.utils.deps import require_admin

router = APIRouter(prefix="/importar", tags=["Importacion"])

TOTP_VALID_WINDOW = 1

# Columnas que acepta el sistema. Las marcadas como requeridas deben estar presentes.
COLUMNAS_REQUERIDAS = {"nombre", "stock_actual", "stock_minimo"}
COLUMNAS_OPCIONALES = {"descripcion", "sala", "categoria"}
TODAS_COLUMNAS = COLUMNAS_REQUERIDAS | COLUMNAS_OPCIONALES


class ErrorFila(BaseModel):
    fila: int
    razon: str


class ImportarResponse(BaseModel):
    importados: int
    omitidos: int
    errores: list[ErrorFila]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verificar_totp(usuario: Usuario, codigo: str) -> None:
    """Lanza 401 si el codigo TOTP no es valido o 2FA no esta habilitado."""
    if not usuario.totp_habilitado or not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes tener el 2FA activado para importar archivos."
        )
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(codigo, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo 2FA incorrecto. La importacion fue cancelada."
        )


def _leer_filas(contenido: bytes, nombre_archivo: str) -> list[dict]:
    """Parsea CSV o XLSX y devuelve una lista de dicts con las filas."""
    extension = nombre_archivo.rsplit(".", 1)[-1].lower()

    if extension == "csv":
        texto = contenido.decode("utf-8-sig")  # utf-8-sig elimina el BOM de Windows
        reader = csv.DictReader(io.StringIO(texto))
        return [dict(fila) for fila in reader]

    elif extension in ("xlsx", "xls"):
        try:
            import openpyxl
        except ImportError:
            raise HTTPException(status_code=500, detail="openpyxl no instalado.")
        wb = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
        ws = wb.active
        filas = list(ws.iter_rows(values_only=True))
        if not filas:
            return []
        encabezados = [str(c).strip().lower() if c else "" for c in filas[0]]
        resultado = []
        for fila in filas[1:]:
            if all(c is None for c in fila):
                continue  # fila completamente vacia
            resultado.append(
                {encabezados[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(fila)}
            )
        return resultado

    else:
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Usa CSV o XLSX."
        )


def _normalizar_encabezados(filas: list[dict]) -> list[dict]:
    """Convierte todas las claves a minusculas y elimina espacios."""
    return [
        {k.strip().lower(): v.strip() if isinstance(v, str) else v for k, v in fila.items()}
        for fila in filas
    ]


def _buscar_o_crear_sala(nombre: str, db: Session) -> Optional[int]:
    if not nombre:
        return None
    sala = db.query(Sala).filter(
        Sala.nombre.ilike(nombre.strip())
    ).first()
    if sala:
        return sala.id
    # Si no existe, la crea automaticamente
    nueva = Sala(nombre=nombre.strip())
    db.add(nueva)
    db.flush()  # obtiene el id sin hacer commit todavia
    return nueva.id


def _buscar_o_crear_categoria(nombre: str, db: Session) -> Optional[int]:
    if not nombre:
        return None
    cat = db.query(Categoria).filter(
        Categoria.nombre.ilike(nombre.strip())
    ).first()
    if cat:
        return cat.id
    nueva = Categoria(nombre=nombre.strip())
    db.add(nueva)
    db.flush()
    return nueva.id


def _procesar_filas(
    filas: list[dict], db: Session
) -> tuple[int, list[ErrorFila]]:
    """Valida e inserta cada fila. Devuelve (importados, errores)."""
    importados = 0
    errores: list[ErrorFila] = []

    for idx, fila in enumerate(filas, start=2):  # start=2 porque fila 1 es el encabezado
        nombre = fila.get("nombre", "").strip()
        if not nombre:
            errores.append(ErrorFila(fila=idx, razon="Campo 'nombre' vacio o ausente."))
            continue

        try:
            stock_actual = int(float(fila.get("stock_actual", "")))
        except (ValueError, TypeError):
            errores.append(ErrorFila(
                fila=idx,
                razon=f"'stock_actual' no es un numero valido: '{fila.get('stock_actual')}'"
            ))
            continue

        try:
            stock_minimo = int(float(fila.get("stock_minimo", "")))
        except (ValueError, TypeError):
            errores.append(ErrorFila(
                fila=idx,
                razon=f"'stock_minimo' no es un numero valido: '{fila.get('stock_minimo')}'"
            ))
            continue

        if stock_actual < 0 or stock_minimo < 0:
            errores.append(ErrorFila(
                fila=idx, razon="Los valores de stock no pueden ser negativos."
            ))
            continue

        sala_id = _buscar_o_crear_sala(fila.get("sala", ""), db)
        categoria_id = _buscar_o_crear_categoria(fila.get("categoria", ""), db)

        insumo = Insumo(
            nombre=nombre,
            descripcion=fila.get("descripcion", "") or None,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            sala_id=sala_id,
            categoria_id=categoria_id,
        )
        db.add(insumo)
        importados += 1

    return importados, errores


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/plantilla")
def descargar_plantilla(
    usuario: Usuario = Depends(require_admin)
):
    """Descarga un CSV de ejemplo con el formato exacto que espera el importador.
    Solo accesible para administradores.
    """
    filas = [
        ["nombre", "descripcion", "stock_actual", "stock_minimo", "sala", "categoria"],
        ["Guantes de nitrilo talla M", "Caja x100 unidades", "50", "20",
         "Laboratorio Clinico", "Proteccion personal"],
        ["Mascarilla KN95", "", "30", "15", "Sala de Simulacion", "Proteccion personal"],
        ["Jeringa 5ml", "Con aguja 21G", "200", "50", "Sala de Procedimientos", "Insumos clinicos"],
        ["Alcohol isopropilico 70%", "Frasco 500ml", "10", "5", "", "Desinfeccion"],
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(filas)
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),  # BOM para Excel en Windows
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantilla_insumos_hestia.csv"}
    )


@router.post("/insumos", response_model=ImportarResponse)
def importar_insumos(
    archivo: UploadFile = File(...),
    codigo_totp: str = Form(...),
    usuario: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Importa insumos desde un archivo CSV o XLSX.

    Seguridad: requiere rol admin + codigo TOTP valido.
    El archivo es procesado solo si ambas verificaciones pasan.

    Columnas soportadas:
    - nombre (requerido)
    - stock_actual (requerido, entero)
    - stock_minimo (requerido, entero)
    - descripcion (opcional)
    - sala (opcional, se crea si no existe)
    - categoria (opcional, se crea si no existe)
    """
    # 1. Verificar TOTP antes de leer el archivo
    _verificar_totp(usuario, codigo_totp)

    # 2. Validar tipo de archivo
    nombre = archivo.filename or ""
    if not nombre.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan archivos .csv o .xlsx"
        )

    # 3. Leer y parsear
    contenido = archivo.file.read()
    filas_raw = _leer_filas(contenido, nombre)
    filas = _normalizar_encabezados(filas_raw)

    if not filas:
        raise HTTPException(status_code=400, detail="El archivo esta vacio.")

    # 4. Validar que esten las columnas requeridas
    columnas_archivo = set(filas[0].keys())
    faltantes = COLUMNAS_REQUERIDAS - columnas_archivo
    if faltantes:
        raise HTTPException(
            status_code=400,
            detail=f"Columnas requeridas faltantes: {', '.join(sorted(faltantes))}. "
                   f"Descarga la plantilla desde GET /importar/plantilla"
        )

    # 5. Procesar e insertar
    importados, errores = _procesar_filas(filas, db)

    # Solo hace commit si hubo al menos un insumo valido
    if importados > 0:
        db.commit()
    else:
        db.rollback()

    return ImportarResponse(
        importados=importados,
        omitidos=len(errores),
        errores=errores
    )
