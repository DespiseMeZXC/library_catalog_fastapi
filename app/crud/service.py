from typing import List, Optional

from app.schemas.books import Book, BookCreate, BookUpdate, AvailabilityStatus
from app.interfaces.books import RepositoryInterface, CRUDServiceInterface
from app.database import DbPostgresRepository
from app.services.openlibrary_api import OpenLibraryApi


class BookCrudService(CRUDServiceInterface[Book, BookCreate, BookUpdate]):
    """
    Репозиторий для работы с книгами. Обеспечивает операции CRUD для книг.
    """
    def __init__(self, storage: RepositoryInterface):
        """
        Инициализация репозитория.
        
        :param storage: Хранилище данных
        """
        self.storage = storage
        self.openlibrary_api = OpenLibraryApi()  # Инициализация объекта OpenLibraryApi
    
    @property
    def is_db_storage(self) -> bool:
        """Проверка типа хранилища данных."""
        return isinstance(self.storage, DbPostgresRepository)
    
    def _get_next_id(self) -> int:
        """Получение следующего ID для новой книги."""
        if self.is_db_storage:
            return self.storage.get_next_id()
        else:
            # Для JSON хранилища загружаем только next_id
            data = self.storage.load_data()
            return data.get("next_id", 1)
    
    def _update_next_id(self, next_id: int) -> None:
        """Обновление счетчика ID в хранилище."""
        if not self.is_db_storage:
            data = self.storage.load_data()
            data["next_id"] = next_id
            self.storage.save_data(data)
    
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
        if self.is_db_storage:
            # Для БД используем встроенную фильтрацию
            books_data = self.storage.load_data()
            filtered_books = []
            
            for book_data in books_data:
                if author and book_data.author.lower() != author.lower():
                    continue
                if genre and book_data.genre.lower() != genre.lower():
                    continue
                if availability and book_data.availability != availability:
                    continue
                
                # Преобразуем объект SQLAlchemy в словарь, а затем в Pydantic модель
                book_dict = {
                    "id": book_data.id,
                    "title": book_data.title,
                    "author": book_data.author,
                    "publication_year": book_data.publication_year,
                    "genre": book_data.genre,
                    "pages": book_data.pages,
                    "availability": book_data.availability,
                    "cover_url": book_data.cover_url,
                    "description": book_data.description,
                    "rating": book_data.rating
                }
                filtered_books.append(Book(**book_dict))
        else:
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
        
        if self.is_db_storage:
            book_data = self.storage.get_data_by_id(book_id)
            if book_data:
                # Преобразуем объект SQLAlchemy в словарь, а затем в Pydantic модель
                book_dict = {
                    "id": book_data.id,
                    "title": book_data.title,
                    "author": book_data.author,
                    "publication_year": book_data.publication_year,
                    "genre": book_data.genre,
                    "pages": book_data.pages,
                    "availability": book_data.availability,
                    "cover_url": book_data.cover_url,
                    "description": book_data.description,
                    "rating": book_data.rating
                }
                book = Book(**book_dict)
                return book
        else:
            # Для JSON хранилища ищем книгу по ID
            data = self.storage.load_data()
            for book_data in data.get("books", []):
                if book_data["id"] == book_id:
                    book = Book(**book_data)
                    return book
        
        return None
    
    def create(self, book: BookCreate) -> Book:
        """
        Создание новой книги.
        
        :param book: Данные книги
        :return: Созданная книга с ID
        """
        next_id = self._get_next_id()
        
        book_dict = book.model_dump()
        book_dict["id"] = next_id
        
        # Обогащаем данные книги информацией из Open Library API
        cover_url, description, rating = self.openlibrary_api.enrich_book_data(
            book_dict["title"],
        )
        
        # Добавляем полученные данные к книге
        if cover_url:
            book_dict["cover_url"] = cover_url
        if description:
            book_dict["description"] = description
        if rating:
            book_dict["rating"] = rating
        
        new_book = Book(**book_dict)
        
        if self.is_db_storage:
            # Для БД сохраняем только новую книгу
            self.storage.save_data(book_dict)
        else:
            # Для JSON хранилища добавляем книгу в список и обновляем next_id
            data = self.storage.load_data()
            books = data.get("books", [])
            books.append(book_dict)
            data["books"] = books
            data["next_id"] = next_id + 1
            self.storage.save_data(data)
        
        return new_book
    
    def update(self, book_id: int, book_update: BookUpdate) -> Optional[Book]:
        """
        Обновление данных книги.
        
        :param book_id: ID книги
        :param book_update: Данные для обновления (только непустые поля будут обновлены)
        :return: Обновленная книга или None, если книга не найдена
        """
        # Получаем текущие данные книги
        book = self.get_by_id(book_id)
        if not book:
            return None
        
        # Получаем данные для обновления
        update_data = book_update.model_dump(exclude_unset=True)
        
        # Создаем обновленный словарь данных книги
        book_dict = book.model_dump()
        for field, value in update_data.items():
            if value is not None:
                book_dict[field] = value
        
        # Если изменился автор или название, обновляем метаданные из Open Library
        if "title" in update_data:
            cover_url, description, rating = self.openlibrary_api.enrich_book_data(
                book_dict["title"]
            )
            
            # Обновляем метаданные, если они получены
            if cover_url:
                book_dict["cover_url"] = cover_url
            if description:
                book_dict["description"] = description
            if rating:
                book_dict["rating"] = rating
        
        updated_book = Book(**book_dict)
        
        if self.is_db_storage:
            # Для БД обновляем только одну книгу
            self.storage.update_data(book_dict)
        else:
            # Для JSON хранилища обновляем книгу в списке
            data = self.storage.load_data()
            books = data.get("books", [])
            
            for i, book_data in enumerate(books):
                if book_data["id"] == book_id:
                    books[i] = book_dict
                    break
            
            data["books"] = books
            self.storage.save_data(data)
        
        
        return updated_book
    
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
        
        if self.is_db_storage:
            # Для БД удаляем только одну книгу
            self.storage.delete_data(book.model_dump())
        else:
            # Для JSON хранилища удаляем книгу из списка
            data = self.storage.load_data()
            books = data.get("books", [])
            
            data["books"] = [book for book in books if book["id"] != book_id]
            self.storage.save_data(data)
        
        return True
