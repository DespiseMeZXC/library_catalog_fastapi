from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Библиотечный каталог",
    description="API для управления библиотечным каталогом",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Корневой маршрут, возвращающий приветственное сообщение."""
    return {"message": "Добро пожаловать в API библиотечного каталога"}

if __name__ == "__main__":
    uvicorn.run("src.library_catalog.main:app", host="127.0.0.1", port=8000, reload=True) 
