import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


load_dotenv()


USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")


if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
    raise ValueError(
        "Faltan variables de configuración de la base de datos"
    )


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=USER,
    password=PASSWORD,
    host=HOST,
    port=int(PORT),
    database=DBNAME,
    query={
        "sslmode": "require",
    },
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
