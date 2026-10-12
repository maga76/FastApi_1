from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import CartItem, Category, Favorite, Order, OrderItem, Product, Review, User
import schemas


def get_users(db: Session):
    return db.query(User).order_by(User.id).all()


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, data: schemas.UserCreate):
    if db.query(User).filter(User.email == data.email).first():
        raise ValueError("Email already exists")
    new_user = User(name=data.name, email=data.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(db: Session, db_user: User, data: schemas.UserUpdate):
    duplicate = db.query(User).filter(
        User.email == data.email,
        User.id != db_user.id,
    ).first()
    if duplicate:
        raise ValueError("Email already exists")
    db_user.name = data.name
    db_user.email = data.email
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()


def get_categories(db: Session, search: str | None, sort_by: str, order: str):
    query = db.query(Category)
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    column = Category.name if sort_by == "name" else Category.id
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.all()


def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(db: Session, data: schemas.CategoryCreate):
    if db.query(Category).filter(Category.name == data.name).first():
        raise ValueError("Category already exists")
    new_category = Category(name=data.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def update_category(db: Session, db_category: Category, data: schemas.CategoryUpdate):
    duplicate = db.query(Category).filter(
        Category.name == data.name,
        Category.id != db_category.id,
    ).first()
    if duplicate:
        raise ValueError("Category already exists")
    db_category.name = data.name
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category: Category):
    if category.products:
        raise ValueError("Category has products")
    db.delete(category)
    db.commit()


def get_product(db: Session, product_id: int):
    return db.query(Product).options(joinedload(Product.category)).filter(
        Product.id == product_id
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
    query = db.query(Product).options(joinedload(Product.category))
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is True:
        query = query.filter(Product.stock > 0)
    if in_stock is False:
        query = query.filter(Product.stock == 0)
    columns = {
        "id": Product.id,
        "name": Product.name,
        "price": Product.price,
        "stock": Product.stock,
    }
    column = columns.get(sort_by, Product.id)
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.offset(skip).limit(limit).all()


def create_product(db: Session, data: schemas.ProductCreate):
    if get_category(db, data.category_id) is None:
        raise ValueError("Category not found")
    new_product = Product(**data.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return get_product(db, new_product.id)


def update_product(db: Session, db_product: Product, data: schemas.ProductUpdate):
    if get_category(db, data.category_id) is None:
        raise ValueError("Category not found")
    for field, value in data.model_dump().items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product: Product):
    active_order = db.query(OrderItem).join(Order).filter(
        OrderItem.product_id == product.id,
        Order.status != "cancelled",
    ).first()
    if active_order:
        raise ValueError("Product is in an active order")
    db.query(CartItem).filter(CartItem.product_id == product.id).delete()
    db.delete(product)
    db.commit()


def get_similar_products(db: Session, product_id: int):
    product = get_product(db, product_id)
    if product is None:
        return None
    return db.query(Product).filter(
        Product.category_id == product.category_id,
        Product.id != product_id,
    ).limit(10).all()


def get_cart_item(db: Session, cart_item_id: int):
    return db.query(CartItem).filter(CartItem.id == cart_item_id).first()


def get_cart_items(db: Session, user_id: int):
    return db.query(CartItem).options(joinedload(CartItem.product)).filter(
        CartItem.user_id == user_id
    ).order_by(CartItem.id).all()


def add_to_cart(db: Session, data: schemas.CartAdd):
    if get_user(db, data.user_id) is None:
        raise ValueError("User not found")
    product = get_product(db, data.product_id)
    if product is None:
        raise ValueError("Product not found")
    if product.stock == 0:
        raise ValueError("Product is out of stock")
    item = db.query(CartItem).filter(
        CartItem.user_id == data.user_id,
        CartItem.product_id == data.product_id,
    ).first()
    new_quantity = data.quantity + (item.quantity if item else 0)
    if new_quantity > product.stock:
        raise ValueError("Not enough product in stock")
    if item:
        item.quantity = new_quantity
    else:
        item = CartItem(**data.model_dump())
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


def change_cart_quantity(db: Session, cart_item: CartItem, quantity: int):
    product = get_product(db, cart_item.product_id)
    if quantity > product.stock:
        raise ValueError("Not enough product in stock")
    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item


def decrease_cart_item(db: Session, cart_item: CartItem):
    if cart_item.quantity <= 1:
        raise ValueError("Quantity cannot be less than 1")
    cart_item.quantity -= 1
    db.commit()
    db.refresh(cart_item)
    return cart_item


def delete_cart_item(db: Session, cart_item: CartItem):
    db.delete(cart_item)
    db.commit()


def clear_cart(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    return True


def cart_response(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    items = get_cart_items(db, user_id)
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


def get_order_total(cart_items):
    total_price = 0
    for item in cart_items:
        if item.quantity > item.product.stock:
            raise ValueError(f"Not enough stock for {item.product.name}")
        total_price += item.product.price * item.quantity
    return round(total_price, 2)


def add_order_items(db: Session, order: Order, cart_items):
    for item in cart_items:
        subtotal = round(item.product.price * item.quantity, 2)
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity,
            subtotal=subtotal,
        )
        db.add(order_item)
        item.product.stock -= item.quantity
        db.delete(item)


def create_order(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        raise ValueError("User not found")
    cart_items = get_cart_items(db, user_id)
    if not cart_items:
        raise ValueError("Cart is empty")
    total_price = get_order_total(cart_items)
    try:
        new_order = Order(user_id=user_id, total_price=total_price, status="new")
        db.add(new_order)
        db.flush()
        add_order_items(db, new_order, cart_items)
        db.commit()
        db.refresh(new_order)
        return get_order(db, new_order.id)
    except Exception:
        db.rollback()
        raise


def get_order(db: Session, order_id: int):
    return db.query(Order).options(joinedload(Order.items)).filter(
        Order.id == order_id
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
    query = db.query(Order).options(joinedload(Order.items))
    if status:
        query = query.filter(Order.status == status)
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    column = Order.total_price if sort_by == "total_price" else Order.created_at
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    return query.offset(skip).limit(limit).all()


def update_order_status(db: Session, db_order: Order, status: str):
    if db_order.status == "cancelled":
        raise ValueError("Cancelled order cannot be changed")
    if status == "cancelled":
        for item in db_order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return get_order(db, db_order.id)


def user_purchase_statistics(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.status != "cancelled",
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
        OrderItem.product_id,
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label("quantity"),
    ).join(Order).filter(
        Order.user_id == user_id,
        Order.status != "cancelled",
    ).group_by(OrderItem.product_id, OrderItem.product_name).all()
    return [
        {"product_id": row.product_id, "product_name": row.product_name, "quantity": row.quantity}
        for row in rows
    ]


def product_purchase_count(db: Session, user_id: int, product_id: int):
    if get_user(db, user_id) is None:
        return None
    quantity = db.query(func.coalesce(func.sum(OrderItem.quantity), 0)).join(
        Order
    ).filter(
        Order.user_id == user_id,
        Order.status != "cancelled",
        OrderItem.product_id == product_id,
    ).scalar()
    return {"user_id": user_id, "product_id": product_id, "quantity": quantity}


def create_review(db: Session, product_id: int, data: schemas.ReviewCreate):
    if get_product(db, product_id) is None:
        raise ValueError("Product not found")
    if get_user(db, data.user_id) is None:
        raise ValueError("User not found")
    new_review = Review(product_id=product_id, **data.model_dump())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


def get_reviews(db: Session, product_id: int):
    if get_product(db, product_id) is None:
        return None
    return db.query(Review).filter(Review.product_id == product_id).all()


def get_review(db: Session, review_id: int):
    return db.query(Review).filter(Review.id == review_id).first()


def delete_review(db: Session, review: Review):
    db.delete(review)
    db.commit()


def average_rating(db: Session, product_id: int):
    if get_product(db, product_id) is None:
        return None
    value = db.query(func.avg(Review.rating)).filter(
        Review.product_id == product_id
    ).scalar()
    return {"product_id": product_id, "average_rating": round(value or 0, 2)}


def products_by_rating(db: Session, minimum: float | None = None, maximum: float | None = None):
    query = db.query(
        Product.id,
        Product.name,
        func.avg(Review.rating).label("average_rating"),
    ).join(Review).group_by(Product.id, Product.name)
    if minimum is not None:
        query = query.having(func.avg(Review.rating) >= minimum)
    if maximum is not None:
        query = query.having(func.avg(Review.rating) <= maximum)
    return [
        {"product_id": row.id, "name": row.name, "average_rating": round(row.average_rating, 2)}
        for row in query.all()
    ]


def get_favorite(db: Session, user_id: int, product_id: int):
    return db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.product_id == product_id,
    ).first()


def create_favorite(db: Session, data: schemas.FavoriteCreate):
    if get_user(db, data.user_id) is None:
        raise ValueError("User not found")
    if get_product(db, data.product_id) is None:
        raise ValueError("Product not found")
    exists = get_favorite(db, data.user_id, data.product_id)
    if exists:
        raise ValueError("Product is already in favorites")
    new_favorite = Favorite(**data.model_dump())
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return db.query(Favorite).options(joinedload(Favorite.product)).filter(
        Favorite.id == new_favorite.id
    ).first()


def get_favorites(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    return db.query(Favorite).options(joinedload(Favorite.product)).filter(
        Favorite.user_id == user_id
    ).all()


def delete_favorite(db: Session, favorite: Favorite):
    db.delete(favorite)
    db.commit()


def favorite_exists(db: Session, user_id: int, product_id: int):
    favorite = get_favorite(db, user_id, product_id)
    return {"is_favorite": favorite is not None}


def shop_statistics(db: Session):
    orders = db.query(Order).filter(Order.status != "cancelled").all()
    total = round(sum(order.total_price for order in orders), 2)
    return {
        "users_count": db.query(User).count(),
        "products_count": db.query(Product).count(),
        "categories_count": db.query(Category).count(),
        "orders_count": len(orders),
        "total_orders_sum": total,
        "average_order_sum": round(total / len(orders), 2) if orders else 0,
    }


def best_selling_product(db: Session):
    row = db.query(
        OrderItem.product_id,
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label("sold"),
    ).join(Order).filter(Order.status != "cancelled").group_by(
        OrderItem.product_id,
        OrderItem.product_name,
    ).order_by(func.sum(OrderItem.quantity).desc()).first()
    if row is None:
        return None
    return {"product_id": row.product_id, "name": row.product_name, "sold": row.sold}


def top_user(db: Session):
    row = db.query(
        User.id,
        User.name,
        func.sum(Order.total_price).label("spent"),
    ).join(Order).filter(Order.status != "cancelled").group_by(
        User.id,
        User.name,
    ).order_by(func.sum(Order.total_price).desc()).first()
    if row is None:
        return None
    return {"user_id": row.id, "name": row.name, "total_spent": round(row.spent, 2)}
