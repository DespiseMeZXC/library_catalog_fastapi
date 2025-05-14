from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Type
from pydantic import BaseModel, HttpUrl

from app.schemas.books import EnrichBookData, StorageType, BookFilter


class RepositoryInterface(ABC):
    """Абстрактный интерфейс для хранилищ данных."""
    storage_type: StorageType = StorageType.FILE
    
    @abstractmethod
    def load_data(self, offset: int = 0, limit: int = 100, **filters: BookFilter) -> Dict[str, Any]:
        """Загрузить данные из хранилища."""
        pass
    
    @abstractmethod
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в хранилище."""
        pass
    
    @abstractmethod
    def _update_next_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление счетчика ID в хранилище."""
        pass
    
    @abstractmethod
    def _get_next_id(self) -> int:
        """Получить следующий ID."""
        pass
    
    @abstractmethod
    def storage_type(self) -> str:
        """Получить тип хранилища."""
        pass


class DbRepositoryInterface(RepositoryInterface):
    """Абстрактный интерфейс для хранилищ данных на основе PostgreSQL."""
    storage_type: StorageType = StorageType.DB
    
    @abstractmethod
    def get_link_db(self) -> str:
        """Получить ссылку на базу данных."""
        pass
    
    @abstractmethod
    def get_data_by_id(self, id: int) -> Dict[str, Any]:
        """Получить данные по ID."""
        pass
    
    @abstractmethod
    def delete_data(self, data: Dict[str, Any]) -> None:
        """Удалить данные по ID."""
        pass
    
    @abstractmethod
    def update_data(self, data: Dict[str, Any]) -> None:
        """Обновить данные по ID."""
        pass
    
T = TypeVar('T', bound=BaseModel)  # Тип модели
C = TypeVar('C', bound=BaseModel)  # Тип для создания
U = TypeVar('U', bound=BaseModel)  # Тип для обновления

class CRUDServiceInterface(Generic[T, C, U], ABC):
    """
    Абстрактный интерфейс репозитория для работы с моделями данных.
    Определяет основные операции CRUD.
    """
    
    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 100, **filters) -> List[T]:
        """Получение списка всех элементов с возможностью фильтрации."""
        pass
    
    @staticmethod
    def _convert_model_to_schema(data: Dict[str, Any], model: Type[BaseModel]) -> T:
        """Конвертация данных в модель."""
        pass
    
    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[T]:
        """Получение элемента по ID."""
        pass
    
    @abstractmethod
    async def create(self, item: C) -> T:
        """Создание нового элемента."""
        pass
    
    @abstractmethod
    async def update(self, item_id: int, item_update: U) -> Optional[T]:
        """Обновление данных элемента."""
        pass
    
    @abstractmethod
    def delete(self, item_id: int) -> bool:
        """Удаление элемента по ID."""
        pass
    

T = TypeVar('T')  # Тип результата поиска
D = TypeVar('D')  # Тип детальной информации


class ExternalApiProvider(Generic[T, D], ABC):
    """
    Абстрактный класс для работы с внешними API.
    Определяет общий интерфейс для взаимодействия с любыми внешними API.
    """
    
    @abstractmethod
    async def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполнение HTTP-запроса к API.
        
        :param endpoint: Конечная точка API
        :param params: Параметры запроса
        :return: Результат запроса или None при ошибке
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> Optional[T]:
        """
        Поиск данных в API.
        
        :param query: Поисковый запрос
        :param kwargs: Дополнительные параметры поиска
        :return: Результат поиска или None, если ничего не найдено
        """
        pass
    
    @abstractmethod
    async def get_details(self, item_id: str) -> Optional[D]:
        """
        Получение детальной информации по идентификатору.
        
        :param item_id: Идентификатор элемента
        :return: Детальная информация или None при ошибке
        """
        pass


class BookInfoProvider(ExternalApiProvider[Dict[str, Any], Dict[str, Any]], ABC):
    """
    Абстрактный класс для провайдеров информации о книгах.
    Расширяет базовый класс ExternalApiProvider для работы с книжными API.
    """
    
    @abstractmethod
    async def search_book(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Поиск книги по названию.
        
        :param title: Название книги
        :return: Информация о найденной книге или None, если книга не найдена
        """
        pass
    
    @abstractmethod
    async def get_book_rating(self, key: str) -> Optional[float]:
        """
        Получение рейтинга книги.
        
        :param key: Ключ книги
        :return: Рейтинг книги или None, если рейтинг не найден
        """
        pass
    
    @abstractmethod
    async def get_cover_url(self, book_id: str, size: str = "M") -> Optional[HttpUrl]:
        """
        Получение URL обложки книги.
        
        :param book_id: ID книги
        :param size: Размер обложки
        :return: URL обложки или None, если обложка не найдена
        """
        pass
    
    @abstractmethod
    async def get_book_description(self, book_data: Dict[str, Any]) -> Optional[str]:
        """
        Извлечение описания книги из данных.
        
        :param book_data: Данные о книге
        :return: Описание книги или None, если описание не найдено
        """
        pass
    
    @abstractmethod
    async def enrich_book_data(self, title: str) -> Optional[EnrichBookData]:
        """
        Получение дополнительной информации о книге.
        
        :param title: Название книги
        :return: Обогащенные данные для книги
        """
        pass
