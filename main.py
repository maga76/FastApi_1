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
