# repositories/equipment_repository.py
from sqlalchemy.orm import Session
from models.equipment import Equipment

class EquipmentRepository:
    def __init__(self, db: Session): self.db = db

    def create(self, data: dict, user_id: str) -> Equipment:
        eq = Equipment(**data, user_id=user_id)
        self.db.add(eq); self.db.commit(); self.db.refresh(eq); return eq

    def get_by_id(self, eid: int, user_id: str) -> Equipment | None:
        return self.db.query(Equipment).filter(Equipment.id == eid, Equipment.user_id == user_id).first()

    def get_all(self, user_id: str, limit: int = 200) -> list[Equipment]:
        return self.db.query(Equipment).filter(Equipment.user_id == user_id).limit(limit).all()

    def update(self, eid: int, data: dict, user_id: str) -> Equipment | None:
        eq = self.get_by_id(eid, user_id)
        if not eq: return None
        for k, v in data.items(): setattr(eq, k, v)
        self.db.commit(); self.db.refresh(eq); return eq

    def delete(self, eid: int, user_id: str) -> bool:
        eq = self.get_by_id(eid, user_id)
        if not eq: return False
        self.db.delete(eq); self.db.commit(); return True