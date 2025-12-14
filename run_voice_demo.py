# run_voice_demo.py
from agents.integrator import SimpleOrchestrator

if __name__ == "__main__":
    orch = SimpleOrchestrator(db_file="vehicle_database.json")
    vehicle = "MH-01-AB-1234"
    brake_sensor = 2.5
    print("Running demo (this will ask you on console)...")
    result = orch.process_brake_event(vehicle, brake_sensor, city="Mumbai")
    print("Flow result:", result)
