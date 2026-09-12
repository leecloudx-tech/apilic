from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from db import session, get_db

from modelo.todo import todo
from sqlalchemy.orm import Session  # <--- Importante para Session



class Datos(BaseModel):
    rif: str
    mac: str

app = FastAPI()



@app.post('/')
async def read_root(datos: Datos):
    return {'Datos':datos,'Rif': datos.rif,'mac':datos.mac}




@app.post('/test')
async def buscar_licencia(
    datos: Datos, 
    db: Session = Depends(get_db)
):
    try:
        licencia = db.query(todo).filter(
            todo.rif == datos.rif,
            todo.mac == datos.mac
        ).first()

        if not licencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Licencia no registrada o inactiva"
            )

        return {
            "status": licencia.estatus, 
            "rif": licencia.rif, 
            "mac": licencia.mac,
            "fecha servidor": licencia.fechaactual,
            "fecha Ultima": licencia.fechaultima
            }

    except Exception as e:
        # Esto te devolverá el mensaje exacto del error en el JSON de respuesta
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )
