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


def get_cart_item(db: Session, cart_item_id: int):
    return db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()


def add_to_cart(db: Session, data: schemas.CartAdd):
    if get_user(db, data.user_id) is None:
        raise ValueError("User not found")
    product = get_product(db, data.product_id)
    if product is None:
        raise ValueError("Product not found")
    if product.stock == 0:
        raise ValueError("Product is out of stock")
    item = db.query(models.CartItem).filter(
        models.CartItem.user_id == data.user_id,
        models.CartItem.product_id == data.product_id,
    ).first()
    new_quantity = data.quantity + (item.quantity if item else 0)
    if new_quantity > product.stock:
        raise ValueError("Not enough product in stock")
    if item:
        item.quantity = new_quantity
    else:
        item = models.CartItem(**data.model_dump())
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


def change_cart_quantity(db: Session, cart_item_id: int, quantity: int):
    item = get_cart_item(db, cart_item_id)
    if item is None:
        return None
    product = get_product(db, item.product_id)
    if quantity > product.stock:
        raise ValueError("Not enough product in stock")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


def decrease_cart_item(db: Session, cart_item_id: int):
    item = get_cart_item(db, cart_item_id)
    if item is None:
        return None
    if item.quantity <= 1:
        raise ValueError("Quantity cannot be less than 1")
    item.quantity -= 1
    db.commit()
    db.refresh(item)
    return item


def delete_cart_item(db: Session, cart_item_id: int):
    item = get_cart_item(db, cart_item_id)
    if item is None:
        return None
    db.delete(item)
    db.commit()
    return item


def clear_cart(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    db.commit()
    return True


def cart_response(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    items = db.query(models.CartItem).options(joinedload(models.CartItem.product)).filter(
        models.CartItem.user_id == user_id
    ).all()
    result = []
    total = 0
    for item in items:
        subtotal = round(item.product.price * item.quantity, 2)
        total += subtotal
        result.append({
            "id": item.id,
            "quantity": item.quantity,
            "product": item.product,
            "subtotal": subtotal,
        })
    return {"user_id": user_id, "items": result, "total_price": round(total, 2)}


def create_order(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        raise ValueError("User not found")
    cart_items = db.query(models.CartItem).options(joinedload(models.CartItem.product)).filter(
        models.CartItem.user_id == user_id
    ).all()
    if not cart_items:
        raise ValueError("Cart is empty")
    for item in cart_items:
        if item.quantity > item.product.stock:
            raise ValueError(f"Not enough stock for {item.product.name}")
    total = round(sum(item.product.price * item.quantity for item in cart_items), 2)
    order = models.Order(user_id=user_id, total_price=total, status="new")
    db.add(order)
    db.flush()
    for item in cart_items:
        subtotal = round(item.product.price * item.quantity, 2)
        db.add(models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity,
            subtotal=subtotal,
        ))
        item.product.stock -= item.quantity
        db.delete(item)
    db.commit()
    return get_order(db, order.id)


def get_order(db: Session, order_id: int):
    return db.query(models.Order).options(joinedload(models.Order.items)).filter(
        models.Order.id == order_id
    ).first()


def get_orders(
    db: Session,
    status: str | None,
    user_id: int | None,
    skip: int,
    limit: int,
    sort_by: str,
    order: str,
):
    query = db.query(models.Order).options(joinedload(models.Order.items))
    if status:
        query = query.filter(models.Order.status == status)
    if user_id is not None:
        query = query.filter(models.Order.user_id == user_id)
    column = models.Order.total_price if sort_by == "total_price" else models.Order.created_at
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.offset(skip).limit(limit).all()


def update_order_status(db: Session, order_id: int, status: str):
    order = get_order(db, order_id)
    if order is None:
        return None
    if order.status == "cancelled":
        raise ValueError("Cancelled order cannot be changed")
    if status == "cancelled":
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity
    order.status = status
    db.commit()
    return get_order(db, order_id)


def user_purchase_statistics(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    orders = db.query(models.Order).filter(
        models.Order.user_id == user_id,
        models.Order.status != "cancelled",
    ).all()
    total = round(sum(order.total_price for order in orders), 2)
    return {
        "user_id": user_id,
        "orders_count": len(orders),
        "total_spent": total,
        "average_order": round(total / len(orders), 2) if orders else 0,
    }


def purchased_products(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    rows = db.query(
        models.OrderItem.product_id,
        models.OrderItem.product_name,
        func.sum(models.OrderItem.quantity).label("quantity"),
    ).join(models.Order).filter(
        models.Order.user_id == user_id,
        models.Order.status != "cancelled",
    ).group_by(models.OrderItem.product_id, models.OrderItem.product_name).all()
    return [
        {"product_id": row.product_id, "product_name": row.product_name, "quantity": row.quantity}
        for row in rows
    ]


def product_purchase_count(db: Session, user_id: int, product_id: int):
    if get_user(db, user_id) is None:
        return None
    quantity = db.query(func.coalesce(func.sum(models.OrderItem.quantity), 0)).join(
        models.Order
    ).filter(
        models.Order.user_id == user_id,
        models.Order.status != "cancelled",
        models.OrderItem.product_id == product_id,
    ).scalar()
    return {"user_id": user_id, "product_id": product_id, "quantity": quantity}


def create_review(db: Session, product_id: int, data: schemas.ReviewCreate):
    if get_product(db, product_id) is None:
        raise ValueError("Product not found")
    if get_user(db, data.user_id) is None:
        raise ValueError("User not found")
    review = models.Review(product_id=product_id, **data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_reviews(db: Session, product_id: int):
    if get_product(db, product_id) is None:
        return None
    return db.query(models.Review).filter(models.Review.product_id == product_id).all()


def delete_review(db: Session, review_id: int):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review is None:
        return None
    db.delete(review)
    db.commit()
    return review


def average_rating(db: Session, product_id: int):
    if get_product(db, product_id) is None:
        return None
    value = db.query(func.avg(models.Review.rating)).filter(
        models.Review.product_id == product_id
    ).scalar()
    return {"product_id": product_id, "average_rating": round(value or 0, 2)}


def products_by_rating(db: Session, minimum: float | None = None, maximum: float | None = None):
    query = db.query(
        models.Product.id,
        models.Product.name,
        func.avg(models.Review.rating).label("average_rating"),
    ).join(models.Review).group_by(models.Product.id, models.Product.name)
    if minimum is not None:
        query = query.having(func.avg(models.Review.rating) >= minimum)
    if maximum is not None:
        query = query.having(func.avg(models.Review.rating) <= maximum)
    return [
        {"product_id": row.id, "name": row.name, "average_rating": round(row.average_rating, 2)}
        for row in query.all()
    ]


def add_favorite(db: Session, data: schemas.FavoriteCreate):
    if get_user(db, data.user_id) is None:
        raise ValueError("User not found")
    if get_product(db, data.product_id) is None:
        raise ValueError("Product not found")
    exists = db.query(models.Favorite).filter(
        models.Favorite.user_id == data.user_id,
        models.Favorite.product_id == data.product_id,
    ).first()
    if exists:
        raise ValueError("Product is already in favorites")
    favorite = models.Favorite(**data.model_dump())
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return db.query(models.Favorite).options(joinedload(models.Favorite.product)).filter(
        models.Favorite.id == favorite.id
    ).first()


def get_favorites(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    return db.query(models.Favorite).options(joinedload(models.Favorite.product)).filter(
        models.Favorite.user_id == user_id
    ).all()


def delete_favorite(db: Session, user_id: int, product_id: int):
    favorite = db.query(models.Favorite).filter(
        models.Favorite.user_id == user_id,
        models.Favorite.product_id == product_id,
    ).first()
    if favorite is None:
        return None
    db.delete(favorite)
    db.commit()
    return favorite


def favorite_exists(db: Session, user_id: int, product_id: int):
    favorite = db.query(models.Favorite).filter(
        models.Favorite.user_id == user_id,
        models.Favorite.product_id == product_id,
    ).first()
    return {"is_favorite": favorite is not None}
