# repositories/trainer_repository.py
from sqlalchemy.orm import Session
from models.trainer import Trainer

class TrainerRepository:
    def __init__(self, db: Session): self.db = db

    def create(self, data: dict, user_id: str) -> Trainer:
        t = Trainer(**data, user_id=user_id)
        self.db.add(t); self.db.commit(); self.db.refresh(t); return t

    def get_by_id(self, tid: int, user_id: str) -> Trainer | None:
        return self.db.query(Trainer).filter(Trainer.id == tid, Trainer.user_id == user_id).first()

    def get_by_email(self, email: str, user_id: str) -> Trainer | None:
        return self.db.query(Trainer).filter(Trainer.email == email, Trainer.user_id == user_id).first()

    def get_all(self, user_id: str, limit: int = 200) -> list[Trainer]:
        return self.db.query(Trainer).filter(Trainer.user_id == user_id).limit(limit).all()

    def update(self, tid: int, data: dict, user_id: str) -> Trainer | None:
        t = self.get_by_id(tid, user_id)
        if not t: return None
        for k, v in data.items(): setattr(t, k, v)
        self.db.commit(); self.db.refresh(t); return t

    def delete(self, tid: int, user_id: str) -> bool:
        t = self.get_by_id(tid, user_id)
        if not t: return False
        from models.schedule import ScheduleSlot
        used = self.db.query(ScheduleSlot).filter(
            ScheduleSlot.trainer_id == tid, ScheduleSlot.user_id == user_id,
            ScheduleSlot.status.in_(["draft","validated"])
        ).first()
        if used: raise ValueError("Trainer is used in an active planning.")
        self.db.delete(t); self.db.commit(); return True