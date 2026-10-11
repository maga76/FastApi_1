from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def clean_text(value: str):
    if not value.strip():
        raise ValueError("Field cannot be empty")
    return value.strip()
