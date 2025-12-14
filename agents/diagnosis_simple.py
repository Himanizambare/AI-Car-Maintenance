# agents/diagnosis_simple.py
"""Tiny diagnosis function (keeps your earlier logic)"""

def diagnose_brake_sensor(sensor_mm: float):
    """
    Returns None or a short issue string based on brake pad thickness in mm.
    (your demo logic: <3mm -> issue)
    """
    if sensor_mm < 3.0:
        return "Brake Pad Wear"
    return None
