"""
IGAD Hackathon 2026 — Demo Regional Scenario
==============================================
Scenario: "Operation Gati" — Cyclone DEMO-GATI approaching the Horn of Africa

This is a FICTIONAL scenario created for the IGAD Hackathon 2026 demonstration.
All shelter capacities, population figures, and resource quantities are fabricated
for demonstration purposes and do not represent real operational data.

Geographic context: The scenario is parameterised for the Puntland coast of Somalia
and surrounding IGAD-region districts, inspired by Cyclone Gati (November 2020) —
which made landfall near Bosaso as a Category 2 cyclone, the strongest ever recorded
on the Somali coast.

Coordinates reference real cities for geographic plausibility, but all
operational parameters (shelter capacity, resource stock, population zones)
are entirely fictional demo values.

NOTE: The validated research scenarios (Scenario A / B / C in scenarios.py)
are unchanged. This file is an additional config for the IGAD demo only.
"""

# ─── Cyclone Track ─────────────────────────────────────────────────────────────
# Track: Arabian Sea (south of Yemen) → Puntland coast (Bosaso region), Somalia
# Inspired by Cyclone Gati (2020), scaled to Cat 4 for dramatic demo effect

IGAD_CYCLONE = {
    "id": "igad_demo",
    "name": "DEMO-GATI",
    "description": "Arabian Sea rapid intensifier — Horn of Africa landfall",
    "start_cat": 2,
    "peak_cat": 4,
    "landfall_tick": 15,      # Landfall at tick 15 of 72 — gives agents early warning time
    "duration": 72,
    "avg_wind": 210.0,        # km/h sustained wind at peak (Cat 4 range)
    "avg_rain": 180.0,        # mm/hr at peak
    "avg_surge": 3.8,         # metres storm surge (Gati produced ~3m surge)
    # Arabian Sea origin — south of Yemen, east of Socotra
    "start_pos": {"lat": 13.2, "lon": 54.5},
    # Landfall near Bosaso/Bari region, Puntland, Somalia
    "landfall_pos": {"lat": 11.3, "lon": 49.8},
}

# ─── Population Zones (IGAD / Puntland / Somalia context) ────────────────────
# Fictional populations. Real population of Bosaso city is ~700k+, but we use
# scaled values suitable for the simulation engine's tick-based model.

IGAD_DISTRICT_CONFIG = {
    "total_pop": 950000,
    "zones": [
        {
            "id": "zone_bosaso_coast",
            "name": "Bosaso Coastal Zone",
            "population": 180000,
            "type": "Coastal",           # Highest evacuation urgency
            "description": "Port city and highest-risk coastal zone (Bari region)"
        },
        {
            "id": "zone_bosaso_urban",
            "name": "Bosaso Urban Centre",
            "population": 280000,
            "type": "Urban",
            "description": "Main urban population — commercial and residential"
        },
        {
            "id": "zone_qardho_inland",
            "name": "Qardho District (Inland)",
            "population": 200000,
            "type": "Suburban",
            "description": "Inland highland district — secondary evacuation route"
        },
        {
            "id": "zone_garowe_hub",
            "name": "Garowe Regional Hub",
            "population": 190000,
            "type": "SafeHaven",         # Receives evacuees from coastal zones
            "description": "Puntland capital — regional logistics and coordination hub"
        },
        {
            "id": "zone_galkayo_south",
            "name": "Galkayo Southern District",
            "population": 100000,
            "type": "Rural",
            "description": "Pastoral/rural communities with limited road access"
        },
    ]
}

# ─── Shelters ─────────────────────────────────────────────────────────────────
# Six shelters covering the affected region.
# Naming follows IGAD-region emergency management conventions (fictional).

IGAD_SHELTERS = [
    {
        "id": "sh-bos-01",
        "name": "Bosaso Port Relief Hub",
        "zone_id": "zone_bosaso_coast",
        "capacity": 8000,
        "current_occupancy": 0,
        "food_days": 5.0,
        "water_days": 4.0,
        "status": "OPERATIONAL",
        # Bosaso port area: 11.28°N, 49.18°E
        "location": {"lat": 11.28, "lon": 49.18},
    },
    {
        "id": "sh-bos-02",
        "name": "Bosaso Secondary School Hall",
        "zone_id": "zone_bosaso_urban",
        "capacity": 12000,
        "current_occupancy": 0,
        "food_days": 6.0,
        "water_days": 5.0,
        "status": "OPERATIONAL",
        # Bosaso city centre: 11.29°N, 49.20°E
        "location": {"lat": 11.29, "lon": 49.20},
    },
    {
        "id": "sh-qar-01",
        "name": "Qardho Community Centre",
        "zone_id": "zone_qardho_inland",
        "capacity": 6000,
        "current_occupancy": 0,
        "food_days": 7.0,
        "water_days": 6.0,
        "status": "OPERATIONAL",
        # Qardho town: 9.50°N, 49.08°E
        "location": {"lat": 9.50, "lon": 49.08},
    },
    {
        "id": "sh-gar-01",
        "name": "Garowe Regional EOC Shelter",
        "zone_id": "zone_garowe_hub",
        "capacity": 25000,
        "current_occupancy": 0,
        "food_days": 10.0,
        "water_days": 8.0,
        "status": "OPERATIONAL",
        # Garowe (Puntland capital): 8.41°N, 48.48°E
        "location": {"lat": 8.41, "lon": 48.48},
    },
    {
        "id": "sh-gar-02",
        "name": "Garowe UNHCR Transit Camp",
        "zone_id": "zone_garowe_hub",
        "capacity": 18000,
        "current_occupancy": 0,
        "food_days": 8.0,
        "water_days": 7.0,
        "status": "OPERATIONAL",
        # Garowe outskirts: 8.43°N, 48.51°E
        "location": {"lat": 8.43, "lon": 48.51},
    },
    {
        "id": "sh-gal-01",
        "name": "Galkayo Relief Camp Alpha",
        "zone_id": "zone_galkayo_south",
        "capacity": 15000,
        "current_occupancy": 0,
        "food_days": 9.0,
        "water_days": 7.0,
        "status": "OPERATIONAL",
        # Galkayo: 6.77°N, 47.43°E
        "location": {"lat": 6.77, "lon": 47.43},
    },
]

# ─── Resources (Depot inventories) ────────────────────────────────────────────
# Pre-positioned stocks at each shelter.
# Units: Water in Litres, Food in kg, Medical Kits in units, Fuel in L, Blankets in units.

IGAD_RESOURCES = [
    # Bosaso Port Hub
    {"id": "res-bos-w1", "type": "WATER",       "quantity": 80000,  "unit": "L",  "shelter_id": "sh-bos-01"},
    {"id": "res-bos-f1", "type": "FOOD",        "quantity": 40000,  "unit": "kg", "shelter_id": "sh-bos-01"},
    {"id": "res-bos-m1", "type": "MEDICAL_KIT", "quantity": 500,    "unit": "kit","shelter_id": "sh-bos-01"},
    # Bosaso School Hall
    {"id": "res-bos-w2", "type": "WATER",       "quantity": 120000, "unit": "L",  "shelter_id": "sh-bos-02"},
    {"id": "res-bos-f2", "type": "FOOD",        "quantity": 60000,  "unit": "kg", "shelter_id": "sh-bos-02"},
    {"id": "res-bos-b2", "type": "BLANKET",     "quantity": 5000,   "unit": "unit","shelter_id": "sh-bos-02"},
    # Qardho Community Centre
    {"id": "res-qar-w1", "type": "WATER",       "quantity": 60000,  "unit": "L",  "shelter_id": "sh-qar-01"},
    {"id": "res-qar-f1", "type": "FOOD",        "quantity": 30000,  "unit": "kg", "shelter_id": "sh-qar-01"},
    # Garowe EOC Shelter (main distribution hub)
    {"id": "res-gar-w1", "type": "WATER",       "quantity": 500000, "unit": "L",  "shelter_id": "sh-gar-01"},
    {"id": "res-gar-f1", "type": "FOOD",        "quantity": 250000, "unit": "kg", "shelter_id": "sh-gar-01"},
    {"id": "res-gar-fu", "type": "FUEL",        "quantity": 20000,  "unit": "L",  "shelter_id": "sh-gar-01"},
    {"id": "res-gar-m1", "type": "MEDICAL_KIT", "quantity": 2000,   "unit": "kit","shelter_id": "sh-gar-01"},
    # Garowe UNHCR Camp
    {"id": "res-gar-w2", "type": "WATER",       "quantity": 300000, "unit": "L",  "shelter_id": "sh-gar-02"},
    {"id": "res-gar-f2", "type": "FOOD",        "quantity": 150000, "unit": "kg", "shelter_id": "sh-gar-02"},
    {"id": "res-gar-b2", "type": "BLANKET",     "quantity": 12000,  "unit": "unit","shelter_id": "sh-gar-02"},
    # Galkayo Relief Camp
    {"id": "res-gal-w1", "type": "WATER",       "quantity": 200000, "unit": "L",  "shelter_id": "sh-gal-01"},
    {"id": "res-gal-f1", "type": "FOOD",        "quantity": 100000, "unit": "kg", "shelter_id": "sh-gal-01"},
    {"id": "res-gal-m1", "type": "MEDICAL_KIT", "quantity": 1000,   "unit": "kit","shelter_id": "sh-gal-01"},
]

# ─── Routes (road network) ────────────────────────────────────────────────────
# Key supply routes in the Puntland / Mudug road network.
# Distances are approximate real-world values.

IGAD_ROUTES = [
    {
        "id": "rt-bos-qar",
        "name": "Bosaso–Qardho Highway",
        "origin":      {"lat": 11.28, "lon": 49.18},  # Bosaso
        "destination": {"lat": 9.50,  "lon": 49.08},  # Qardho
        "distance_km": 185.0,
        "status": "CLEAR",
    },
    {
        "id": "rt-qar-gar",
        "name": "Qardho–Garowe Road",
        "origin":      {"lat": 9.50,  "lon": 49.08},  # Qardho
        "destination": {"lat": 8.41,  "lon": 48.48},  # Garowe
        "distance_km": 145.0,
        "status": "CLEAR",
    },
    {
        "id": "rt-gar-gal",
        "name": "Garowe–Galkayo Trunk Road",
        "origin":      {"lat": 8.41, "lon": 48.48},   # Garowe
        "destination": {"lat": 6.77, "lon": 47.43},   # Galkayo
        "distance_km": 250.0,
        "status": "CLEAR",
    },
    {
        "id": "rt-bos-coast",
        "name": "Coastal Evacuation Corridor",
        "origin":      {"lat": 11.29, "lon": 49.20},  # Bosaso urban
        "destination": {"lat": 11.28, "lon": 49.18},  # Bosaso port hub
        "distance_km": 3.5,
        "status": "CLEAR",
        # NOTE: This route is at high flood risk during storm surge —
        # InfraDT will block it at tick ~10 (5 ticks before landfall)
    },
]

# ─── Map Display Settings ─────────────────────────────────────────────────────
# Used by the frontend to position the Leaflet map on the IGAD region.

IGAD_MAP_CONFIG = {
    # Centre between cyclone origin and affected shelters — shows the full track
    "default_center": [10.0, 49.5],   # [lat, lon] — northern Puntland / Somalia
    "default_zoom": 6,                 # Wide enough to show cyclone track from Arabian Sea
    "region_label": "Horn of Africa — Puntland, Somalia (IGAD Demo Region)",
    "scenario_label": "Cyclone DEMO-GATI | IGAD Hackathon 2026 Demo Scenario",
}
