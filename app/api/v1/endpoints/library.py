from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.library import BookResponse, BookCreate, BookUpdate, LoanResponse
from app.crud import crud_library

router = APIRouter()


@router.get("/books", response_model=List[BookResponse])
def search_books(search: str = None, db: Session = Depends(get_db)):
    return crud_library.get_books(db, search)


@router.post("/books", response_model=BookResponse)
def add_book(
    book_in: BookCreate, role: str = Cookie(None), db: Session = Depends(get_db)
):
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return crud_library.create_book(db, book_in)


@router.put("/books/{book_id}", response_model=BookResponse)
def edit_book(
    book_id: int,
    book_update: BookUpdate,
    role: str = Cookie(None),
    db: Session = Depends(get_db),
):
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    book = crud_library.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book_update.title:
        book.title = book_update.title
    if book_update.author:
        book.author = book_update.author
    if book_update.category:
        book.category = book_update.category
    if book_update.total_count is not None:
        diff = book_update.total_count - book.total_count
        book.total_count = book_update.total_count
        book.available_count += diff
        if book.available_count < 0:
            raise HTTPException(
                status_code=400, detail="Available count cannot be negative"
            )
    db.commit()
    db.refresh(book)
    return book


@router.delete("/books/{book_id}")
def remove_book(book_id: int, role: str = Cookie(None), db: Session = Depends(get_db)):
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    book = crud_library.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    crud_library.delete_book(db, book)
    return {"detail": "Book deleted"}


@router.post("/loans/request")
def loan_request(
    book_title: str, username: str = Cookie(None), db: Session = Depends(get_db)
):
    book = crud_library.get_book_by_title(db, book_title)
    if not book or book.available_count <= 0:
        raise HTTPException(status_code=400, detail="Book not available!")
    crud_library.create_loan_request(db, username, book.title)
    return {"detail": "Request sent for approval."}


@router.get("/loans/my", response_model=List[LoanResponse])
def my_books(username: str = Cookie(None), db: Session = Depends(get_db)):
    return crud_library.get_user_loans(db, username)


@router.post("/loans/{loan_id}/action")
def loan_action(
    loan_id: int,
    action: str,
    username: str = Cookie(None),
    db: Session = Depends(get_db),
):
    loan = crud_library.get_loan_by_id(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if action in ["extension", "return"]:
        if loan.username != username or loan.status != "approved":
            raise HTTPException(
                status_code=400, detail="Invalid action for this loan status"
            )
        loan.status = "renew_pending" if action == "extension" else "return_pending"
    db.commit()
    return {"detail": f"{action} request sent."}


@router.get("/loans/all", response_model=List[LoanResponse])
def all_loans(role: str = Cookie(None), db: Session = Depends(get_db)):
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Denied")
    return crud_library.get_all_loans(db)


@router.post("/loans/{loan_id}/manage")
def manage_loan(
    loan_id: int, decision: str, role: str = Cookie(None), db: Session = Depends(get_db)
):
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Denied")
    loan = crud_library.get_loan_by_id(db, loan_id)
    book = crud_library.get_book_by_title(db, loan.book_title)

    if decision == "approve":
        if loan.status == "pending" and book:
            book.available_count -= 1
            loan.status = "approved"
        elif loan.status == "return_pending" and book:
            book.available_count += 1
            loan.status = "returned"
        elif loan.status == "renew_pending":
            loan.status = "approved"
    elif decision == "reject":
        loan.status = "rejected"
    db.commit()
    return {"detail": "Decision applied successfully"}
