import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from typing import List, Optional
from pathlib import Path as FilePath

from .models import Book, BookCreate, BookUpdate, AvailabilityStatus
from .repositories import BookRepository
from .storage import Storage, FileStorage, JsonBinStorage


BOOKS_FILE_PATH = FilePath(__file__).parent.parent.parent / "data" / "books.json"
os.makedirs(os.path.dirname(BOOKS_FILE_PATH), exist_ok=True)

app = FastAPI(
    title="Библиотечный каталог",
    description="API для управления библиотечным каталогом",
    version="0.1.0"
)

def get_storage() -> Storage:
    """Функция-зависимость для получения хранилища данных."""
    storage_type = os.getenv("STORAGE_TYPE", "file")
    
    if storage_type == "file":
        return FileStorage(file_path=str(BOOKS_FILE_PATH))
    elif storage_type == "jsonbin":
        return JsonBinStorage()
    else:
        raise ValueError(f"Неизвестный тип хранилища: {storage_type}")

def get_book_repository(storage: Storage = Depends(get_storage)):
    """Функция-зависимость для получения репозитория книг."""
    return BookRepository(storage=storage)

@app.get("/")
async def root():
    """Корневой маршрут, возвращающий приветственное сообщение."""
    return {"message": "Добро пожаловать в API библиотечного каталога"}

@app.get("/books", response_model=List[Book], tags=["books"])
async def get_books(
    offset: int = Query(0, description="Сколько книг пропустить"),
    limit: int = Query(10, description="Максимальное количество книг для возврата"),
    author: Optional[str] = Query(None, description="Фильтр по автору"),
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    availability: Optional[AvailabilityStatus] = Query(None, description="Фильтр по доступности"),
    repo: BookRepository = Depends(get_book_repository)
):
    """
    Получение списка всех книг с возможностью фильтрации.
    """
    return repo.get_all(offset=offset, limit=limit, author=author, genre=genre, availability=availability)

@app.get("/books/{book_id}", response_model=Book, tags=["books"])
async def get_book(
    book_id: int = Path(..., description="ID книги"),
    repo: BookRepository = Depends(get_book_repository)
):
    """
    Получение информации о конкретной книге по ID.
    """
    book = repo.get_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    return book

@app.post("/books", response_model=Book, status_code=201, tags=["books"])
async def add_book(
    book: BookCreate,
    repo: BookRepository = Depends(get_book_repository)
):
    """
    Добавление новой книги в каталог.
    """
    return repo.create(book)

@app.put("/books/{book_id}", response_model=Book, tags=["books"])
async def update_book(
    book_id: int = Path(..., description="ID книги"),
    book_update: BookUpdate = None,
    repo: BookRepository = Depends(get_book_repository)
):
    """
    Обновление информации о книге.
    """
    if book_update is None:
        raise HTTPException(status_code=400, detail="Необходимо указать данные для обновления")
    
    updated_book = repo.update(book_id, book_update)
    if updated_book is None:
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    return updated_book

@app.delete("/books/{book_id}", tags=["books"])
async def delete_book(
    book_id: int = Path(..., description="ID книги"),
    repo: BookRepository = Depends(get_book_repository)
):
    """
    Удаление книги из каталога.
    """
    if not repo.delete(book_id):
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    return {"message": f"Книга с ID {book_id} успешно удалена"}

if __name__ == "__main__":
    uvicorn.run("src.library_catalog.main:app", host="127.0.0.1", port=8000, reload=True)
