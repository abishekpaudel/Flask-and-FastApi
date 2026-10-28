import mysql.connector
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

from common.db import init_db, list_parts, get_part, create_part, update_part, delete_part


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Marine Parts Inventory API", version="1.0.0", lifespan=lifespan)


class PartInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=0)
    price: float = Field(ge=0)


def normalized(data: PartInput):
    payload = data.model_dump()
    payload["name"] = payload["name"].strip()
    payload["sku"] = payload["sku"].strip()
    if not payload["name"] or not payload["sku"]:
        raise HTTPException(status_code=422, detail="Name and SKU cannot be blank")
    return payload


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/parts")
def all_parts():
    return list_parts()


@app.get("/parts/{part_id}")
def one_part(part_id: Annotated[int, Path(gt=0)]):
    part = get_part(part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@app.post("/parts", status_code=201)
def add_part(data: PartInput):
    try:
        return create_part(normalized(data))
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=409, detail="SKU already exists or data violates a database constraint")


@app.put("/parts/{part_id}")
def replace_part(part_id: Annotated[int, Path(gt=0)], data: PartInput):
    try:
        part = update_part(part_id, normalized(data))
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=409, detail="SKU already exists or data violates a database constraint")
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@app.delete("/parts/{part_id}", status_code=204)
def remove_part(part_id: Annotated[int, Path(gt=0)]):
    if not delete_part(part_id):
        raise HTTPException(status_code=404, detail="Part not found")
    return None
