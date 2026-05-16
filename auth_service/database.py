import os
from sqlmodel import SQLModel, create_engine, Session, Field # 👈 Agregamos Field aquí también
from redis import Redis

sqlite_file_name = "users.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

# CONFIGURACIÓN DE REDIS
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# 🔑 REESTABLECER EL MODELO USER QUE SE HABÍA PERDIDO
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session