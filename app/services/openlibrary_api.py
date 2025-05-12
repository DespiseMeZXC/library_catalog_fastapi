import requests
from typing import Dict, Any, Optional, Tuple
from pydantic import HttpUrl

from app.interfaces.books import BookInfoProvider
from app.utils.logger import setup_logger


# Настраиваем логгер для модуля openlibrary_api
logger = setup_logger("app.services.openlibrary_api")


class OpenLibraryApi(BookInfoProvider):
    """
    Класс для взаимодействия с Open Library API.
    Реализует интерфейс BookInfoProvider для получения дополнительной информации о книгах.
    """
    
    BASE_URL = "https://openlibrary.org"
    COVERS_URL = "https://covers.openlibrary.org/b"

    
    def __init__(self):
        self.session = requests.Session()
    
    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполнение HTTP-запроса к API Open Library.
        
        :param endpoint: Конечная точка API
        :param params: Параметры запроса
        :return: Результат запроса или None при ошибке
        """
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к API: {e}")
            return None
        except ValueError as e:
            logger.error(f"Ошибка при разборе JSON: {e}")
            return None
    
    def search(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Поиск данных в API Open Library.
        
        :param query: Поисковый запрос
        :param kwargs: Дополнительные параметры поиска
        :return: Результат поиска или None, если ничего не найдено
        """
        try:
            params = {"q": query, **kwargs}
            result = self.make_request("/search.json", params)
            
            if result and result.get("numFound", 0) > 0 and len(result.get("docs", [])) > 0:
                return result["docs"][0]
            return None
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return None
    
    def get_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации по идентификатору.
        
        :param item_id: Идентификатор элемента
        :return: Детальная информация или None при ошибке
        """
        try:
            return self.make_request(f"{item_id}.json")
        except Exception as e:
            logger.error(f"Ошибка при получении деталей: {e}")
            return None
    
    def search_book(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Поиск книги в Open Library по названию.
        
        :param title: Название книги
        :return: Информация о найденной книге или None, если книга не найдена
        """
        try:
            query = f"title:{title}"
            return self.search(query, limit=1)
        except Exception as e:
            logger.error(f"Ошибка при поиске книги: {e}")
            return None
    
    def get_book_details(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации о книге по её ключу.
        
        :param key: Ключ книги в Open Library (например, /works/OL1234W)
        :return: Детальная информация о книге или None при ошибке
        """
        try:
            return self.get_details(key)
        except Exception as e:
            logger.error(f"Ошибка при получении деталей книги: {e}")
            return None
    
    def get_book_rating(self, key: str) -> Optional[float]:
        """
        Получение рейтинга книги.
        
        :param key: Ключ книги в Open Library
        :return: Рейтинг книги или None, если рейтинг не найден
        """
        try:
            # Удаляем префикс '/works/' из ключа, если он есть
            work_id = key.split('/')[-1] if '/' in key else key
            
            result = self.make_request(f"/works/{work_id}/ratings.json")
            if result and "summary" in result and "average" in result["summary"]:
                return result["summary"]["average"]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении рейтинга книги: {e}")
            return None
    
    def get_cover_url(self, book_id: str, size: str = "M") -> Optional[HttpUrl]:
        """
        Получение URL обложки книги.
        
        :param book_id: ID книги в Open Library 
        :param size: Размер обложки (S, M, L)
        :return: URL обложки или None, если обложка не найдена
        """
        try:
            # Удаляем префикс и берем только идентификатор
            olid = book_id.split('/')[-1] if '/' in book_id else book_id
            
            if not olid:
                return None
            
            # Учитываем, что идентификатор может быть для работы (OL...W) или издания (OL...M)
            id_type = "OLID"
            cover_url = f"{self.COVERS_URL}/{id_type}/{olid}-{size}.jpg"
            
            return cover_url
        except Exception as e:
            logger.error(f"Ошибка при получении URL обложки: {e}")
            return None
    
    def get_book_description(self, book_data: Dict[str, Any]) -> Optional[str]:
        """
        Извлечение описания книги из данных Open Library.
        
        :param book_data: Данные о книге из Open Library
        :return: Описание книги или None, если описание не найдено
        """
        try:
            description = None
            result = self.make_request(f"{book_data['key']}/editions.json")
            
            if result and "entries" in result:
                for entry in result["entries"]:
                    if "description" in entry and entry["description"]["type"] == "/type/text":
                        description = entry["description"]["value"]
                        break
            
            return description
        except Exception as e:
            logger.error(f"Ошибка при получении описания книги: {e}")
            return None
    
    def enrich_book_data(self, title: str) -> Tuple[Optional[HttpUrl], Optional[str], Optional[float]]:
        """
        Получение дополнительной информации о книге из Open Library.
        
        :param title: Название книги
        :return: Кортеж (URL обложки, описание, рейтинг)
        """
        try:
            book_search_result = self.search_book(title)
            
            if not book_search_result:
                return None, None, None
            
            cover_url = None
            description = None
            rating = None
            
            # Получаем ключ книги (работы)
            work_key = book_search_result.get("key") or book_search_result.get("work_key")
            if work_key:
                book_details = self.get_book_details(work_key)
                if book_details:
                    description = self.get_book_description(book_details)
                    rating = self.get_book_rating(work_key)
            
            # Получаем ID книги для обложки
            cover_id = book_search_result.get("cover_i") or book_search_result.get("cover_id")
            if cover_id:
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            elif "edition_key" in book_search_result and book_search_result["edition_key"]:
                # Используем ID первого издания, если доступно
                edition_id = book_search_result["edition_key"][0]
                cover_url = self.get_cover_url(edition_id)
            
            return cover_url, description, rating
        except Exception as e:
            logger.error(f"Ошибка при обогащении данных книги: {e}")
            return None, None, None
