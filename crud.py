from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

import models
import schemas


def get_users(db: Session):
    return db.query(models.User).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, data: schemas.UserCreate):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise ValueError("Email already exists")
    user = models.User(name=data.name, email=data.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: schemas.UserUpdate):
    user = get_user(db, user_id)
    if user is None:
        return None
    duplicate = db.query(models.User).filter(
        models.User.email == data.email,
        models.User.id != user_id,
    ).first()
    if duplicate:
        raise ValueError("Email already exists")
    user.name = data.name
    user.email = data.email
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user is None:
        return None
    db.delete(user)
    db.commit()
    return user
