from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def clean_text(value: str):
    if not value.strip():
        raise ValueError("Field cannot be empty")
    return value.strip()


class UserCreate(BaseModel):
    name: str
    email: str

    @field_validator("name", "email")
    @classmethod
    def validate_text(cls, value: str):
        return clean_text(value)


class UserUpdate(UserCreate):
    pass


class UserRead(UserCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        return clean_text(value)


class CategoryUpdate(CategoryCreate):
    pass


class CategoryRead(CategoryCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        return clean_text(value)


class ProductUpdate(ProductCreate):
    pass


class ProductRead(ProductCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProductNested(ProductRead):
    category: CategoryRead


class CartAdd(BaseModel):
    user_id: int = Field(ge=1)
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1)


class CartQuantity(BaseModel):
    quantity: int = Field(ge=1)


class CartItemRead(BaseModel):
    id: int
    quantity: int
    product: ProductRead
    subtotal: float


class CartRead(BaseModel):
    user_id: int
    items: list[CartItemRead]
    total_price: float


class OrderCreate(BaseModel):
    user_id: int = Field(ge=1)


class OrderStatusUpdate(BaseModel):
    status: Literal["new", "paid", "cancelled"]


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float
    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str
    created_at: datetime
    items: list[OrderItemRead]
    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    user_id: int = Field(ge=1)
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewRead(ReviewCreate):
    id: int
    product_id: int
    model_config = ConfigDict(from_attributes=True)


class FavoriteCreate(BaseModel):
    user_id: int = Field(ge=1)
    product_id: int = Field(ge=1)


class FavoriteRead(BaseModel):
    id: int
    user_id: int
    product: ProductRead
    model_config = ConfigDict(from_attributes=True)
