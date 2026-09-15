from fastapi import FastAPI, Depends, HTTPException, status, Response, Header
from pydantic import BaseModel
from db import session, get_db
import calendar
from modelo.todo import todo
from sqlalchemy.orm import Session  # <--- Importante para Session
from sqlalchemy import text
from datetime import date, datetime
from Funciones import ErroresVarios
from fastapi.middleware.cors import CORSMiddleware




class Datos(BaseModel):
    rif: str | None = None
    tipo: str

class DatosLicencia(BaseModel):
    rif: str
    razonsocial: str
    mac: str | None = None
    estatus: str 
    fechaultima: date | None = None
    licencia: str | None = None
    tipoempresa: str | None = None
    estaciones: int | None = None
    fechapago: date | None = None

class DatosActualizar(BaseModel):
    rif: str
    fechaultima: date
    mac: str



app = FastAPI()
# Configuración de CORS
origins = [
    "http://localhost:5173",  # Puerto por defecto de Vite / React
    "http://127.0.0.1:5173",
    "https://webapi-m1cw.onrender.com/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # O usa ["*"] para permitir cualquier origen en desarrollo
    allow_credentials=True,
    allow_methods=["*"],         # Permite OPTIONS, POST, GET, PUT, DELETE, etc.
    allow_headers=["*"],         # Permite Content-Type y otros encabezados
)




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
        if datos.tipo == '1' :
            texto = datos.rif
            texto = texto.upper()
            texto = texto.replace("-", "")

            licencia = db.query(todo).filter(
                todo.rif == texto,
            ).first()

            if not licencia:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Licencia no registrada o inactiva"
                )

            return {
                "id": licencia.id if hasattr(licencia, 'id') else licencia.rif,
                "status": licencia.estatus,
                "rif": licencia.rif,
                "razonsocial": licencia.razonsocial,
                "licencia": licencia.licencia,
                "fechaultima": str(licencia.fechaultima) if licencia.fechaultima else "",
                "fechapago": str(licencia.fechapago) if licencia.fechapago else "",
                "tipoempresa": licencia.tipoempresa,
                "estaciones": licencia.estaciones
                }
        elif datos.tipo == '2':
            licencias = db.query(todo).all()
            resultado = []
            for lic in licencias:

                # 3. Construir el diccionario de cada elemento
                resultado.append({
                    "id": lic.id if hasattr(lic, 'id') else lic.rif,
                    "status": lic.estatus,
                    "rif": lic.rif,
                    "razonsocial": lic.razonsocial,
                    "licencia": lic.licencia,
                    "fechaultima": str(lic.fechaultima) if lic.fechaultima else "",
                    "fechapago": str(lic.fechapago) if lic.fechapago else "",
                    "tipoempresa": lic.tipoempresa,
                    "estaciones": lic.estaciones
                })

            return resultado
        else:
            ErroresVarios(400,"Tipo de consulta no válido. Usa '1' o '2'.")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        ErroresVarios(500, mensaje_custom=f"Error interno en la base de datos o servidor: {str(e)}")




#CONSULTA USANDO HEADER, SOLO PARA WINDEV17
@app.get('/consulta')
async def buscar_licencia(
    rif: str,
    lic: str,
    tip: int,
    db: Session = Depends(get_db)
):
    try:
        match tip:
            case 1: #BUSCA POR RIF
                licencia = db.query(todo).filter(
                    todo.rif == rif
                ).first()

            case 2: #BUSCA POR RIF Y LICENCIA
                licencia = db.query(todo).filter(
                    todo.rif == rif,
                    todo.licencia == lic
                ).first()
                estatus_calculado = VerificarStatus(licencia, db)

                
                if not estatus_calculado:
                    ErroresVarios(404,"No se pudo comprobar el estatus de su licencia")


            case 3: # Busca todo
                licencias = db.query(todo).all()

                resultado = []
                for lic in licencias:

                    # 3. Construir el diccionario de cada elemento
                    resultado.append({
                        "id": lic.id if hasattr(lic, 'id') else lic.rif,
                        "status": estatus_calculado,
                        "rif": lic.rif,
                        "razonsocial": lic.razonsocial,
                        "licencia": lic.licencia,
                        "fechaultima": str(lic.fechaultima) if lic.fechaultima else "",
                        "fechapago": str(lic.fechapago) if lic.fechapago else "",
                        "tipoempresa": lic.tipoempresa,
                        "estaciones": lic.estaciones
                    })

                return resultado
            case _: # ERROR NO SE ENVIO NADA
                ErroresVarios(500)


        if not licencia:
            ErroresVarios(404,"No se encontro una licencia valida")

        return {
            "status": licencia.estatus, 
            "rif": licencia.rif,
            "razonsocial": licencia.razonsocial,
            "licencia": licencia.licencia,
            "fecha Ultima": licencia.fechaultima,
            "tipo de Empresa": licencia.tipoempresa,
            "Nro Estaciones" : licencia.estaciones,
            "mensaje" : "OK",
            "Fecha Ultimo pago" : licencia.fechapago
        }

    except HTTPException:
        raise
    except Exception as e:
        ErroresVarios(500)



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
        ).first()

        # 2. SI EXISTE: Actualizar los campos
        if licencia:
            texto = datos.razonsocial
            texto = texto.replace(",", "")
            licencia.razonsocial = texto.upper() or licencia.razonsocial
            licencia.estatus = datos.estatus
            licencia.fechaultima = datos.fechaultima
            licencia.tipoempresa = datos.tipoempresa
            licencia.estaciones = datos.estaciones
            hoy = datos.fechapago
            _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month) 
            licencia.fechapago = date(hoy.year, hoy.month, ultimo_dia)


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
            hoy = date.today()
            _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month)

            nueva_licencia = todo(
                rif = datos.rif,
                razonsocial = datos.razonsocial,
                mac = datos.mac,
                estatus = datos.estatus,
                fechaultima = datos.fechaultima or date.today(),
                licencia = datos.licencia,
                tipoempresa = datos.tipoempresa,
                estaciones = datos.estaciones or date(hoy.year, hoy.month, ultimo_dia)
            )

            db.add(nueva_licencia)
            db.commit()
            db.refresh(nueva_licencia)

            return {
                "mensaje": "OK",
                "operacion": "INSERT",
                "rif": nueva_licencia.rif,
                "estatus": nueva_licencia.estatus
            }

    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error
        ErroresVarios(500,"Fallo de conexion a la base de datos")



#FUNCION QUE EVALUA LA FECHA Y ACTUALIZA EL ESTATUS 
def VerificarStatus(licencia: todo, db: Session) -> int:

    fecha_pago = licencia.fechapago

    if not fecha_pago:
        return False
    else:
        # Convertir a date si viene como string
        if isinstance(fecha_pago, str):
            fecha_pago = datetime.strptime(fecha_pago, "%Y-%m-%d").date()

        fecha_actual = date.today()
        dias_transcurridos = (fecha_actual - fecha_pago).days

        # Menos de 15 días -> 1, 15 días o más -> 2
        nuevo_estatus = 1 if dias_transcurridos < 15 else 2

    # Actualizar la base de datos solo si el estatus cambió
    if licencia.estatus != nuevo_estatus:
        licencia.estatus = nuevo_estatus
        db.commit()
        db.refresh(licencia)

    return True



