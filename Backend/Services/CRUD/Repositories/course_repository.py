# repositories/course_repository.py
from sqlalchemy.orm import Session
from models.course import Course

class CourseRepository:
    def __init__(self, db: Session): self.db = db

    def create(self, data: dict, user_id: str) -> Course:
        c = Course(**data, user_id=user_id)
        self.db.add(c); self.db.commit(); self.db.refresh(c); return c

    def get_by_id(self, cid: int, user_id: str) -> Course | None:
        return self.db.query(Course).filter(Course.id == cid, Course.user_id == user_id).first()

    def get_all(self, user_id: str, limit: int = 200) -> list[Course]:
        return self.db.query(Course).filter(Course.user_id == user_id).limit(limit).all()

    def update(self, cid: int, data: dict, user_id: str) -> Course | None:
        c = self.get_by_id(cid, user_id)
        if not c: return None
        for k, v in data.items(): setattr(c, k, v)
        self.db.commit(); self.db.refresh(c); return c

    def delete(self, cid: int, user_id: str) -> bool:
        c = self.get_by_id(cid, user_id)
        if not c: return False
        from models.schedule import ScheduleSlot
        used = self.db.query(ScheduleSlot).filter(
            ScheduleSlot.course_id == cid, ScheduleSlot.user_id == user_id,
            ScheduleSlot.status.in_(["draft","validated"])
        ).first()
        if used: raise ValueError("Course is used in an active planning.")
        self.db.delete(c); self.db.commit(); return True