from fastapi import FastAPI, Depends, HTTPException, status, Response, Header
from typing import NoReturn, Optional


##Funcion de errores
def ErroresVarios(tipo_error: int, mensaje_custom: Optional[str] = None) -> NoReturn:

    match tipo_error:
        case 404:  # No encontrado (404)
            codigo = status.HTTP_404_NOT_FOUND
            mensaje_defecto = "No se pudo comprobar el estatus de su licencia"

        case 400:  # Datos de entrada no válidos (400)
            codigo = status.HTTP_400_BAD_REQUEST
            mensaje_defecto = "Parámetros o datos de consulta no válidos"

        case 401:  # No autorizado / Credenciales incorrectas (401)
            codigo = status.HTTP_401_UNAUTHORIZED
            mensaje_defecto = "No autorizado para realizar esta acción"

        case 403:  # Licencia suspendida o prohibida (403)
            codigo = status.HTTP_403_FORBIDDEN
            mensaje_defecto = "La licencia se encuentra suspendida o inactiva"

        case _:  # Error interno del servidor (500 por defecto)
            codigo = status.HTTP_500_INTERNAL_SERVER_ERROR
            mensaje_defecto = "Error interno del servidor"

    detalle = mensaje_custom if mensaje_custom else mensaje_defecto

    raise HTTPException(status_code=codigo, detail=detalle)