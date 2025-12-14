def build_synthetic_vehicles(n=20):
    """
    Build up to 20 synthetic vehicles mixing Hero / Mahindra / Tata / Hyundai / Kia / Maruti / Honda /
    TVS / Bajaj / Royal Enfield / Toyota / MG.
    """

    base_year = datetime.now().year

    all_vehicles = [
        # ---- Hero (2W) ----
        ("Hero", "Splendor Plus", "2W"),
        ("Hero", "Glamour", "2W"),
        ("Hero", "Xtreme 160R", "2W"),
        ("Hero", "Xpulse 200", "2W"),

        # ---- Mahindra (4W) ----
        ("Mahindra", "XUV700", "4W"),
        ("Mahindra", "Scorpio N", "4W"),
        ("Mahindra", "Thar", "4W"),
        ("Mahindra", "Bolero Neo", "4W"),

        # ---- Tata (4W) ----
        ("Tata", "Harrier", "4W"),
        ("Tata", "Safari", "4W"),

        # ---- Hyundai (4W) ----
        ("Hyundai", "Creta", "4W"),
        ("Hyundai", "Venue", "4W"),

        # ---- Kia (4W) ----
        ("Kia", "Seltos", "4W"),
        ("Kia", "Sonet", "4W"),

        # ---- Maruti (4W) ----
        ("Maruti", "Swift", "4W"),
        ("Maruti", "Baleno", "4W"),

        # ---- Honda (4W + 2W) ----
        ("Honda", "City", "4W"),
        ("Honda", "CB Shine", "2W"),

        # ---- Others ----
        ("Royal Enfield", "Classic 350", "2W"),
        ("Bajaj", "Pulsar 150", "2W"),
        ("TVS", "Apache RTR 160", "2W"),
        ("MG", "ZS EV", "4W"),
        ("Toyota", "Innova Crysta", "4W")
    ]

    # Ensure n does not exceed 20
    n = min(n, len(all_vehicles))

    # Random selection of vehicle list
    selected = random.sample(all_vehicles, n)

    cities = [
        "Mumbai", "Pune", "Delhi", "Nagpur", "Bengaluru", "Chennai", "Jaipur",
        "Lucknow", "Hyderabad", "Indore", "Surat", "Ranchi", "Chandigarh",
        "Ahmedabad", "Kolkata"
    ]

    vehicles = []
    for i, (make, model, seg) in enumerate(selected, start=1):
        vehicles.append({
            "id": f"V{str(i).zfill(4)}",
            "make": make,
            "model": model,
            "year": base_year - random.randint(0, 10),
            "city": random.choice(cities),
            "segment": seg,
            "avg_km_per_day": random.randint(20, 100)
        })

    return pd.DataFrame(vehicles)
