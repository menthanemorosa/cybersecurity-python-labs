from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

# Моделі для категорій
class CategoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=2, max_length=40)

class CategoryRead(CategoryCreate):
    id: int

# Моделі для записів
class RecordCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: float = Field(ge=0.0, allow_inf_nan=False)
    status: Literal["new", "in_progress", "done"]

class RecordReplace(RecordCreate):
    # Усі змінювані поля обов'язкові, тому можна просто успадкувати RecordCreate
    pass

class RecordRead(RecordCreate):
    id: int
    category_name: str