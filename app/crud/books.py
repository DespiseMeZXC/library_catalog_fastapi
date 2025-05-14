from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel
from app.schemas.books import Book, BookCreate, BookUpdate, AvailabilityStatus, EnrichBookData
from app.interfaces.books import RepositoryInterface, CRUDServiceInterface
from app.services.openlibrary_api import OpenLibraryApi
from app.utils.logger import setup_logger
from app.schemas.books import StorageType, BookFilter

# Настраиваем логгер для CRUD сервиса
logger = setup_logger("app.crud.service")


class BookCrudService(CRUDServiceInterface[Book, BookCreate, BookUpdate]):
    """
    Сервис для работы с книгами. Обеспечивает операции CRUD для книг. Включая обогащение данных из Open Library API.
    """
    def __init__(self, storage: RepositoryInterface, openlibrary_api: OpenLibraryApi):
        """
        Инициализация сервиса.
        :param storage: Хранилище данных
        """
        self.storage = storage
        self.openlibrary_api = openlibrary_api
        logger.debug(f"Инициализирован BookCrudService с хранилищем типа {type(storage).__name__}")
    
    @staticmethod
    def _convert_model_to_schema(data: Dict[str, Any], model: Type[BaseModel]) -> Book:
        """Конвертация модели в схему."""
        data_dict = {
            "id": data.id,
            "title": data.title,
            "author": data.author,
            "publication_year": data.publication_year,
            "genre": data.genre,
            "pages": data.pages,
            "availability": data.availability,
            "cover_url": data.cover_url,
            "description": data.description,
            "rating": data.rating
        }
        return model(**data_dict)
    
    def get_all(self, offset: int = 0, limit: int = 100, 
                author: Optional[str] = None, 
                genre: Optional[str] = None, 
                availability: Optional[AvailabilityStatus] = None, 
                **filters) -> List[Book]:
        """
        Получение списка книг с возможностью фильтрации.
        
        :param offset: Сколько книг пропустить (для пагинации)
        :param limit: Максимальное количество книг для возврата
        :param author: Фильтр по автору
        :param genre: Фильтр по жанру
        :param availability: Фильтр по доступности
        :return: Список книг
        """
        
        if self.storage.storage_type == StorageType.DB:
            # Для БД используем встроенную фильтрацию
            filter_params = {}
            if author:
                filter_params["author"] = author
            if genre:
                filter_params["genre"] = genre
            if availability:
                filter_params["availability"] = availability
            
            books_data = self.storage.load_data(offset=offset, limit=limit, **filter_params)
            
            if books_data == []:
                return []
            filtered_books = [self._convert_model_to_schema(book_data, Book) for book_data in books_data]
            return filtered_books
        else:
            logger.debug("Использование JSON для получения списка книг")
            # Для JSON хранилища загружаем данные и фильтруем
            data = self.storage.load_data()
            filtered_books = []
            
            for book_data in data.get("books", []):
                if author and book_data["author"].lower() != author.lower():
                    continue
                if genre and book_data["genre"].lower() != genre.lower():
                    continue
                if availability and book_data["availability"] != availability:
                    continue
                
                book = Book(**book_data)
                filtered_books.append(book)
        
            return filtered_books[offset:offset + limit]
    
    def get_by_id(self, book_id: int) -> Optional[Book]:
        """
        Получение книги по ID.
        
        :param book_id: ID книги
        :return: Данные книги или None, если книга не найдена
        """
        
        if self.storage.storage_type == StorageType.DB:
            book_data = self.storage.get_data_by_id(book_id)
            if book_data:
                # Преобразуем объект SQLAlchemy в словарь, а затем в Pydantic модель
                book = self._convert_model_to_schema(book_data, Book)
                return book
        else:
            # Для JSON хранилища ищем книгу по ID
            data = self.storage.load_data()
            for book_data in data.get("books", []):
                if book_data["id"] == book_id:
                    book = Book(**book_data)
                    return book
        
        return None
    
    async def create(self, book: BookCreate) -> Book:
        """
        Создание новой книги.
        
        :param book: Данные книги
        :return: Созданная книга с ID
        """
        
        
        book_dict = book.model_dump()
        book_dict["id"] = self.storage._get_next_id()
        
        # Обогащаем данные книги информацией из Open Library API
        enriched_data = await self.openlibrary_api.enrich_book_data(book_dict["title"])
        logger.debug(f"Получены обогащенные данные: {enriched_data}")
        
        # Добавляем полученные данные к книге
        if enriched_data.cover_url:
            book_dict["cover_url"] = str(enriched_data.cover_url)
        if enriched_data.description:
            book_dict["description"] = enriched_data.description
        if enriched_data.rating:
            book_dict["rating"] = enriched_data.rating
        new_book = Book(**book_dict)
        if self.storage.storage_type == StorageType.DB:
            # Для БД сохраняем только новую книгу
            self.storage.save_data(book_dict)
        else:
            # Для JSON хранилища добавляем книгу в список и обновляем next_id
            
            data = self.storage.load_data()
            books = data.get("books", [])
            books.append(book_dict)
            data["books"] = books
            data = self.storage._update_next_id(data)
            self.storage.save_data(data)
        return new_book
    
    async def update(self, book_id: int, book_update: BookUpdate) -> Optional[Book]:
        """
        Обновление данных книги.
        
        :param book_id: ID книги
        :param book_update: Данные для обновления (только непустые поля будут обновлены)
        :return: Обновленная книга или None, если книга не найдена
        """
        
        # Получаем текущие данные книги
        current_book = None
        
        if self.storage.storage_type == StorageType.DB:
            # Для БД используем метод get_data_by_id
            current_book = self.storage.get_data_by_id(book_id)
        else:
            # Для JSON хранилища ищем книгу в загруженных данных
            data = self.storage.load_data()
            for book_data in data.get("books", []):
                if book_data["id"] == book_id:
                    current_book = book_data
                    break
        
        if not current_book:
            logger.warning(f"Книга с ID {book_id} не найдена для обновления")
            return None
        
        # Получаем данные для обновления
        update_data = book_update.model_dump(exclude_unset=True)
        
        # Если используем JSON хранилище, создаем полный словарь с обновленными данными
        if self.storage.storage_type != StorageType.DB:
            book_dict = current_book.copy()
            book_dict.update(update_data)
        else:
            # Для БД достаточно только обновляемых полей
            book_dict = update_data
        
        book_dict["id"] = book_id
        
        # Если изменилось название, обновляем метаданные из Open Library
        if "title" in update_data:
            enriched_data = await self.openlibrary_api.enrich_book_data(update_data["title"])
            # Обновляем метаданные, если они получены
            if enriched_data.cover_url:
                book_dict["cover_url"] = str(enriched_data.cover_url)
            if enriched_data.description:
                book_dict["description"] = enriched_data.description
            if enriched_data.rating:
                book_dict["rating"] = enriched_data.rating
            book_dict["asdasd"] = 5
        if self.storage.storage_type == StorageType.DB:
            updated_book_dict = self.storage.update_data(book_dict)
            if updated_book_dict:
                return Book(**updated_book_dict)
        else:
            data = self.storage.load_data()
            books = data.get("books", [])
            
            for i, book_data in enumerate(books):
                if book_data["id"] == book_id:
                    books[i] = book_dict
                    data["books"] = books
                    self.storage.save_data(data)
                    return Book(**book_dict)
        
        return None
    
    def delete(self, book_id: int) -> bool:
        """
        Удаление книги по ID.
        
        :param book_id: ID книги
        :return: True, если книга успешно удалена, иначе False
        """
        
        # Проверяем наличие книги
        book = self.get_by_id(book_id)
        if not book:
            return False
        
        if self.storage.storage_type == StorageType.DB:
            self.storage.delete_data({"id": book_id})
        else:
            data = self.storage.load_data()
            books = data.get("books", [])
            
            data["books"] = [book_data for book_data in books if book_data["id"] != book_id]
            self.storage.save_data(data)
        
        return True
