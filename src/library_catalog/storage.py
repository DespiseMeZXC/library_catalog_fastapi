from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
import os
import requests


class Storage(ABC):
    """Абстрактный интерфейс для хранилищ данных."""
    
    @abstractmethod
    def load_data(self) -> Dict[str, Any]:
        """Загрузить данные из хранилища."""
        pass
    
    @abstractmethod
    def save_data(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в хранилище."""
        pass


class FileStorage(Storage):
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


class JsonBinStorage(Storage):
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
