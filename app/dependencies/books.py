import os
from fastapi import Depends

from app.database import RepositoryInterface, FileRepository, JsonBinRepository, DbPostgresRepository
from app.services.openlibrary_api import OpenLibraryApi
from app.crud.books import BookCrudService
from app.utils.logger import setup_logger


logger = setup_logger("app.dependencies.books")

def get_storage() -> RepositoryInterface:
    """Функция-зависимость для получения хранилища данных."""
    storage_type = os.getenv("STORAGE_TYPE", "file")
    logger.debug(f"Использование хранилища данных: {storage_type}")
    
    if storage_type == "file":
        return FileRepository()
    elif storage_type == "jsonbin":
        return JsonBinRepository()
    elif storage_type == "db":
        return DbPostgresRepository()
    else:
        logger.error(f"Неизвестный тип хранилища: {storage_type}")
        raise ValueError(f"Неизвестный тип хранилища: {storage_type}")

def get_openlibrary_api():
    return OpenLibraryApi()

def get_book_service(storage: RepositoryInterface = Depends(get_storage), openlibrary_api: OpenLibraryApi = Depends(get_openlibrary_api)):
    """Функция-зависимость для получения репозитория книг."""
    logger.debug("Создание репозитория книг")
    return BookCrudService(storage=storage, openlibrary_api=openlibrary_api)
