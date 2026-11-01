from typing import List, Optional
from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace
from labs.lab03 import repository

router = APIRouter()

@router.get("", response_model=List[RecordRead])
def read_records(
    category_id: Optional[int] = Query(None, gt=0),
    status: Optional[str] = None,
    min_value: Optional[float] = None,
    q: Optional[str] = Query(None, min_length=1, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return repository.get_records(category_id, status, min_value, q, limit, offset)

@router.get("/{record_id}", response_model=RecordRead)
def read_record(record_id: int = Path(..., gt=0)):
    record = repository.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    return record

@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_record(record: RecordCreate):
    created = repository.create_record(record.model_dump())
    if not created:
        raise HTTPException(status_code=409, detail="Дублікат code або неіснуюча категорія")
    return created

@router.put("/{record_id}", response_model=RecordRead)
def update_record(record_id: int, record: RecordReplace):
    if record_id <= 0:
        raise HTTPException(status_code=422, detail="id має бути додатним")
    try:
        updated = repository.update_record(record_id, record.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Запис не знайдено")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int = Path(..., gt=0)):
    if not repository.delete_record(record_id):
        raise HTTPException(status_code=404, detail="Запис не знайдено")

@router.post("/bulk", response_model=List[RecordRead], status_code=status.HTTP_201_CREATED)
def bulk_create_records(records: List[RecordCreate] = Body(..., min_length=1, max_length=100)):
    created = repository.bulk_create_records([r.model_dump() for r in records])
    if created is None:
        raise HTTPException(status_code=409, detail="Конфлікт даних у пакеті (дублікат або категорія 404)")
    return created