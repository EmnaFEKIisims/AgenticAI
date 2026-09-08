# schemas/room.py
from pydantic import BaseModel, Field
from typing import Optional


class RoomCreate(BaseModel):
    name:      str           = Field(..., min_length=1)
    capacity:  int           = Field(..., gt=0)
    room_type: Optional[str] = None   # 'Lab', 'Classroom', 'Virtual'


class RoomUpdate(BaseModel):
    name:      Optional[str] = None
    capacity:  Optional[int] = Field(None, gt=0)
    room_type: Optional[str] = None


class RoomResponse(BaseModel):
    id:        int
    name:      str
    capacity:  int
    room_type: Optional[str]

    class Config:
        from_attributes = True