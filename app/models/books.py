from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

# Определение таблицы книг
class Book(Base):
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
