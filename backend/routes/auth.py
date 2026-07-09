from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, Bitacora
from schemas import UsuarioCreate, LoginRequest, TokenResponse, UsuarioResponse
import hashlib
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Autenticación"])

SECRET_KEY = os.getenv("SECRET_KEY", "smartinvoice-secret-key-2026")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_current_user(token: str, db: Session) -> Usuario:
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(Usuario).filter(Usuario.id == payload["user_id"]).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/register", response_model=TokenResponse)
def register(data: UsuarioCreate, db: Session = Depends(get_db)):
    existing = db.query(Usuario).filter(Usuario.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    user = Usuario(
        username=data.username,
        password_hash=hash_password(data.password),
        nombre=data.nombre,
        email=data.email
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log = Bitacora(
        usuario_id=user.id, accion="REGISTRO_USUARIO",
        documento="-", estado="Éxito",
        resultado=f"Usuario {data.username} registrado"
    )
    db.add(log)
    db.commit()

    token = create_token(user.id)
    return TokenResponse(
        access_token=token,
        usuario=UsuarioResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == data.username).first()
    if not user or user.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    log = Bitacora(
        usuario_id=user.id, accion="LOGIN",
        documento="-", estado="Éxito",
        resultado=f"Login exitoso: {data.username}"
    )
    db.add(log)
    db.commit()

    token = create_token(user.id)
    return TokenResponse(
        access_token=token,
        usuario=UsuarioResponse.model_validate(user)
    )
