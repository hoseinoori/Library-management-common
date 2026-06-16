from sqlalchemy.orm import Session
from app.models.library import Book, Loan
from app.schemas.library import BookCreate, BookUpdate
from datetime import datetime


def get_books(db: Session, search: str = None):
    query = db.query(Book)
    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%") | Book.author.ilike(f"%{search}%")
        )
    return query.all()


def get_book_by_id(db: Session, book_id: int):
    return db.query(Book).filter(Book.id == book_id).first()


def get_book_by_title(db: Session, title: str):
    return db.query(Book).filter(Book.title.ilike(title)).first()


def create_book(db: Session, book_in: BookCreate):
    db_book = Book(**book_in.model_dump(), available_count=book_in.total_count)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, db_book: Book):
    db.delete(db_book)
    db.commit()


def create_loan_request(db: Session, username: str, book_title: str):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    db_loan = Loan(
        username=username, book_title=book_title, date=date_str, status="pending"
    )
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


def get_user_loans(db: Session, username: str):
    return db.query(Loan).filter(Loan.username == username).all()


def get_all_loans(db: Session):
    return db.query(Loan).all()


def get_loan_by_id(db: Session, loan_id: int):
    return db.query(Loan).filter(Loan.id == loan_id).first()
