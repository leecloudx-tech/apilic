from fastapi import APIRouter

app = APIRouter

@app.get('/lic')
async def lic():
    return {"message": "Ruta licencia"}
