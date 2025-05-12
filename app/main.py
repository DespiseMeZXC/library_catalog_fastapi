import uvicorn
from fastapi import FastAPI

from .routers import books


app = FastAPI(
    title="Библиотечный каталог",
    description="API для управления библиотечным каталогом",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(books.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
