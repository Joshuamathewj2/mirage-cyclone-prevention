SCENARIO_A = {
    "id": "scenario_A",
    "name": "The Sprint",
    "description": "Rapid Intensification",
    "start_cat": 2,
    "peak_cat": 5,
    "landfall_tick": 12,
    "duration": 72,
    "avg_wind": 220.0,
    "avg_rain": 100.0,
    "avg_surge": 4.5,
    "start_pos": {"lat": 18.0, "lon": 85.0},
    "landfall_pos": {"lat": 19.5, "lon": 84.0}
}

SCENARIO_B = {
    "id": "scenario_B",
    "name": "The Slow Burn",
    "description": "Prolonged Category 3",
    "start_cat": 1,
    "peak_cat": 3,
    "landfall_tick": 24,
    "duration": 72,
    "avg_wind": 180.0,
    "avg_rain": 300.0,
    "avg_surge": 3.0,
    "start_pos": {"lat": 17.0, "lon": 86.0},
    "landfall_pos": {"lat": 19.5, "lon": 84.0}
}

SCENARIO_C = {
    "id": "scenario_C",
    "name": "Coast Buster",
    "description": "Category 5 Direct Hit",
    "start_cat": 3,
    "peak_cat": 5,
    "landfall_tick": 6,
    "duration": 48,
    "avg_wind": 260.0,
    "avg_rain": 100.0,
    "avg_surge": 6.0,
    "start_pos": {"lat": 19.0, "lon": 85.0},
    "landfall_pos": {"lat": 19.5, "lon": 84.0}
}

DISTRICT_CONFIG = {
    "total_pop": 1000000,
    "zones": [
        {"id": "zone_01", "population": 200000, "type": "Coastal"},
        {"id": "zone_02", "population": 300000, "type": "Urban"},
        {"id": "zone_03", "population": 250000, "type": "Suburban"},
        {"id": "zone_04", "population": 150000, "type": "Rural"},
        {"id": "zone_05", "population": 100000, "type": "SafeHaven"}
    ]
}

# Initial Data (Sample)
INITIAL_SHELTERS = [
    {"id": "sh-01", "name": "Coastal Haven", "capacity": 10000, "zone_id": "zone_01", "location": {"lat": 19.4, "lon": 84.1}, "status": "OPERATIONAL"},
    {"id": "sh-02", "name": "City Center", "capacity": 40000, "zone_id": "zone_02", "location": {"lat": 19.6, "lon": 84.3}, "status": "OPERATIONAL"},
]

INITIAL_RESOURCES = [
    {"id": "res-01", "type": "WATER", "quantity": 100000, "unit": "L", "shelter_id": "sh-01"},
    {"id": "res-02", "type": "FOOD", "quantity": 50000, "unit": "kg", "shelter_id": "sh-01"},
    {"id": "res-03", "type": "WATER", "quantity": 500000, "unit": "L", "shelter_id": "sh-02"},
    {"id": "res-04", "type": "FOOD", "quantity": 250000, "unit": "kg", "shelter_id": "sh-02"},
]

INITIAL_ROUTES = [
    {"id": "rt-01", "origin": {"lat": 19.0, "lon": 85.0}, "destination": {"lat": 19.4, "lon": 84.1}, "distance_km": 50.0, "status": "CLEAR"},
]
