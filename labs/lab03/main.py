from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared import student
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Створюємо відсутні таблиці під час запуску (без перезапису даних)
    initialize_database()
    yield

app = FastAPI(
    title="Облік часу опрацювання повідомлень",
    description="Сервіс обліку тривалості перевірки повідомлень про події безпеки. Одиниця вимірювання: хвилини.",
    lifespan=lifespan
)

app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(records.router, prefix="/records", tags=["Records"])

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/student")
def get_student_info():
    return {
        "student_name": student.student_name,
        "group_name": student.group_name,
        "variant_number": student.variant_number
    }