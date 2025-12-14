# agents/integrator.py
from services.db_manager import DatabaseManager
from agents.voice_agent import VoiceAI_Agent
from agents.diagnosis_simple import diagnose_brake_sensor
from agents.scheduler_agent import SchedulingAgent

class SimpleOrchestrator:
    def __init__(self, db_file: str = "vehicle_database.json"):
        self.db = DatabaseManager(db_file)
        self.voice = VoiceAI_Agent()
        self.scheduler = SchedulingAgent(self.db)

    def process_brake_event(self, vehicle_id: str, brake_sensor_mm: float, city: str = "Unknown"):
        """
        1) Diagnose
        2) If issue -> call owner using voice agent (interactive)
        3) If owner accepts -> book service and persist
        Returns a dict with the flow result.
        """
        vehicle = self.db.get_vehicle(vehicle_id)
        if not vehicle:
            return {"error": "vehicle_not_found", "vehicle_id": vehicle_id}

        issue = diagnose_brake_sensor(brake_sensor_mm)
        flow = {"vehicle_id": vehicle_id, "owner": vehicle.get("owner"), "issue": issue}

        if not issue:
            flow["status"] = "no_issue"
            return flow

        # ask owner
        owner = vehicle.get("owner", "Owner")
        response = self.voice.make_call(owner, issue)
        flow["owner_response"] = response

        if response and ("yes" in response or response.strip().lower().startswith("y")):
            booking = self.scheduler.book_service(vehicle_id, issue, city=city)
            flow["booking"] = booking
            flow["status"] = "booked"
        else:
            flow["status"] = "declined"

        return flow
