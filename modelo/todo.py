from sqlalchemy import Boolean, Column, Integer, String, Date, text
from sqlalchemy.orm import declarative_base

from db import engine

Base = declarative_base()

class todo(Base):
    __tablename__ = "licencias"

    id = Column(Integer, primary_key=True, index=True)
    rif = Column(String)
    razonsocial = Column(String)
    mac = Column(String)
    fechaultima = Column(Date)
    estatus = Column(Integer)
    licencia = Column(String)
    tipoempresa = Column(Integer)
    estaciones = Column(Integer)

Base.metadata.create_all(engine)



def actualizar_esquema():
    sql_script = text("""
        ALTER TABLE licencias 
        ADD COLUMN IF NOT EXISTS estaciones INTEGER,
        ADD COLUMN IF NOT EXISTS tipoempresa INTEGER,
        ADD COLUMN IF NOT EXISTS razonsocial VARCHAR,
        ADD COLUMN IF NOT EXISTS licencia VARCHAR;
    """)
    
    with engine.connect() as conexion:
        conexion.execute(sql_script)
        conexion.commit()

# Ejecuta la actualización de columnas
actualizar_esquema()

