import os
from fastapi import APIRouter, HTTPException, Depends, Path
from typing import List

from app.schemas.books import Book, BookCreate, BookUpdate, BookQueryParams
from app.crud.service import BookCrudService, CRUDServiceInterface
from app.database import RepositoryInterface, FileRepository, JsonBinRepository, DbPostgresRepository


router = APIRouter(tags=["books"])


def get_storage() -> RepositoryInterface:
    """Функция-зависимость для получения хранилища данных."""
    storage_type = os.getenv("STORAGE_TYPE", "file")
    
    if storage_type == "file":
        return FileRepository()
    elif storage_type == "jsonbin":
        return JsonBinRepository()
    elif storage_type == "db":
        return DbPostgresRepository()
    else:
        raise ValueError(f"Неизвестный тип хранилища: {storage_type}")

def get_book_repository(storage: RepositoryInterface = Depends(get_storage)):
    """Функция-зависимость для получения репозитория книг."""
    return BookCrudService(storage=storage)

@router.get("/")
async def root():
    """Корневой маршрут, возвращающий приветственное сообщение."""
    return {"message": "Добро пожаловать в API библиотечного каталога"}

@router.get("/books", response_model=List[Book], tags=["books"])
async def get_books(
    query_params: BookQueryParams = Depends(),
    repo: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_repository)
):
    """
    Получение списка всех книг с возможностью фильтрации.
    """
    return repo.get_all(offset=query_params.offset, limit=query_params.limit, author=query_params.author, genre=query_params.genre, availability=query_params.availability)

@router.get("/books/{book_id}", response_model=Book, tags=["books"])
async def get_book(
    book_id: int = Path(..., description="ID книги"),
    repo: BookCrudService = Depends(get_book_repository)
):
    """
    Получение информации о конкретной книге по ID.
    """
    book = repo.get_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    return book

@router.post("/books", response_model=Book, status_code=201, tags=["books"])
async def add_book(
    book: BookCreate,
    repo: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_repository)
):
    """
    Добавление новой книги в каталог.
    Также получает дополнительную информацию о книге из Open Library API.
    """
    return repo.create(book)

@router.put("/books/{book_id}", response_model=Book, tags=["books"])
async def update_book(
    book_id: int = Path(..., description="ID книги"),
    book_update: BookUpdate = None,
    repo: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_repository)
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

@router.delete("/books/{book_id}", tags=["books"])
async def delete_book(
    book_id: int = Path(..., description="ID книги"),
    repo: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_repository)
):
    """
    Удаление книги из каталога.
    """
    if not repo.delete(book_id):
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    return {"message": f"Книга с ID {book_id} успешно удалена"}
