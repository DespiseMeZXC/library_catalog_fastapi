from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"


class StorageType(str, Enum):
    FILE = "file"
    JSONBIN = "jsonbin"
    DB = "db"


class BookFilter(BaseModel):
    author: Optional[str] = None
    genre: Optional[str] = None
    availability: Optional[AvailabilityStatus] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

    class Config:
        extra = "forbid"  


class BookBase(BaseModel):
    title: str
    author: str
    publication_year: int
    genre: str
    pages: int
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class BookCreate(BookBase):
    class Config:
        extra = "forbid"  


class Book(BookBase):
    id: int
    # Дополнительные поля с информацией из Open Library API
    cover_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    
    class Config:
        extra = "forbid"  

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    pages: Optional[int] = None
    availability: Optional[AvailabilityStatus] = None
    
    class Config:
        extra = "forbid"  


class BookQueryParams(BaseModel):
    offset: int = 0
    limit: int = 10
    author: Optional[str] = None
    genre: Optional[str] = None
    availability: Optional[AvailabilityStatus] = None

    class Config:
        extra = "forbid"  

class EnrichBookData(BaseModel):
    cover_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    rating: Optional[float] = None

    class Config:
        extra = "forbid"  

class FullBookData(BaseModel):
    id: int
    title: str
    author: str
    publication_year: int
    genre: str
    pages: int
    availability: AvailabilityStatus
    cover_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    
    class Config:
        extra = "forbid" 
        
