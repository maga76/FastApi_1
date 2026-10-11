from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import Base, engine, get_db


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Internet Shop API", version="1.0.0")


def bad_request(error: ValueError):
    raise HTTPException(status_code=400, detail=str(error))


@app.get("/")
def home():
    return {"message": "Internet Shop API is running"}


@app.post("/users/", response_model=schemas.UserRead, status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, data)
    except ValueError as error:
        bad_request(error)


@app.get("/users/", response_model=list[schemas.UserRead])
def get_users(db: Session = Depends(get_db)):
    return crud.get_users(db)


@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=schemas.UserRead)
def update_user(user_id: int, data: schemas.UserUpdate, db: Session = Depends(get_db)):
    try:
        user = crud.update_user(db, user_id, data)
    except ValueError as error:
        bad_request(error)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    if crud.delete_user(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@app.post("/categories/", response_model=schemas.CategoryRead, status_code=201)
def create_category(data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_category(db, data)
    except ValueError as error:
        bad_request(error)


@app.get("/categories/", response_model=list[schemas.CategoryRead])
def get_categories(
    search: str | None = Query(None, min_length=1),
    sort_by: Literal["id", "name"] = "id",
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    return crud.get_categories(db, search, sort_by, order)


@app.get("/categories/{category_id}", response_model=schemas.CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = crud.get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.put("/categories/{category_id}", response_model=schemas.CategoryRead)
def update_category(category_id: int, data: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    try:
        category = crud.update_category(db, category_id, data)
    except ValueError as error:
        bad_request(error)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    try:
        category = crud.delete_category(db, category_id)
    except ValueError as error:
        bad_request(error)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@app.get("/categories/{category_id}/products/", response_model=list[schemas.ProductNested])
def category_products(category_id: int, db: Session = Depends(get_db)):
    if crud.get_category(db, category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return crud.get_products(db, category_id=category_id, limit=100)


@app.get("/products/cheap/", response_model=list[schemas.ProductNested])
def cheap_products(max_price: float = Query(100, gt=0), db: Session = Depends(get_db)):
    return crud.get_products(db, max_price=max_price, limit=100, sort_by="price")


@app.get("/products/expensive/", response_model=list[schemas.ProductNested])
def expensive_products(min_price: float = Query(100, gt=0), db: Session = Depends(get_db)):
    return crud.get_products(db, min_price=min_price, limit=100, sort_by="price", order="desc")


@app.get("/products/out-of-stock/", response_model=list[schemas.ProductNested])
def out_of_stock_products(db: Session = Depends(get_db)):
    return crud.get_products(db, in_stock=False, limit=100)


@app.get("/products/low-stock/", response_model=list[schemas.ProductNested])
def low_stock_products(db: Session = Depends(get_db)):
    return db.query(models.Product).filter(
        models.Product.stock > 0,
        models.Product.stock < 5,
    ).order_by(models.Product.stock.asc()).all()


@app.post("/products/", response_model=schemas.ProductNested, status_code=201)
def create_product(data: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_product(db, data)
    except ValueError as error:
        bad_request(error)


@app.get("/products/", response_model=list[schemas.ProductNested])
def get_products(
    search: str | None = Query(None, min_length=1),
    category_id: int | None = Query(None, ge=1),
    min_price: float | None = Query(None, gt=0),
    max_price: float | None = Query(None, gt=0),
    in_stock: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: Literal["id", "name", "price", "stock"] = "id",
    order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price")
    return crud.get_products(
        db, search, category_id, min_price, max_price, in_stock,
        (page - 1) * page_size, page_size, sort_by, order,
    )


@app.get("/products/{product_id}", response_model=schemas.ProductNested)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}", response_model=schemas.ProductNested)
def update_product(product_id: int, data: schemas.ProductUpdate, db: Session = Depends(get_db)):
    try:
        product = crud.update_product(db, product_id, data)
    except ValueError as error:
        bad_request(error)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = crud.delete_product(db, product_id)
    except ValueError as error:
        bad_request(error)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}


@app.get("/products/{product_id}/similar/", response_model=list[schemas.ProductRead])
def similar_products(product_id: int, db: Session = Depends(get_db)):
    products = crud.get_similar_products(db, product_id)
    if products is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return products


@app.post("/cart/add/", response_model=schemas.CartRead)
def add_to_cart(data: schemas.CartAdd, db: Session = Depends(get_db)):
    try:
        crud.add_to_cart(db, data)
    except ValueError as error:
        bad_request(error)
    return crud.cart_response(db, data.user_id)


@app.get("/cart/{user_id}", response_model=schemas.CartRead)
def get_cart(user_id: int, db: Session = Depends(get_db)):
    result = crud.cart_response(db, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@app.put("/cart/items/{cart_item_id}")
def change_cart_quantity(
    cart_item_id: int,
    data: schemas.CartQuantity,
    db: Session = Depends(get_db),
):
    try:
        item = crud.change_cart_quantity(db, cart_item_id, data.quantity)
    except ValueError as error:
        bad_request(error)
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Quantity changed", "quantity": item.quantity}


@app.patch("/cart/items/{cart_item_id}/decrease")
def decrease_cart_item(cart_item_id: int, db: Session = Depends(get_db)):
    try:
        item = crud.decrease_cart_item(db, cart_item_id)
    except ValueError as error:
        bad_request(error)
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Quantity decreased", "quantity": item.quantity}


@app.delete("/cart/items/{cart_item_id}")
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db)):
    if crud.delete_cart_item(db, cart_item_id) is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Product removed from cart"}


@app.delete("/cart/clear/{user_id}")
def clear_cart(user_id: int, db: Session = Depends(get_db)):
    if crud.clear_cart(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Cart cleared"}


@app.post("/orders/create/", response_model=schemas.OrderRead, status_code=201)
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_order(db, data.user_id)
    except ValueError as error:
        bad_request(error)


@app.get("/orders/", response_model=list[schemas.OrderRead])
def get_orders(
    status: Literal["new", "paid", "cancelled"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: Literal["total_price", "created_at"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
):
    return crud.get_orders(
        db, status, None, (page - 1) * page_size, page_size, sort_by, order
    )


@app.get("/orders/{order_id}", response_model=schemas.OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/orders/{order_id}/status", response_model=schemas.OrderRead)
def update_order_status(
    order_id: int,
    data: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        order = crud.update_order_status(db, order_id, data.status)
    except ValueError as error:
        bad_request(error)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/orders/{order_id}/cancel", response_model=schemas.OrderRead)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = crud.update_order_status(db, order_id, "cancelled")
    except ValueError as error:
        bad_request(error)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/users/{user_id}/orders/", response_model=list[schemas.OrderRead])
def user_orders(user_id: int, db: Session = Depends(get_db)):
    if crud.get_user(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_orders(db, None, user_id, 0, 100, "created_at", "desc")


@app.get("/users/{user_id}/statistics/")
def user_statistics(user_id: int, db: Session = Depends(get_db)):
    result = crud.user_purchase_statistics(db, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@app.get("/users/{user_id}/purchases/", response_model=list[schemas.OrderRead])
def user_purchase_history(user_id: int, db: Session = Depends(get_db)):
    if crud.get_user(db, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_orders(db, None, user_id, 0, 100, "created_at", "desc")


@app.get("/users/{user_id}/purchases/last", response_model=schemas.OrderRead)
def last_user_order(user_id: int, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, None, user_id, 0, 1, "created_at", "desc")
    if not orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[0]


@app.get("/users/{user_id}/purchases/most-expensive", response_model=schemas.OrderRead)
def most_expensive_user_order(user_id: int, db: Session = Depends(get_db)):
    orders = crud.get_orders(db, None, user_id, 0, 1, "total_price", "desc")
    if not orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[0]


@app.get("/users/{user_id}/purchased-products/")
def user_purchased_products(user_id: int, db: Session = Depends(get_db)):
    result = crud.purchased_products(db, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@app.get("/users/{user_id}/purchased-products/{product_id}/count")
def user_product_purchase_count(user_id: int, product_id: int, db: Session = Depends(get_db)):
    result = crud.product_purchase_count(db, user_id, product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result
