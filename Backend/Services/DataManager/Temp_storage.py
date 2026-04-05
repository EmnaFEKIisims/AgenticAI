"""
agents/data_manager/storage/temp_storage.py
============================================
In-memory temporary storage for uploaded data.

Stores data between upload and HITL validation.
Each entry has:
  - upload_id  : unique UUID
  - filename   : original file name
  - data       : list of raw dicts (extracted rows)
  - status     : "pending_review" | "corrected" | "approved" | "rejected"
"""

import uuid
from datetime import datetime


class TempStorage:
    """
    Simple in-memory key-value store.
    Resets when the server restarts.
    Replace with Redis or a temp DB table for production.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}

    def save(self, filename: str, data: list[dict]) -> str:
        """Saves a new entry and returns its upload_id."""
        upload_id = uuid.uuid4().hex
        self._store[upload_id] = {
            "upload_id":  upload_id,
            "filename":   filename,
            "data":       data,
            "status":     "pending_review",
            "created_at": datetime.utcnow().isoformat(),
        }
        return upload_id

    def get(self, upload_id: str) -> dict | None:
        """Returns the entry or None if not found."""
        return self._store.get(upload_id)

    def update_status(self, upload_id: str, status: str):
        """Updates the status of an entry."""
        if upload_id in self._store:
            self._store[upload_id]["status"] = status

    def update_data(self, upload_id: str, data: list[dict]):
        """Replaces the data of an entry (used after manual correction)."""
        if upload_id in self._store:
            self._store[upload_id]["data"] = data

    def delete(self, upload_id: str):
        """Removes an entry from storage."""
        self._store.pop(upload_id, None)

    def list_all(self) -> list[dict]:
        """Returns all entries (useful for admin/debug)."""
        return list(self._store.values())