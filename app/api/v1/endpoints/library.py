from fastapi import APIRouter, Depends, HTTPException, Cookie, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.library import BookResponse, BookCreate, BookUpdate, LoanResponse
from app.crud import crud_library, crud_user
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/books", response_model=List[BookResponse])
def search_books(search: str = None, db: Session = Depends(get_db)):
    """دقیقاً منطق book_search کد شما با قابلیت سرور ساید"""
    return crud_library.get_books(db, search)


@router.post("/books", response_model=BookResponse)
def add_book(
    book_in: BookCreate, role: str = Cookie(None), db: Session = Depends(get_db)
):
    """منطق add_book کد شما"""
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="فقط ادمین و کتابدار مجاز هستند!")
    return crud_library.create_book(db, book_in)


@router.put("/books/{book_id}", response_model=BookResponse)
def edit_book(
    book_id: int,
    book_update: BookUpdate,
    role: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """منطق دقیق edit_book شما (محاسبه تفاوت تعداد کل و موجودی دسترس)"""
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز!")

    book = crud_library.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="کتاب یافت نشد!")

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
                status_code=400, detail="خطا: تعداد کتاب‌های در دسترس کافی نیست!"
            )

    db.commit()
    db.refresh(book)
    return book


@router.delete("/books/{book_id}")
def remove_book(book_id: int, role: str = Cookie(None), db: Session = Depends(get_db)):
    """منطق remove_book شما"""
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز!")
    book = crud_library.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="کتاب یافت نشد!")
    crud_library.delete_book(db, book)
    return {"detail": "کتاب با موفقیت حذف شد."}


@router.post("/loans/request")
def loan_request(
    book_title: str, username: str = Cookie(None), db: Session = Depends(get_db)
):
    """منطق دقیق loan_request"""
    book = crud_library.get_book_by_title(db, book_title)
    if not book or book.available_count <= 0:
        raise HTTPException(
            status_code=400, detail="کتاب موجود نیست یا تعداد دسترس صفر است!"
        )

    crud_library.create_loan_request(db, username, book.title)
    return {"detail": "درخواست امانت با موفقیت ثبت و ارسال شد."}


@router.get("/loans/my", response_model=List[LoanResponse])
def show_my_books(username: str = Cookie(None), db: Session = Depends(get_db)):
    """منطق show_my_books شما"""
    return crud_library.get_user_loans(db, username)


@router.post("/loans/{loan_id}/action")
def loan_action(
    loan_id: int,
    action: str,
    username: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """منطق درخواست‌های تمدید (extension_request) و بازگشت (return_request)"""
    loan = crud_library.get_loan_by_id(db, loan_id)
    if not loan or loan.username != username:
        raise HTTPException(status_code=404, detail="امانتی یافت نشد!")

    if action == "extension":
        if loan.status != "approved":
            raise HTTPException(
                status_code=400, detail="فقط کتاب‌های تایید شده قابل تمدید هستند!"
            )
        loan.status = "renew_pending"
    elif action == "return":
        if loan.status != "approved":
            raise HTTPException(
                status_code=400, detail="کتاب در وضعیت امانت فعال نیست!"
            )
        loan.status = "return_pending"

    db.commit()
    return {"detail": "درخواست شما برای بررسی به مدیریت ارسال شد."}


@router.get("/loans/all", response_model=List[LoanResponse])
def manage_requests(role: str = Cookie(None), db: Session = Depends(get_db)):
    """لیست کردن تمام درخواست‌ها جهت بررسی در پنل ادمین/کتابدار"""
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="عدم دسترسی!")
    return crud_library.get_all_loans(db)


@router.post("/loans/{loan_id}/manage")
def approve_reject_request(
    loan_id: int, decision: str, role: str = Cookie(None), db: Session = Depends(get_db)
):
    """منطق عددی و محاسباتی کامل مدیریت درخواست‌ها (manage_requests)"""
    if role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="عدم دسترسی!")

    loan = crud_library.get_loan_by_id(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="درخواست پیدا نشد!")

    book = crud_library.get_book_by_title(db, loan.book_title)

    if decision == "approve":
        if loan.status == "pending":
            if book and book.available_count > 0:
                book.available_count -= 1
                loan.status = "approved"
            else:
                raise HTTPException(
                    status_code=400, detail="موجودی کتاب برای تایید کافی نیست!"
                )
        elif loan.status == "return_pending":
            if book:
                book.available_count += 1
                loan.status = "returned"
        elif loan.status == "renew_pending":
            loan.status = "approved"

    elif decision == "reject":
        loan.status = "rejected"

    db.commit()
    return {"detail": "تغییرات با موفقیت در سیستم اعمال شد."}
