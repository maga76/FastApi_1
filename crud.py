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


def get_categories(db: Session, search: str | None, sort_by: str, order: str):
    query = db.query(models.Category)
    if search:
        query = query.filter(models.Category.name.contains(search))
    column = models.Category.name if sort_by == "name" else models.Category.id
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.all()


def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def create_category(db: Session, data: schemas.CategoryCreate):
    if db.query(models.Category).filter(models.Category.name == data.name).first():
        raise ValueError("Category already exists")
    category = models.Category(name=data.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: schemas.CategoryUpdate):
    category = get_category(db, category_id)
    if category is None:
        return None
    duplicate = db.query(models.Category).filter(
        models.Category.name == data.name,
        models.Category.id != category_id,
    ).first()
    if duplicate:
        raise ValueError("Category already exists")
    category.name = data.name
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int):
    category = get_category(db, category_id)
    if category is None:
        return None
    if category.products:
        raise ValueError("Category has products")
    db.delete(category)
    db.commit()
    return category
