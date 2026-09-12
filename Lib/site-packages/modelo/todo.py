from sqlalchemy import Boolean, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

from db import engine

Base = declarative_base()

class todo(Base):
    __tablename__ = "licencias"

    id = Column(Integer, primary_key=True, index=True)
    rif = Column(String)
    mac = Column(String)
    fechaactual = Column(Date)
    fechaultima = Column(Date)
    estatus = Column(Integer)

Base.metadata.create_all(engine)

