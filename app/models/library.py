from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.session import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    category = Column(String, nullable=False)
    total_count = Column(Integer, default=1)
    available_count = Column(Integer, default=1)


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    book_title = Column(String, nullable=False)
    date = Column(String, nullable=False)
    status = Column(String, default="pending")
