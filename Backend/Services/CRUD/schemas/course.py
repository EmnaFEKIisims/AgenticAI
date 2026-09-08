# schemas/course.py
from pydantic import BaseModel, Field
from typing import Optional


class CourseCreate(BaseModel):
    title:                  str            = Field(..., min_length=1)
    description:            Optional[str]  = None
    total_hours:            float          = Field(..., gt=0)
    session_duration:       int            = Field(..., gt=0)  # minutes
    pedagogical_objectives: Optional[str]  = None


class CourseUpdate(BaseModel):
    title:                  Optional[str]   = None
    description:            Optional[str]   = None
    total_hours:            Optional[float] = Field(None, gt=0)
    session_duration:       Optional[int]   = Field(None, gt=0)
    pedagogical_objectives: Optional[str]   = None


class CourseResponse(BaseModel):
    id:                     int
    title:                  str
    description:            Optional[str]
    total_hours:            float
    session_duration:       int
    pedagogical_objectives: Optional[str]

    class Config:
        from_attributes = True