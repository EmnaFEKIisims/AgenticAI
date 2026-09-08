# schemas/learner_group.py
from pydantic import BaseModel, Field
from typing import Optional


class LearnerGroupCreate(BaseModel):
    name:  str           = Field(..., min_length=1)
    size:  int           = Field(default=1, gt=0)
    level: Optional[str] = None   # e.g. 'beginner', 'intermediate', 'advanced'


class LearnerGroupUpdate(BaseModel):
    name:  Optional[str] = None
    size:  Optional[int] = Field(None, gt=0)
    level: Optional[str] = None


class LearnerGroupResponse(BaseModel):
    id:    int
    name:  str
    size:  int
    level: Optional[str]

    class Config:
        from_attributes = True