# schemas/trainer.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class TrainerCreate(BaseModel):
    name:               str           = Field(..., min_length=1)
    email:              str           = Field(..., min_length=5)
    specialization:     Optional[str] = None
    availability_notes: Optional[str] = None


class TrainerUpdate(BaseModel):
    name:               Optional[str] = None
    email:              Optional[str] = None
    specialization:     Optional[str] = None
    availability_notes: Optional[str] = None


class TrainerResponse(BaseModel):
    id:                 int
    name:               str
    email:              str
    specialization:     Optional[str]
    availability_notes: Optional[str]

    class Config:
        from_attributes = True