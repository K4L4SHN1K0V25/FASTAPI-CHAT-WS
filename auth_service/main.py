from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import init_db, get_session, User, redis_client
from auth_utils import hash_password, verify_password, create_access_token, decode_token
from pydantic import BaseModel, Field

app = FastAPI(title="Authentication Service", version="1.0.0")

# Inicializar la base de datos al arrancar el contenedor
@app.on_event("startup")
def on_startup():
    init_db()

# Esquema para la creación de usuarios
class UserRegister(BaseModel):
    username: str
    password: str

# 1. Endpoint de Registro
@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, session: Session = Depends(get_session)):
    # Verificar si el usuario ya existe
    statement = select(User).where(User.username == user_data.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado."
        )
    
    # Crear nuevo usuario con contraseña encriptada
    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    return {"message": "Usuario registrado exitosamente."}

# 2. Endpoint de Login (Emisión de JWT + Registro en Redis)
@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar el token
    access_token = create_access_token(data={"sub": user.username})
    
    # 🔐 PERSISTENCIA COMPARTIDA EN REDIS
    # Guardamos la sesión usando el token como LLAVE y el username como VALOR
    # ex=3600 le dice a Redis que borre esta clave automáticamente en 1 hora (3600 segundos)
    try:
        redis_client.set(f"session:{access_token}", user.username, ex=3600)
    except Exception as e:
        print(f"⚠️ Alerta: No se pudo guardar la sesión en Redis: {e}")
        # Continuamos de todos modos para no romper el flujo del usuario si Redis parpadea
    
    return {"access_token": access_token, "token_type": "bearer"}

# 3. Endpoint de Validación (El que usará nuestro Chat Service internamente)
@app.get("/auth/validate")
def validate_token(token: str):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado."
        )
    return {"valid": True, "username": payload.get("sub")}

# Esquema corregido para la creación de usuarios
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)