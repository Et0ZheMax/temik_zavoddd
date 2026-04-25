from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.auth.security import hash_password
from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import APIMessage, UserCreate, UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return db.query(User).all()


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists:
        raise HTTPException(400, "username уже используется")
    user = User(**payload.model_dump(exclude={"password"}), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def patch_user(user_id: int, payload: UserCreate, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    for k, v in payload.model_dump(exclude={"password"}).items():
        setattr(user, k, v)
    user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/deactivate", response_model=APIMessage)
def deactivate_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    user.is_active = False
    db.commit()
    return APIMessage(message="Пользователь деактивирован")
