from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import UserCreate, LoginSchema, UserResponse
from app.crud import crud_user
from app.core.security import verify_password

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud_user.create_user(db=db, user_in=user_in)


@router.post("/login")
def login(login_data: LoginSchema, response: Response, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username=login_data.username)
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    response.set_cookie(key="username", value=user.username)
    response.set_cookie(key="role", value=user.role)
    return {"status": "success", "username": user.username, "role": user.role}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("username")
    response.delete_cookie("role")
    return {"status": "success"}
