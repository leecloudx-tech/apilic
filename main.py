from fastapi import FastAPI, Depends, HTTPException, status, Response, Header
from pydantic import BaseModel
from db import session, get_db

from modelo.todo import todo
from sqlalchemy.orm import Session  # <--- Importante para Session
from sqlalchemy import text
from datetime import date, datetime





class Datos(BaseModel):
    rif: str
    mac: str

class DatosLicencia(BaseModel):
    rif: str
    razonsocial: str
    mac: str | None = None
    estatus: str 
    fechaultima: date | None = None
    licencia: str | None = None
    tipoempresa: str | None = None

class DatosActualizar(BaseModel):
    rif: str
    fechaultima: date
    mac: str

app = FastAPI()



#@app.post('/')
#async def read_root(datos: Datos):
#    return {'Datos':datos,'Rif': datos.rif,'mac':datos.mac}



#COMPROBAR QUE ESTA ACTIVA LA API
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







#CONSULTA USANDO UN BODY JSON
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



#CONSULTA USANDO HEADER, SOLO PARA WINDEV17
@app.get('/consulta')
async def buscar_licencia(
    rif: str,
 #   mac: str,
    db: Session = Depends(get_db)
):
    try:
        licencia = db.query(todo).filter(
            todo.rif == rif,
#            todo.mac == mac
        ).first()

        if not licencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Licencia no registrada"
            )

        return {
            "status": licencia.estatus, 
            "rif": licencia.rif,
            "razonsocial": licencia.razonsocial,
            "licencia": licencia.licencia,
            "fecha Ultima": licencia.fechaultima,
            "tipo de Empresa": licencia.tipoempresa
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )



#CREA O ACTUALIZA LA LICENCIA
@app.post('/guardar')
async def guardar_o_actualizar_licencia(
    datos: DatosLicencia,
    db: Session = Depends(get_db)
):
    try:
        # 1. Buscar si la licencia ya existe con el RIF
        licencia = db.query(todo).filter(
            todo.rif == datos.rif,
 #           todo.mac == datos.mac
        ).first()

        # 2. SI EXISTE: Actualizar los campos
        if licencia:
            licencia.estatus = datos.estatus
            licencia.fechaultima = datos.fechaultima
            licencia.tipoempresa = datos.tipoempresa
            licencia.mac = datos.mac


            db.commit()
            db.refresh(licencia)

            return {
                "mensaje": "OK",
                "operacion": "UPDATE",
                "rif": licencia.rif,
                "estatus": licencia.estatus
            }

        else:
            # 3. NO EXISTE: Crear e insertar nuevo registro
            nueva_licencia = todo(
                rif = datos.rif,
                razonsocial = datos.razonsocial,
                mac = datos.mac,
                estatus = datos.estatus,
                fechaultima = datos.fechaultima or date.today(),
                licencia = datos.licencia,
                tipoempresa = datos.tipoempresa

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




#Actualizo la ultima conexion y la mac
@app.get('/combinar')
async def combinar(
    rif1: str,
    mac1: str,
    fechaultima1: str,
    db: Session = Depends(get_db)
):

#SE VALIDA LA FECHA
    try:
        fecha_validada: date = datetime.strptime(fechaultima1, "%Y%m%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido en el Header. Debe ser de 8 dígitos: AAAAMMDD (Ejemplo: 20260101)"
        )

# SE BUSCA EL REGISTRO 
    try:
        licencia = db.query(todo).filter(
            todo.rif == rif1,
        ).first()

        if not licencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Licencia no registrada"
            )

        licencia.mac = mac1
        licencia.fechaultima = fecha_validada

        db.commit()
        db.refresh(licencia)

        return {
            "status": licencia.estatus, 
            "rif": licencia.rif,
            "mac": licencia.mac,
            "fecha Ultima": licencia.fechaultima
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de fallo
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )

