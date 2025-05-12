import logging
import os
from pathlib import Path
from datetime import datetime

# Настройка форматирования логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

# Директория для сохранения логов
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Имя файла логов с текущей датой
LOG_FILE = LOG_DIR / f"library_catalog_{datetime.now().strftime('%Y-%m-%d')}.log"

# Настройка корневого логгера
def setup_logger(name=None):
    """
    Настраивает и возвращает логгер с заданным именем.
    
    Args:
        name: Имя логгера (если None, возвращается корневой логгер)
        
    Returns:
        Настроенный объект логгера
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Обработчик для вывода в файл
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Добавляем обработчики к логгеру, если их еще нет
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    # Отключаем распространение логов, чтобы избежать дублирования
    logger.propagate = False
    
    return logger 
