from fastapi import FastAPI, Depends, HTTPException, status, Response, Header
from pydantic import BaseModel
from db import session, get_db

from modelo.todo import todo
from sqlalchemy.orm import Session  # <--- Importante para Session
from sqlalchemy import text
from datetime import date





class Datos(BaseModel):
    rif: str
    mac: str

class DatosLicencia(BaseModel):
    rif: str
    mac: str
    estatus: bool | str
    fechaactual: date | None = None
    fechaultima: date | None = None
    licencia: str


app = FastAPI()



#@app.post('/')
#async def read_root(datos: Datos):
#    return {'Datos':datos,'Rif': datos.rif,'mac':datos.mac}

@app.get('/', status_code=status.HTTP_200_OK)
async def health_check(response: Response, db: Session = Depends(get_db)):
    health_status = {
        "api": "online",
        "database": "offline",
        "details": None
    }
    
    try:
        # Ejecutamos una consulta liviana de prueba a Neon.tech
        db.execute(text("SELECT 1"))
        health_status["database"] = "online"
        return health_status

    except Exception as e:
        # Si la BD falla o la conexión se cayó, cambiamos el código HTTP a 530 / 500
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        health_status["details"] = f"Error de conexión a la BD: {str(e)}"
        return health_status












@app.post('/consultaBody')
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




@app.get('/consulta')
async def buscar_licencia(
    rif: str,  # <--- Sin Header(...), ahora se lee de la URL (?rif=...)
    mac: str,  # <--- Sin Header(...), ahora se lee de la URL (&mac=...)
    db: Session = Depends(get_db)
):
    try:
        licencia = db.query(todo).filter(
            todo.rif == rif,
            todo.mac == mac
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )








@app.post('/guardar')
async def guardar_o_actualizar_licencia(
    datos: DatosLicencia,
    db: Session = Depends(get_db)
):
    try:
        # 1. Buscar si la licencia ya existe con esa combinación de RIF y MAC
        licencia = db.query(todo).filter(
            todo.rif == datos.rif,
            todo.mac == datos.mac
        ).first()

        # 2. SI EXISTE: Actualizar los campos
        if licencia:
            licencia.estatus = datos.estatus
            licencia.fechaactual = datos.fechaactual
            licencia.fechaultima = datos.fechaultima
            licencia.licencia = datos.licencia

            db.commit()
            db.refresh(licencia)

            return {
                "mensaje": "OK",
                "operacion": "UPDATE",
                "rif": licencia.rif,
                "mac": licencia.mac,
                "estatus": licencia.estatus
            }

        else:
            # 3. NO EXISTE: Crear e insertar nuevo registro
            nueva_licencia = todo(
                rif=datos.rif,
                mac=datos.mac,
                estatus=datos.estatus,
                fechaactual=datos.fechaactual or date.today(),
                fechaultima=datos.fechaultima or date.today(),
                licencia=datos.licencia
            )
            db.add(nueva_licencia)
            db.commit()
            db.refresh(nueva_licencia)

            return {
                "mensaje": "OK",
                "operacion": "INSERT",
                "rif": nueva_licencia.rif,
                "mac": nueva_licencia.mac,
                "estatus": nueva_licencia.estatus
            }

    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la licencia: {str(e)}"
        )