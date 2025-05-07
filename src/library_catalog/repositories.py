import json
import os
import hashlib
from typing import List, Optional, Dict, Any
import requests
from .models import Book, BookCreate, BookUpdate, AvailabilityStatus
from .storage import Storage
from .openlibrary_api import OpenLibraryApi


class BookRepository:
    """
    Репозиторий для работы с книгами. Обеспечивает операции CRUD для книг.
    """
    def __init__(self, storage: Storage):
        """
        Инициализация репозитория.
        
        :param storage: Хранилище данных
        """
        self.storage = storage
        self.openlibrary_api = OpenLibraryApi()  # Инициализация объекта OpenLibraryApi
        
        # Загружаем данные из хранилища
        data = self.storage.load_data()
        self.books_dict = {book["id"]: book for book in data.get("books", [])}
        self.next_id = data.get("next_id", 1)
    
    def _save(self) -> None:
        """Сохранение данных в хранилище."""
        books_list = list(self.books_dict.values())
        data = {"books": books_list, "next_id": self.next_id}
        self.storage.save_data(data)
    
    def get_all(self, offset: int = 0, limit: int = 100, 
                author: Optional[str] = None, 
                genre: Optional[str] = None, 
                availability: Optional[AvailabilityStatus] = None) -> List[Book]:
        """
        Получение списка всех книг с возможностью фильтрации.
        
        :param offset: Сколько книг пропустить (для пагинации)
        :param limit: Максимальное количество книг для возврата
        :param author: Фильтр по автору
        :param genre: Фильтр по жанру
        :param availability: Фильтр по доступности
        :return: Список книг
        """
        filtered_books = []
        
        for book_data in self.books_dict.values():
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
        book_data = self.books_dict.get(book_id)
        
        if book_data:
            return Book(**book_data)
        
        return None
    
    def create(self, book: BookCreate) -> Book:
        """
        Создание новой книги.
        
        :param book: Данные книги
        :return: Созданная книга с ID
        """
        book_id = self.next_id
        self.next_id += 1
        
        book_dict = book.model_dump()
        book_dict["id"] = book_id
        
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
        
        self.books_dict[book_id] = book_dict
        
        self._save()
        
        return Book(**book_dict)
    
    def update(self, book_id: int, book_update: BookUpdate) -> Optional[Book]:
        """
        Обновление данных книги.
        
        :param book_id: ID книги
        :param book_update: Данные для обновления (только непустые поля будут обновлены)
        :return: Обновленная книга или None, если книга не найдена
        """
        book_data = self.books_dict.get(book_id)
                    
        if not book_data:
            return None
        
        update_data = book_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                book_data[field] = value
        
        # Если изменился автор или название, обновляем метаданные из Open Library
        if "title" in update_data:
            cover_url, description, rating = self.openlibrary_api.enrich_book_data(
                book_data["title"]
            )
            
            # Обновляем метаданные, если они получены
            if cover_url:
                book_data["cover_url"] = cover_url
            if description:
                book_data["description"] = description
            if rating:
                book_data["rating"] = rating
                
        self.books_dict[book_id] = book_data
        
        self._save()
        
        return Book(**book_data)
    
    def delete(self, book_id: int) -> bool:
        """
        Удаление книги по ID.
        
        :param book_id: ID книги
        :return: True, если книга успешно удалена, иначе False
        """
        # Проверяем наличие книги по ID
        if book_id in self.books_dict:
            del self.books_dict[book_id]
            self._save()
            return True
        return False
