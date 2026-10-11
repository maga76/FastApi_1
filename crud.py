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


def get_product(db: Session, product_id: int):
    return db.query(models.Product).options(joinedload(models.Product.category)).filter(
        models.Product.id == product_id
    ).first()


def get_products(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    order: str = "asc",
):
    query = db.query(models.Product).options(joinedload(models.Product.category))
    if search:
        query = query.filter(models.Product.name.contains(search))
    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    if in_stock is True:
        query = query.filter(models.Product.stock > 0)
    if in_stock is False:
        query = query.filter(models.Product.stock == 0)
    columns = {
        "id": models.Product.id,
        "name": models.Product.name,
        "price": models.Product.price,
        "stock": models.Product.stock,
    }
    column = columns.get(sort_by, models.Product.id)
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.offset(skip).limit(limit).all()


def create_product(db: Session, data: schemas.ProductCreate):
    if get_category(db, data.category_id) is None:
        raise ValueError("Category not found")
    product = models.Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return get_product(db, product.id)


def update_product(db: Session, product_id: int, data: schemas.ProductUpdate):
    product = get_product(db, product_id)
    if product is None:
        return None
    if get_category(db, data.category_id) is None:
        raise ValueError("Category not found")
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    if product is None:
        return None
    active_order = db.query(models.OrderItem).join(models.Order).filter(
        models.OrderItem.product_id == product_id,
        models.Order.status != "cancelled",
    ).first()
    if active_order:
        raise ValueError("Product is in an active order")
    db.query(models.CartItem).filter(models.CartItem.product_id == product_id).delete()
    db.delete(product)
    db.commit()
    return product


def get_similar_products(db: Session, product_id: int):
    product = get_product(db, product_id)
    if product is None:
        return None
    return db.query(models.Product).filter(
        models.Product.category_id == product.category_id,
        models.Product.id != product_id,
    ).limit(10).all()
