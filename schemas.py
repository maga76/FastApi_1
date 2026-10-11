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
