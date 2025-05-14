from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()

# Определение таблицы книг
class Book(Base):
    """Модель данных для книг в библиотеке."""
    __tablename__ = 'books'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="Название книги")
    author: Mapped[str] = mapped_column(String(255), nullable=False, comment="Автор книги")
    publication_year: Mapped[int] = mapped_column(Integer, nullable=False, comment="Год публикации")
    genre: Mapped[str] = mapped_column(String(100), nullable=False, comment="Жанр книги")
    pages: Mapped[int] = mapped_column(Integer, nullable=False, comment="Количество страниц")
    availability: Mapped[str] = mapped_column(String(50), nullable=False, comment="Статус доступности")
    cover_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="URL обложки книги")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Описание книги")
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="Рейтинг книги")  
