# services/db_manager.py
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_DB = {
    "MH-01-AB-1234": {
        "owner": "Mr. Sharma",
        "phone": "555-0199",
        "model": "XUV700",
        "status": "Healthy",
        "history": []
    },
    "DL-04-XY-9999": {
        "owner": "Ms. Priya",
        "phone": "555-2342",
        "model": "Thar",
        "status": "Healthy",
        "history": []
    }
}

class DatabaseManager:
    def __init__(self, db_file: str = "vehicle_database.json"):
        self.db_file = Path(db_file)
        self._ensure_db()

    def _ensure_db(self):
        if self.db_file.exists():
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                # if corrupted, create default
                self.data = DEFAULT_DB.copy()
                self.save()
        else:
            # create default file
            self.data = DEFAULT_DB.copy()
            self.save()

    def save(self):
        tmp = self.db_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.db_file)

    def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        return self.data.get(vehicle_id)

    def list_vehicles(self):
        return list(self.data.keys())

    def update_vehicle_history(self, vehicle_id: str, issue: str, action: str):
        if vehicle_id not in self.data:
            # create minimal record if unknown
            self.data[vehicle_id] = {
                "owner": "Unknown",
                "phone": "",
                "model": "",
                "status": "Unknown",
                "history": []
            }
        entry = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issue": issue,
            "action": action
        }
        self.data[vehicle_id]["history"].append(entry)
        self.data[vehicle_id]["status"] = action if action else self.data[vehicle_id].get("status", "Updated")
        self.save()

    def set_status(self, vehicle_id: str, status: str):
        if vehicle_id in self.data:
            self.data[vehicle_id]["status"] = status
            self.save()
