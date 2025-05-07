from pydantic import BaseModel, Field
from typing import List, Optional
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
    

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    pages: Optional[int] = None
    availability: Optional[AvailabilityStatus] = None

