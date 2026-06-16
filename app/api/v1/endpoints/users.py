from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.crud import crud_user

router = APIRouter()


def check_admin(role: str = Cookie(None)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized! Admin only.")


@router.get("/", response_model=List[UserResponse], dependencies=[Depends(check_admin)])
def list_users(db: Session = Depends(get_db)):
    return crud_user.get_all_users(db)


@router.put(
    "/{username}", response_model=UserResponse, dependencies=[Depends(check_admin)]
)
def edit_user(username: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud_user.update_user(db, user, user_update)


@router.delete("/{username}", dependencies=[Depends(check_admin)])
def remove_user(
    username: str, current_user: str = Cookie(None), db: Session = Depends(get_db)
):
    if username == current_user:
        raise HTTPException(
            status_code=400, detail="You cannot delete your own account!"
        )
    user = crud_user.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud_user.delete_user(db, user)
    return {"detail": "User deleted successfully"}
