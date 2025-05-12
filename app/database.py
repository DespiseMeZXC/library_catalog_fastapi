import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from pathlib import Path as FilePath

from app.models.books import Book, Base
from app.utils.logger import setup_logger


# Настраиваем логгер для модуля database
logger = setup_logger("app.database")


class RepositoryInterface(ABC):
    """Абстрактный интерфейс для хранилищ данных."""
    
    @abstractmethod
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из хранилища."""
        pass
    
    @abstractmethod
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в хранилище."""
        pass


class FileRepository(RepositoryInterface):
    """Хранилище данных     а основе JSON-файла."""
    
    def __init__(self):
        self.file_path = FilePath(__file__).parent.parent.parent / "data" / "books.json"
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        logger.debug(f"Инициализировано файловое хранилище: {self.file_path}")
    
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из файла."""
        logger.debug(f"Загрузка данных из файла: {self.file_path}")
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    books_count = len(data.get("books", []))
                    logger.info(f"Загружено {books_count} книг из файла JSON")
                    return data
            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON в файле {self.file_path}")
                return {"books": [], "next_id": 1}
        logger.warning(f"Файл {self.file_path} не существует, возвращаем пустой список книг")
        return {"books": [], "next_id": 1}
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в файл."""
        logger.debug(f"Сохранение данных в файл: {self.file_path}")
        books_count = len(data.get("books", []))
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Сохранено {books_count} книг в файл JSON")
    

class JsonBinRepository(RepositoryInterface):
    """Хранилище данных на основе jsonbin.io."""
    
    def __init__(self):
        self.jsonbin_url = os.getenv("JSONBIN_URL")
        self.jsonbin_master_key = os.getenv("JSONBIN_X_MASTER_KEY")
        self.jsonbin_access_key = os.getenv("JSONBIN_X_ACCESS_KEY")
        self.jsonbin_bin_id = os.getenv("JSONBIN_BIN_ID")
        self.headers = {
            "X-Master-Key": self.jsonbin_master_key,
            "X-Access-Key": self.jsonbin_access_key,
            "Content-Type": "application/json",
            "X-Bin-Id": self.jsonbin_bin_id
        }
        logger.debug(f"Инициализировано хранилище JSONBin с URL: {self.jsonbin_url}")
    
    @property
    def jsonbin_url_api(self) -> str:
        return f"{self.jsonbin_url}/{self.jsonbin_bin_id}"
    
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из jsonbin.io."""
        logger.debug(f"Загрузка данных из JSONBin: {self.jsonbin_url_api}")
        try:
            response = requests.get(self.jsonbin_url_api, headers=self.headers)
            if response.status_code == 200:
                data = response.json()["record"]
                books_count = len(data.get("books", []))
                logger.info(f"Загружено {books_count} книг из JSONBin")
                return data
            logger.error(f"Ошибка при загрузке данных из JSONBin. Код ответа: {response.status_code}")
            return {"books": [], "next_id": 1}
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из JSONBin: {e}")
            return {"books": [], "next_id": 1}
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в jsonbin.io."""
        books_count = len(data.get("books", []))
        logger.debug(f"Сохранение {books_count} книг в JSONBin: {self.jsonbin_url_api}")
        try:
            response = requests.put(self.jsonbin_url_api, json=data, headers=self.headers)
            if response.status_code == 200:
                logger.info(f"Успешно сохранено {books_count} книг в JSONBin")
            else:
                logger.error(f"Ошибка при сохранении данных в JSONBin: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в JSONBin: {e}")


class DbPostgresRepository(RepositoryInterface):
    """Хранилище данных на основе PostgreSQL с использованием SQLAlchemy."""
    def __init__(self):
        self.engine = create_engine(self.get_link_db)
        logger.info(f"Инициализировано хранилище PostgreSQL: {self.get_link_db}")
        
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Структура БД успешно создана/проверена")
        except Exception as e:
            logger.error(f"Ошибка при создании структуры БД: {e}")
        
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        self.books_table = Book
        logger.debug("Сессия SQLAlchemy настроена")
             
    @property
    def get_link_db(self) -> str:
        """Получить URL для подключения к PostgreSQL."""
        host = os.getenv("DB_POSTGRES_HOST", "localhost")
        port = os.getenv("DB_POSTGRES_PORT", "5432")
        user = os.getenv("DB_POSTGRES_USER", "postgres")
        password = os.getenv("DB_POSTGRES_PASSWORD", "postgres")
        db_name = os.getenv("DB_POSTGRES_DB", "library")
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        logger.debug(f"Строка подключения к БД: {conn_str}")
        return conn_str
    
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из PostgreSQL."""
        logger.debug("Загрузка данных из PostgreSQL")
        session = self.Session()
        try:
            books = session.query(self.books_table).all()
            logger.info(f"Загружено {len(books)} книг из PostgreSQL")
            return books
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из PostgreSQL: {e}")
            return []
        finally:
            session.close()
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в PostgreSQL."""
        logger.debug(f"Сохранение книги в PostgreSQL: {data.get('title')}")
        session = self.Session()
        try:
            # Обрабатываем поля HttpUrl, преобразуя их в строки
            cover_url = data.get("cover_url")
            cover_url_str = str(cover_url) if cover_url is not None else None
            
            # Создаем объект SQLAlchemy из словаря
            book = self.books_table(
                id=data["id"],
                title=data["title"],
                author=data["author"],
                publication_year=data["publication_year"],
                genre=data["genre"],
                pages=data["pages"],
                availability=data["availability"],
                cover_url=cover_url_str,
                description=data.get("description"),
                rating=data.get("rating")
            )
            session.add(book)
            session.commit()
            logger.info(f"Книга '{data.get('title')}' успешно сохранена в PostgreSQL")
        except Exception as e:
            logger.error(f"Ошибка при сохранении книги в PostgreSQL: {e}")
            session.rollback()
        finally:
            session.close()
    
    def delete_data(self, data: Dict[str, Any]) -> None:
        """Удалить данные из PostgreSQL."""
        logger.debug(f"Удаление книги из PostgreSQL: ID {data.get('id')}")
        session = self.Session()
        try:
            book = session.query(self.books_table).filter(self.books_table.id == data["id"]).first()
            if book:
                session.delete(book)
                session.commit()
                logger.info(f"Книга с ID {data.get('id')} успешно удалена из PostgreSQL")
            else:
                logger.warning(f"Книга с ID {data.get('id')} не найдена в PostgreSQL для удаления")
        except Exception as e:
            logger.error(f"Ошибка при удалении книги из PostgreSQL: {e}")
            session.rollback()
        finally:
            session.close()
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Обновить данные в PostgreSQL."""
        logger.debug(f"Обновление книги в PostgreSQL: ID {data.get('id')}")
        session = self.Session()
        try:
            book = session.query(self.books_table).filter(self.books_table.id == data["id"]).first()
            if book:
                # Обрабатываем поля HttpUrl, преобразуя их в строки
                cover_url = data.get("cover_url")
                cover_url_str = str(cover_url) if cover_url is not None else None
                
                # Обновляем атрибуты объекта
                book.title = data["title"]
                book.author = data["author"]
                book.publication_year = data["publication_year"]
                book.genre = data["genre"]
                book.pages = data["pages"]
                book.availability = data["availability"]
                book.cover_url = cover_url_str
                book.description = data.get("description")
                book.rating = data.get("rating")
                session.commit()
                logger.info(f"Книга с ID {data.get('id')} успешно обновлена в PostgreSQL")
            else:
                logger.warning(f"Книга с ID {data.get('id')} не найдена в PostgreSQL для обновления")
        except Exception as e:
            logger.error(f"Ошибка при обновлении книги в PostgreSQL: {e}")
            session.rollback()
        finally:
            session.close()
    
    def get_data_by_id(self, id: int) -> Dict[str, Any]:
        """Получить данные по ID."""
        logger.debug(f"Получение книги из PostgreSQL по ID: {id}")
        session = self.Session()
        try:
            book = session.query(self.books_table).filter(self.books_table.id == id).first()
            if book:
                logger.info(f"Книга с ID {id} найдена в PostgreSQL")
            else:
                logger.warning(f"Книга с ID {id} не найдена в PostgreSQL")
            return book
        except Exception as e:
            logger.error(f"Ошибка при получении книги из PostgreSQL: {e}")
            return None
        finally:
            session.close()
            
    def get_next_id(self) -> int:
        """Получить следующий ID."""
        logger.debug("Получение следующего ID из PostgreSQL")
        session = self.Session()
        try:
            # Получаем последнюю книгу с максимальным ID
            last_book = session.query(self.books_table).order_by(self.books_table.id.desc()).first()
            if last_book:
                next_id = last_book.id + 1
                logger.info(f"Следующий ID из PostgreSQL: {next_id}")
                return next_id
            logger.info("Таблица пуста, начинаем с ID 1")
            return 1  # Если таблица пуста, начинаем с 1
        except Exception as e:
            logger.error(f"Ошибка при получении следующего ID из PostgreSQL: {e}")
            return 1
        finally:
            session.close()
