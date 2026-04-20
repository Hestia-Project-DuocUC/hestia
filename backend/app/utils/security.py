from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
import bcrypt
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

def _prehash(password: str) -> bytes:
    return hashlib.sha256(password.encode()).hexdigest().encode("utf-8")

def hashear_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode("utf-8")

def verificar_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(_prehash(password), hash.encode("utf-8"))

def crear_token(data: dict) -> str:
    payload = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expiracion})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None