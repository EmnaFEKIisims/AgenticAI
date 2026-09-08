# schemas/equipment.py
from pydantic import BaseModel, Field
from typing import Optional


class EquipmentCreate(BaseModel):
    name:           str           = Field(..., min_length=1)
    description:    Optional[str] = None
    total_quantity: int           = Field(default=1, gt=0)


class EquipmentUpdate(BaseModel):
    name:           Optional[str] = None
    description:    Optional[str] = None
    total_quantity: Optional[int] = Field(None, gt=0)


class EquipmentResponse(BaseModel):
    id:             int
    name:           str
    description:    Optional[str]
    total_quantity: int

    class Config:
        from_attributes = True