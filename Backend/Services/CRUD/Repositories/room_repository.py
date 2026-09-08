#repositories/room_repository.py
from sqlalchemy.orm import Session
from models.room import Room

class RoomRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict, user_id: str) -> Room:
        room = Room(**data, user_id=user_id)
        self.db.add(room); self.db.commit(); self.db.refresh(room)
        return room

    def get_by_id(self, room_id: int, user_id: str) -> Room | None:
        return self.db.query(Room).filter(Room.id == room_id, Room.user_id == user_id).first()

    def get_all(self, user_id: str, limit: int = 200) -> list[Room]:
        return self.db.query(Room).filter(Room.user_id == user_id).limit(limit).all()

    def update(self, room_id: int, data: dict, user_id: str) -> Room | None:
        room = self.get_by_id(room_id, user_id)
        if not room: return None
        for k, v in data.items(): setattr(room, k, v)
        self.db.commit(); self.db.refresh(room)
        return room

    def delete(self, room_id: int, user_id: str) -> bool:
        room = self.get_by_id(room_id, user_id)
        if not room: return False
        from models.schedule import ScheduleSlot
        used = self.db.query(ScheduleSlot).filter(
            ScheduleSlot.room_id == room_id, ScheduleSlot.user_id == user_id,
            ScheduleSlot.status.in_(["draft","validated"])
        ).first()
        if used: raise ValueError("Room is used in an active planning.")
        self.db.delete(room); self.db.commit()
        return True