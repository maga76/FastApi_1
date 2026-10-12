from sqlalchemy.orm import Session

from models import CartItem, Category, Favorite, Order, OrderItem, Product, Review, User
import schemas

def get_users(db: Session):
    return db.query(User).order_by(User.id).all()

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user):
    old_user = db.query(User).filter(User.email == user.email).first()
    if old_user:
        raise ValueError("Email already exists")
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user(db: Session, db_user: User, user):
    old_user = db.query(User).filter(
        User.email == user.email,
        User.id != db_user.id,
    ).first()
    if old_user:
        raise ValueError("Email already exists")
    db_user.name = user.name
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()

def get_categories(db: Session, search=None, sort_by="id", order="asc"):
    query = db.query(Category)
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    field = Category.name if sort_by == "name" else Category.id
    if order == "desc":
        query = query.order_by(field.desc())
    else:
        query = query.order_by(field)
    return query.all()

def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()

def create_category(db: Session, category):
    old_category = db.query(Category).filter(Category.name == category.name).first()
    if old_category:
        raise ValueError("Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

def update_category(db: Session, db_category: Category, category):
    old_category = db.query(Category).filter(
        Category.name == category.name,
        Category.id != db_category.id,
    ).first()
    if old_category:
        raise ValueError("Category already exists")
    db_category.name = category.name
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category: Category):
    if category.products:
        raise ValueError("Category has products")
    db.delete(category)
    db.commit()

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_products(
    db: Session,
    search=None,
    category_id=None,
    min_price=None,
    max_price=None,
    in_stock=None,
    skip=0,
    limit=10,
    sort_by="id",
    order="asc",
):
    query = db.query(Product)
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

    fields = {
        "id": Product.id,
        "name": Product.name,
        "price": Product.price,
        "stock": Product.stock,
    }
    field = fields.get(sort_by, Product.id)
    if order == "desc":
        query = query.order_by(field.desc())
    else:
        query = query.order_by(field)
    return query.offset(skip).limit(limit).all()

def create_product(db: Session, product):
    category = get_category(db, product.category_id)
    if category is None:
        raise ValueError("Category not found")
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(db: Session, db_product: Product, product):
    category = get_category(db, product.category_id)
    if category is None:
        raise ValueError("Category not found")
    db_product.name = product.name
    db_product.description = product.description
    db_product.price = product.price
    db_product.stock = product.stock
    db_product.category_id = product.category_id
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product: Product):
    order_items = db.query(OrderItem).filter(OrderItem.product_id == product.id).all()
    for item in order_items:
        order = get_order(db, item.order_id)
        if order and order.status != "cancelled":
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
    return db.query(CartItem).filter(
        CartItem.user_id == user_id
    ).order_by(CartItem.id).all()

def add_to_cart(db: Session, data: schemas.CartAdd):
    user = get_user(db, data.user_id)
    if user is None:
        raise ValueError("User not found")
    product = get_product(db, data.product_id)
    if product is None:
        raise ValueError("Product not found")
    if product.stock == 0:
        raise ValueError("Product is out of stock")

    cart_item = db.query(CartItem).filter(
        CartItem.user_id == data.user_id,
        CartItem.product_id == data.product_id,
    ).first()
    if cart_item:
        new_quantity = cart_item.quantity + data.quantity
    else:
        new_quantity = data.quantity
    if new_quantity > product.stock:
        raise ValueError("Not enough product in stock")

    if cart_item:
        cart_item.quantity = new_quantity
    else:
        cart_item = CartItem(
            user_id=data.user_id,
            product_id=data.product_id,
            quantity=data.quantity,
        )
        db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item

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
    cart_items = get_cart_items(db, user_id)
    items = []
    total_price = 0
    for cart_item in cart_items:
        subtotal = cart_item.product.price * cart_item.quantity
        total_price += subtotal
        items.append({
            "id": cart_item.id,
            "quantity": cart_item.quantity,
            "product": cart_item.product,
            "subtotal": round(subtotal, 2),
        })
    return {
        "user_id": user_id,
        "items": items,
        "total_price": round(total_price, 2),
    }

def get_order(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()

def get_order_total(cart_items):
    total_price = 0
    for item in cart_items:
        if item.quantity > item.product.stock:
            raise ValueError(f"Not enough stock for {item.product.name}")
        total_price += item.product.price * item.quantity
    return round(total_price, 2)

def add_order_items(db: Session, order: Order, cart_items):
    for item in cart_items:
        subtotal = item.product.price * item.quantity
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity,
            subtotal=round(subtotal, 2),
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
        new_order = Order(
            user_id=user_id,
            total_price=total_price,
            status="new",
        )
        db.add(new_order)
        db.flush()
        add_order_items(db, new_order, cart_items)
        db.commit()
        db.refresh(new_order)
        return new_order
    except Exception:
        db.rollback()
        raise

def get_orders(
    db: Session,
    status=None,
    user_id=None,
    skip=0,
    limit=10,
    sort_by="created_at",
    order="desc",
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    field = Order.total_price if sort_by == "total_price" else Order.created_at
    if order == "desc":
        query = query.order_by(field.desc())
    else:
        query = query.order_by(field)
    return query.offset(skip).limit(limit).all()

def update_order_status(db: Session, db_order: Order, status: str):
    if db_order.status == "cancelled":
        raise ValueError("Cancelled order cannot be changed")
    if status == "cancelled":
        for item in db_order.items:
            product = get_product(db, item.product_id)
            if product:
                product.stock += item.quantity
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order

def get_valid_user_orders(db: Session, user_id: int):
    return db.query(Order).filter(
        Order.user_id == user_id,
        Order.status != "cancelled",
    ).all()

def user_purchase_statistics(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    orders = get_valid_user_orders(db, user_id)
    total_spent = 0
    for order in orders:
        total_spent += order.total_price
    if orders:
        average_order = total_spent / len(orders)
    else:
        average_order = 0
    return {
        "user_id": user_id,
        "orders_count": len(orders),
        "total_spent": round(total_spent, 2),
        "average_order": round(average_order, 2),
    }

def purchased_products(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    orders = get_valid_user_orders(db, user_id)
    products = {}
    for order in orders:
        for item in order.items:
            if item.product_id not in products:
                products[item.product_id] = {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": 0,
                }
            products[item.product_id]["quantity"] += item.quantity
    return list(products.values())

def product_purchase_count(db: Session, user_id: int, product_id: int):
    if get_user(db, user_id) is None:
        return None
    orders = get_valid_user_orders(db, user_id)
    quantity = 0
    for order in orders:
        for item in order.items:
            if item.product_id == product_id:
                quantity += item.quantity
    return {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
    }

def get_review(db: Session, review_id: int):
    return db.query(Review).filter(Review.id == review_id).first()

def get_reviews(db: Session, product_id: int):
    if get_product(db, product_id) is None:
        return None
    return db.query(Review).filter(
        Review.product_id == product_id
    ).order_by(Review.id.desc()).all()

def create_review(db: Session, product_id: int, review):
    if get_product(db, product_id) is None:
        raise ValueError("Product not found")
    if get_user(db, review.user_id) is None:
        raise ValueError("User not found")
    new_review = Review(product_id=product_id, **review.model_dump())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

def delete_review(db: Session, review: Review):
    db.delete(review)
    db.commit()

def average_rating(db: Session, product_id: int):
    reviews = get_reviews(db, product_id)
    if reviews is None:
        return None
    total_rating = 0
    for review in reviews:
        total_rating += review.rating
    if reviews:
        result = total_rating / len(reviews)
    else:
        result = 0
    return {
        "product_id": product_id,
        "average_rating": round(result, 2),
    }

def products_by_rating(db: Session, minimum=None, maximum=None):
    products = db.query(Product).all()
    result = []
    for product in products:
        if not product.reviews:
            continue
        rating = average_rating(db, product.id)["average_rating"]
        if minimum is not None and rating < minimum:
            continue
        if maximum is not None and rating > maximum:
            continue
        result.append({
            "product_id": product.id,
            "name": product.name,
            "average_rating": rating,
        })
    return result

def get_favorite(db: Session, user_id: int, product_id: int):
    return db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.product_id == product_id,
    ).first()

def get_favorites(db: Session, user_id: int):
    if get_user(db, user_id) is None:
        return None
    return db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).order_by(Favorite.id).all()

def create_favorite(db: Session, favorite):
    if get_user(db, favorite.user_id) is None:
        raise ValueError("User not found")
    if get_product(db, favorite.product_id) is None:
        raise ValueError("Product not found")
    old_favorite = get_favorite(db, favorite.user_id, favorite.product_id)
    if old_favorite:
        raise ValueError("Product is already in favorites")
    new_favorite = Favorite(**favorite.model_dump())
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return new_favorite

def delete_favorite(db: Session, favorite: Favorite):
    db.delete(favorite)
    db.commit()

def favorite_exists(db: Session, user_id: int, product_id: int):
    favorite = get_favorite(db, user_id, product_id)
    return {"is_favorite": favorite is not None}

def get_valid_orders(db: Session):
    return db.query(Order).filter(Order.status != "cancelled").all()

def shop_statistics(db: Session):
    orders = get_valid_orders(db)
    total_orders_sum = 0
    for order in orders:
        total_orders_sum += order.total_price
    if orders:
        average_order_sum = total_orders_sum / len(orders)
    else:
        average_order_sum = 0
    return {
        "users_count": db.query(User).count(),
        "products_count": db.query(Product).count(),
        "categories_count": db.query(Category).count(),
        "orders_count": len(orders),
        "total_orders_sum": round(total_orders_sum, 2),
        "average_order_sum": round(average_order_sum, 2),
    }

def best_selling_product(db: Session):
    orders = get_valid_orders(db)
    products = {}
    for order in orders:
        for item in order.items:
            if item.product_id not in products:
                products[item.product_id] = {
                    "product_id": item.product_id,
                    "name": item.product_name,
                    "sold": 0,
                }
            products[item.product_id]["sold"] += item.quantity
    if not products:
        return None
    return max(products.values(), key=lambda product: product["sold"])

def top_user(db: Session):
    users = get_users(db)
    result = []
    for user in users:
        orders = get_valid_user_orders(db, user.id)
        total_spent = 0
        for order in orders:
            total_spent += order.total_price
        if orders:
            result.append({
                "user_id": user.id,
                "name": user.name,
                "total_spent": round(total_spent, 2),
            })
    if not result:
        return None
    return max(result, key=lambda user: user["total_spent"])
