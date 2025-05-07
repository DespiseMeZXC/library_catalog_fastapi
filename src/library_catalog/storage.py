import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


Base = declarative_base()

# Определение таблицы книг
class BookTable(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    publication_year = Column(Integer, nullable=False)
    genre = Column(String(100), nullable=False)
    pages = Column(Integer, nullable=False)
    availability = Column(String(50), nullable=False)
    cover_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)

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
    """Хранилище данных на основе JSON-файла."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из файла."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"books": [], "next_id": 1}
        return {"books": [], "next_id": 1}
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в файл."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    

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
    @property
    def jsonbin_url_api(self) -> str:
        return f"{self.jsonbin_url}/{self.jsonbin_bin_id}"
    
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из jsonbin.io."""
        try:
            response = requests.get(self.jsonbin_url_api, headers=self.headers)
            if response.status_code == 200:
                return response.json()["record"]
            return {"books": [], "next_id": 1}
        except Exception as e:
            print(f"Ошибка при загрузке данных из jsonbin: {e}")
            return {"books": [], "next_id": 1}
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в jsonbin.io."""
        try:
            response = requests.put(self.jsonbin_url_api, json=data, headers=self.headers)
            if response.status_code != 200:
                print(f"Ошибка при сохранении данных в jsonbin: {response.text}")
        except Exception as e:
            print(f"Ошибка при сохранении данных в jsonbin: {e}")


class DbPostgresRepository(RepositoryInterface):
    """Хранилище данных на основе PostgreSQL с использованием SQLAlchemy."""
    def __init__(self):
        self.engine = create_engine(self.get_link_db)
        
        Base.metadata.create_all(self.engine)
        
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        self.books_table = BookTable
             
    @property
    def get_link_db(self) -> str:
        """Получить URL для подключения к PostgreSQL."""
        host = os.getenv("DB_POSTGRES_HOST", "localhost")
        port = os.getenv("DB_POSTGRES_PORT", "5432")
        user = os.getenv("DB_POSTGRES_USER", "postgres")
        password = os.getenv("DB_POSTGRES_PASSWORD", "postgres")
        db_name = os.getenv("DB_POSTGRES_DB", "library")
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из PostgreSQL."""
        session = self.Session()
        try:
            return session.query(self.books_table).all()
        finally:
            session.close()
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в PostgreSQL."""
        session = self.Session()
        try:
            # Создаем объект SQLAlchemy из словаря
            book = self.books_table(
                id=data["id"],
                title=data["title"],
                author=data["author"],
                publication_year=data["publication_year"],
                genre=data["genre"],
                pages=data["pages"],
                availability=data["availability"],
                cover_url=data.get("cover_url"),
                description=data.get("description"),
                rating=data.get("rating")
            )
            session.add(book)
            session.commit()
        finally:
            session.close()
    
    def delete_data(self, data: Dict[str, Any]) -> None:
        """Удалить данные из PostgreSQL."""
        session = self.Session()
        try:
            book = session.query(self.books_table).filter(self.books_table.id == data["id"]).first()
            if book:
                session.delete(book)
                session.commit()
        finally:
            session.close()
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Обновить данные в PostgreSQL."""
        session = self.Session()
        try:
            book = session.query(self.books_table).filter(self.books_table.id == data["id"]).first()
            if book:
                # Обновляем атрибуты объекта
                book.title = data["title"]
                book.author = data["author"]
                book.publication_year = data["publication_year"]
                book.genre = data["genre"]
                book.pages = data["pages"]
                book.availability = data["availability"]
                book.cover_url = data.get("cover_url")
                book.description = data.get("description")
                book.rating = data.get("rating")
                session.commit()
        finally:
            session.close()
    
    def get_data_by_id(self, id: int) -> Dict[str, Any]:
        """Получить данные по ID."""
        session = self.Session()
        try:
            return session.query(self.books_table).filter(self.books_table.id == id).first()
        finally:
            session.close()
            
    def get_next_id(self) -> int:
        """Получить следующий ID."""
        session = self.Session()
        try:
            # Получаем последнюю книгу с максимальным ID
            last_book = session.query(self.books_table).order_by(self.books_table.id.desc()).first()
            if last_book:
                return last_book.id + 1
            return 1  # Если таблица пуста, начинаем с 1
        finally:
            session.close()
