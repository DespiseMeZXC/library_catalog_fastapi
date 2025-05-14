from fastapi import APIRouter, HTTPException, Depends, Path
from typing import List, Optional

from app.schemas.books import Book, BookCreate, BookUpdate, BookQueryParams
from app.crud.books import BookCrudService, CRUDServiceInterface
from app.dependencies.books import get_book_service
from app.utils.logger import setup_logger

# Настраиваем логгер для роутеров книг
logger = setup_logger("app.routers.books")

router = APIRouter(tags=["books"])


@router.get("/")
async def root():
    """Корневой маршрут, возвращающий приветственное сообщение."""
    logger.info("Запрос к корневому маршруту")
    return {"message": "Добро пожаловать в API библиотечного каталога"}

@router.get("/books", response_model=List[Book])
async def get_books(
    query_params: BookQueryParams = Depends(),
    service: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_service)
):
    """
    Получение списка всех книг с возможностью фильтрации.
    """
    books = service.get_all(
        offset=query_params.offset, 
        limit=query_params.limit, 
        author=query_params.author, 
        genre=query_params.genre, 
        availability=query_params.availability
    )
    
    logger.info(f"Найдено {len(books)} книг")
    return books

@router.get("/books/{book_id}", response_model=Book, tags=["books"])
async def get_book(
    book_id: int = Path(..., description="ID книги"),
    service: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_service)
):
    """
    Получение информации о конкретной книге по ID.
    """
    
    book = service.get_by_id(book_id)
    if book is None:
        logger.warning(f"Книга с ID {book_id} не найдена")
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    
    logger.info(f"Найдена книга: {book.title} (ID: {book.id})")
    return book

@router.post("/books", response_model=Book, status_code=201)
async def add_book(
    book: BookCreate,
    service: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_service)
):
    """
    Добавление новой книги в каталог.
    Также получает дополнительную информацию о книге из Open Library API.
    """
    created_book = await service.create(book)
    
    logger.info(f"Книга успешно добавлена: {created_book.title} (ID: {created_book.id})")
    return created_book

@router.put("/books/{book_id}", response_model=Book)
async def update_book(
    book_id: int = Path(..., description="ID книги"),
    book_update: Optional[BookUpdate] = None,
    service: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_service)
):
    """
    Обновление информации о книге.
    """
    logger.info(f"Запрос на обновление книги с ID: {book_id}")
    
    if book_update is None:
        logger.warning(f"Отсутствуют данные для обновления книги с ID: {book_id}")
        raise HTTPException(status_code=400, detail="Необходимо указать данные для обновления")
    
    updated_book = await service.update(book_id, book_update)
    if updated_book is None:
        logger.warning(f"Книга с ID {book_id} не найдена для обновления")
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    
    logger.info(f"Книга успешно обновлена: {updated_book.title} (ID: {updated_book.id})")
    return updated_book

@router.delete("/books/{book_id}")
async def delete_book(
    book_id: int = Path(..., description="ID книги"),
    service: CRUDServiceInterface[Book, BookCreate, BookUpdate] = Depends(get_book_service)
):
    """
    Удаление книги из каталога.
    """
    logger.info(f"Запрос на удаление книги с ID: {book_id}")
    
    if not service.delete(book_id):
        logger.warning(f"Книга с ID {book_id} не найдена для удаления")
        raise HTTPException(status_code=404, detail=f"Книга с ID {book_id} не найдена")
    
    logger.info(f"Книга с ID {book_id} успешно удалена")
    return {"message": f"Книга с ID {book_id} успешно удалена"}
