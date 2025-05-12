from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"


class BookBase(BaseModel):
    title: str
    author: str
    publication_year: int
    genre: str
    pages: int
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class BookCreate(BookBase):
    pass


class Book(BookBase):
    id: int
    # Дополнительные поля с информацией из Open Library API
    cover_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    pages: Optional[int] = None
    availability: Optional[AvailabilityStatus] = None


class BookQueryParams(BaseModel):
    offset: int = 0
    limit: int = 10
    author: Optional[str] = None
    genre: Optional[str] = None
    availability: Optional[AvailabilityStatus] = None

