import requests
from typing import Dict, Any, Optional, List, Tuple
from pydantic import HttpUrl


class OpenLibraryApi:
    """
    Класс для взаимодействия с Open Library API.
    Позволяет получать дополнительную информацию о книгах.
    """
    
    BASE_URL = "https://openlibrary.org"
    COVERS_URL = "https://covers.openlibrary.org/b"

    
    def __init__(self):
        self.session = requests.Session()
    
    def search_book(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Поиск книги в Open Library по названию и автору.
        
        :param title: Название книги
        :return: Информация о найденной книге или None, если книга не найдена
        """
        query = f"title:{title}"
        
        params = {
            "q": query,
            "limit": 1
        }
        
        try:
            response = self.session.get(f"{self.BASE_URL}/search.json", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("numFound", 0) > 0 and len(data.get("docs", [])) > 0:
                return data["docs"][0]
            
            return None
        
        except requests.RequestException as e:
            return None
    
    def get_book_details(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации о книге по её ключу.
        
        :param key: Ключ книги в Open Library (например, /works/OL1234W)
        :return: Детальная информация о книге или None при ошибке
        """
        try:
            response = self.session.get(f"{self.BASE_URL}{key}.json")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            return None
    
    def get_book_rating(self, key: str) -> Optional[float]:
        """
        Получение рейтинга книги.
        
        :param key: Ключ книги в Open Library
        :return: Рейтинг книги или None, если рейтинг не найден
        """
        # Удаляем префикс '/works/' из ключа, если он есть
        work_id = key.split('/')[-1] if '/' in key else key
        
        try:
            # Используем Books API для получения информации о книге
            response = self.session.get(f"{self.BASE_URL}/works/{work_id}/ratings.json")
            response.raise_for_status()
            data = response.json()
            if "summary" in data and "average" in data["summary"]:
                return data["summary"]["average"]
            return None
        
        except requests.RequestException as e:
            return None
    
    def get_cover_url(self, olid: str, size: str = "M") -> Optional[HttpUrl]:
        """
        Получение URL обложки книги.
        
        :param olid: ID книги в Open Library 
        :param size: Размер обложки (S, M, L)
        :return: URL обложки или None, если обложка не найдена
        """
        # Удаляем префикс и берем только идентификатор
        book_id = olid.split('/')[-1] if '/' in olid else olid
        
        if not book_id:
            return None
        
        # Учитываем, что идентификатор может быть для работы (OL...W) или издания (OL...M)
        id_type = "OLID"
        cover_url = f"{self.COVERS_URL}/{id_type}/{book_id}-{size}.jpg"
        
        return cover_url
    
    def get_book_description(self, book_data: Dict[str, Any]) -> Optional[str]:
        """
        Извлечение описания книги из данных Open Library.
        
        :param book_data: Данные о книге из Open Library
        :return: Описание книги или None, если описание не найдено
        """
        description = None
        try:
            response = self.session.get(f"{self.BASE_URL}/{book_data['key']}/editions.json")
            response.raise_for_status()
           
            for i in response.json()["entries"]:
                if "description" in i and i["description"]["type"] == "/type/text":
                    description = i["description"]["value"]
                    break
        except requests.RequestException as e:
            return None
        
        return description
    
    def enrich_book_data(self, title: str) -> Tuple[Optional[HttpUrl], Optional[str], Optional[float]]:
        """
        Получение дополнительной информации о книге из Open Library.
        
        :param title: Название книги
        :return: Кортеж (URL обложки, описание, рейтинг, ключ Open Library)
        """
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
