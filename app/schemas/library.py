from pydantic import BaseModel
from typing import Optional


class BookBase(BaseModel):
    title: str
    author: str
    category: str
    total_count: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    total_count: Optional[int] = None


class BookResponse(BookBase):
    id: int
    available_count: int

    class Config:
        from_attributes = True


class LoanResponse(BaseModel):
    id: int
    username: str
    book_title: str
    date: str
    status: str

    class Config:
        from_attributes = True
