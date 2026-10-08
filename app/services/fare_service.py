"""
CampusRide Centralized Fare Engine & Location Registry
Authoritative fare calculation logic based on campus rules and priority tiers.
"""

# Location Code to Human-Readable Name Map
LOCATION_NAMES = {
    # Girls' Hostels
    "KANNAGI": "Kannagi",
    "SAVITRIBAI_PHULE": "Savitribai Phule",
    "NARMADA": "Narmada",
    "KALPANA_CHAWLA": "Kalpana Chawla",
    "MADAM_CURIE": "Madam Curie",
    "YAMUNA": "Yamuna",
    "GANGA": "Ganga",
    "SARASWATHI": "Saraswathi",
    "CAUVERY": "Cauvery",
    # Boys' Hostels
    "CV_RAMAN": "CV Raman",
    "BHARATHIDASAN": "Bharathidasan",
    "SUBRAMANIA_BHARATHI": "Subramania Bharathi",
    "KALIDAS": "Kalidas",
    "AUROBINDO": "Aurobindo",
    "MAKA": "MAKA",
    "VALMIKI": "Valmiki",
    "BIRSA_MUNDA": "Birsa Munda",
    "ILLANGO_ADIGAL": "Illango Adigal",
    "TAGORE": "Tagore",
    "KABIRDAS": "Kabirdas",
    "KAMBAN": "Kamban",
    "KANNADASAN": "Kannadasan",
    "SRK": "SRK",
    # Mess
    "MOTHER_THERESA": "Mother Theresa",
    "AMUDHAM": "Amudham",
    "MEGA_MESS": "Mega Mess",
    # Academic Areas
    "SOM": "SOM",
    "SJ_AND_UMISARC": "SJ & UMISARC",
    "SCIENCE_BLOCK": "Science Block",
    "LAW_DEPARTMENT": "Law Department",
    "PERFORMING_ARTS": "Performing Arts",
    # Other Areas
    "PONLAIT": "Ponlait",
    "GATE_1": "Gate 1",
    "GATE_2": "Gate 2",
    "ADMIN_BLOCK": "Admin Block",
    "LIBRARY_AND_READING_ROOM": "Library & Reading Room",
    "HEALTH_CENTRE": "Health Centre",
    "THIRUVALLUR_STADIUM": "Thiruvallur Stadium",
    "RAJIV_GANDHI_STADIUM": "Rajiv Gandhi Stadium",
}

# Location Group Classifications
GIRLS_HOSTEL = {
    "KANNAGI",
    "SAVITRIBAI_PHULE",
    "NARMADA",
    "KALPANA_CHAWLA",
    "MADAM_CURIE",
    "YAMUNA",
    "GANGA",
    "SARASWATHI",
    "CAUVERY",
}

BOYS_HOSTEL = {
    "CV_RAMAN",
    "BHARATHIDASAN",
    "SUBRAMANIA_BHARATHI",
    "KALIDAS",
    "AUROBINDO",
    "MAKA",
    "VALMIKI",
    "BIRSA_MUNDA",
    "ILLANGO_ADIGAL",
    "TAGORE",
    "KABIRDAS",
    "KAMBAN",
    "KANNADASAN",
    "SRK",
}

GIRLS_MESS = {"MOTHER_THERESA"}
BOYS_MESS = {"AMUDHAM"}
SJ_UMISARC = {"SJ_AND_UMISARC"}

# Structured UI Location Categories for Customer Dropdowns
LOCATION_CATEGORIES = [
    {
        "category": "Girls' Hostels",
        "locations": [{"code": code, "name": LOCATION_NAMES[code]} for code in sorted(GIRLS_HOSTEL)]
    },
    {
        "category": "Boys' Hostels",
        "locations": [{"code": code, "name": LOCATION_NAMES[code]} for code in sorted(BOYS_HOSTEL)]
    },
    {
        "category": "Mess & Dining",
        "locations": [
            {"code": "MOTHER_THERESA", "name": "Mother Theresa (Girls Mess)"},
            {"code": "AMUDHAM", "name": "Amudham (Boys Mess)"},
            {"code": "MEGA_MESS", "name": "Mega Mess"}
        ]
    },
    {
        "category": "Academic Blocks",
        "locations": [
            {"code": "SJ_AND_UMISARC", "name": LOCATION_NAMES["SJ_AND_UMISARC"]},
            {"code": "SCIENCE_BLOCK", "name": LOCATION_NAMES["SCIENCE_BLOCK"]},
            {"code": "LAW_DEPARTMENT", "name": LOCATION_NAMES["LAW_DEPARTMENT"]},
            {"code": "SOM", "name": LOCATION_NAMES["SOM"]},
            {"code": "PERFORMING_ARTS", "name": LOCATION_NAMES["PERFORMING_ARTS"]}
        ]
    },
    {
        "category": "Campus Gates & Facilities",
        "locations": [
            {"code": "GATE_1", "name": LOCATION_NAMES["GATE_1"]},
            {"code": "GATE_2", "name": LOCATION_NAMES["GATE_2"]},
            {"code": "ADMIN_BLOCK", "name": LOCATION_NAMES["ADMIN_BLOCK"]},
            {"code": "LIBRARY_AND_READING_ROOM", "name": LOCATION_NAMES["LIBRARY_AND_READING_ROOM"]},
            {"code": "HEALTH_CENTRE", "name": LOCATION_NAMES["HEALTH_CENTRE"]},
            {"code": "PONLAIT", "name": LOCATION_NAMES["PONLAIT"]},
            {"code": "THIRUVALLUR_STADIUM", "name": LOCATION_NAMES["THIRUVALLUR_STADIUM"]},
            {"code": "RAJIV_GANDHI_STADIUM", "name": LOCATION_NAMES["RAJIV_GANDHI_STADIUM"]}
        ]
    }
]


def is_in_group(code: str, group: set) -> bool:
    """Helper to check if a location code belongs to a group."""
    return code in group


def calculate_fare(pickup_code: str, drop_code: str) -> int:
    """
    Calculates the exact fare between two campus locations based on prioritized rules.
    Symmetric rule enforcement: fare(A, B) == fare(B, A)
    """
    p = pickup_code.upper().strip()
    d = drop_code.upper().strip()

    # Rule Helper for Bidirectional Matching
    def match(cond1: bool, cond2: bool) -> bool:
        return (cond1 and cond2)

    def route_contains(loc_or_group1, loc_or_group2) -> bool:
        def check_endpoint(loc_set, endpoint):
            if isinstance(loc_set, str):
                return endpoint == loc_set
            return endpoint in loc_set

        return (
            (check_endpoint(loc_or_group1, p) and check_endpoint(loc_or_group2, d)) or
            (check_endpoint(loc_or_group2, p) and check_endpoint(loc_or_group1, d))
        )

    # 1. SJ_AND_UMISARC ↔ GATE_2 => ₹35
    if route_contains("SJ_AND_UMISARC", "GATE_2"):
        return 35

    # 2. GIRLS_HOSTEL / GIRLS_MESS ↔ SJ_AND_UMISARC => ₹30
    if route_contains(GIRLS_HOSTEL | GIRLS_MESS, "SJ_AND_UMISARC"):
        return 30

    # 3. SJ_AND_UMISARC ↔ GATE_1 => ₹30
    if route_contains("SJ_AND_UMISARC", "GATE_1"):
        return 30

    # 4. SJ_AND_UMISARC ↔ ADMIN_BLOCK => ₹30
    if route_contains("SJ_AND_UMISARC", "ADMIN_BLOCK"):
        return 30

    # 5. SJ_AND_UMISARC ↔ LIBRARY_AND_READING_ROOM => ₹30
    if route_contains("SJ_AND_UMISARC", "LIBRARY_AND_READING_ROOM"):
        return 30

    # 6. SJ_AND_UMISARC ↔ HEALTH_CENTRE => ₹30
    if route_contains("SJ_AND_UMISARC", "HEALTH_CENTRE"):
        return 30

    # 7. SJ_AND_UMISARC ↔ LAW_DEPARTMENT => ₹30
    if route_contains("SJ_AND_UMISARC", "LAW_DEPARTMENT"):
        return 30

    # 8. SJ_AND_UMISARC ↔ SCIENCE_BLOCK => ₹30
    if route_contains("SJ_AND_UMISARC", "SCIENCE_BLOCK"):
        return 30

    # 9. BOYS_HOSTEL / BOYS_MESS ↔ ANYWHERE => ₹25
    if p in (BOYS_HOSTEL | BOYS_MESS) or d in (BOYS_HOSTEL | BOYS_MESS):
        return 25

    # 10. GIRLS_HOSTEL / GIRLS_MESS ↔ ANYWHERE ELSE => ₹25
    if p in (GIRLS_HOSTEL | GIRLS_MESS) or d in (GIRLS_HOSTEL | GIRLS_MESS):
        return 25

    # 11. ALL REMAINING COMBINATIONS => ₹25
    return 25


def get_location_name(code: str) -> str:
    """Returns the human-readable display name for a location code."""
    return LOCATION_NAMES.get(code.upper().strip(), code)
