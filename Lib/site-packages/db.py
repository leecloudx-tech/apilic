from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker,DeclarativeBase




#url = URL.create(
#    drivername="postgresql+psycopg2",
#    username="postgres",
#    password="postgres",
#    host="localhost",
#    database="cmp",
#   port=5432,
#)

url = URL.create(
drivername="postgresql+psycopg2",
    username="neondb_owner",
    password="npg_C2wQHSxlrzM9",
    host="ep-orange-sun-ayt5eg55-pooler.c-5.us-east-2.aws.neon.tech",
    database="neondb",
    port=5432,
    query={"sslmode": "require"},  # Requerido por Neon
)

engine = create_engine(url)
Session = sessionmaker(bind=engine)
session = Session()


class Base(DeclarativeBase):
    pass

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()