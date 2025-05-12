import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import books
from .utils.logger import setup_logger

# Настраиваем логгер для основного модуля
logger = setup_logger("app.main")

app = FastAPI(
    title="Библиотечный каталог",
    description="API для управления библиотечным каталогом",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Включаем роуты
app.include_router(books.router)

logger.info("Приложение успешно настроено")

@app.on_event("startup")
async def startup_event():
    logger.info("Приложение запущено")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Приложение остановлено")

if __name__ == "__main__":
    logger.info("Запуск сервера разработки")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
