from pydantic import BaseModel
from datetime import datetime


class StoreCreate(BaseModel):
    name: str
    store_number: str
    address: str | None = None
    city: str | None = None
    state: str | None = None


class StoreSchema(BaseModel):
    id: int
    name: str
    store_number: str
    address: str | None
    city: str | None
    state: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
