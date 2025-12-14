# agents/scheduler_agent.py
import time
from typing import Dict
from services.db_manager import DatabaseManager

class SchedulingAgent:
    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()

    def _find_earliest_slot(self, city: str):
        # Minimal deterministic slot logic for demo
        t = time.localtime()
        # build a friendly string
        slot = time.strftime("%a %d %b - 10:00 AM", t)
        return slot

    def book_service(self, vehicle_id: str, issue: str, city: str = "Unknown"):
        slot = self._find_earliest_slot(city)
        action = f"Scheduled Service ({slot})"
        self.db.update_vehicle_history(vehicle_id, issue, action)
        return {"status": "booked", "slot": slot, "vehicle_id": vehicle_id}
