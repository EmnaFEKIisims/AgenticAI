# repositories/learner_group_repository.py
from sqlalchemy.orm import Session
from models.learner import LearnerGroup

class LearnerGroupRepository:
    def __init__(self, db: Session): self.db = db

    def create(self, data: dict, user_id: str) -> LearnerGroup:
        g = LearnerGroup(**data, user_id=user_id)
        self.db.add(g); self.db.commit(); self.db.refresh(g); return g

    def get_by_id(self, gid: int, user_id: str) -> LearnerGroup | None:
        return self.db.query(LearnerGroup).filter(LearnerGroup.id == gid, LearnerGroup.user_id == user_id).first()

    def get_all(self, user_id: str, limit: int = 200) -> list[LearnerGroup]:
        return self.db.query(LearnerGroup).filter(LearnerGroup.user_id == user_id).limit(limit).all()

    def update(self, gid: int, data: dict, user_id: str) -> LearnerGroup | None:
        g = self.get_by_id(gid, user_id)
        if not g: return None
        for k, v in data.items(): setattr(g, k, v)
        self.db.commit(); self.db.refresh(g); return g

    def delete(self, gid: int, user_id: str) -> bool:
        g = self.get_by_id(gid, user_id)
        if not g: return False
        from models.schedule import ScheduleSlot
        used = self.db.query(ScheduleSlot).filter(
            ScheduleSlot.learner_group_id == gid, ScheduleSlot.user_id == user_id,
            ScheduleSlot.status.in_(["draft","validated"])
        ).first()
        if used: raise ValueError("Group is used in an active planning.")
        self.db.delete(g); self.db.commit(); return True