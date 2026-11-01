from typing import List
from fastapi import APIRouter, HTTPException, status
from labs.lab03.schemas import CategoryCreate, CategoryRead
from labs.lab03 import repository

router = APIRouter()

@router.get("", response_model=List[CategoryRead])
def read_categories():
    return repository.get_categories()

@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate):
    created = repository.create_category(category.name)
    if not created:
        raise HTTPException(status_code=409, detail="Категорія з такою назвою вже існує")
    return created

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int):
    try:
        deleted = repository.delete_category(category_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Категорію не знайдено")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))