"""
Unit Test Suite for CampusRide Fare Engine
Validates all user-provided validation examples and priority edge cases.
"""

import sys
import os
import pytest

# Add workspace directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.fare_service import calculate_fare, LOCATION_NAMES

VALIDATION_CASES = [
    ("KANNAGI", "SJ_AND_UMISARC", 30),
    ("SJ_AND_UMISARC", "KANNAGI", 30),
    ("MOTHER_THERESA", "SJ_AND_UMISARC", 30),
    ("SJ_AND_UMISARC", "MOTHER_THERESA", 30),
    ("KANNAGI", "GATE_1", 25),
    ("GATE_1", "KANNAGI", 25),
    ("CV_RAMAN", "SJ_AND_UMISARC", 25),
    ("SJ_AND_UMISARC", "CV_RAMAN", 25),
    ("CV_RAMAN", "GATE_2", 25),
    ("SJ_AND_UMISARC", "GATE_1", 30),
    ("GATE_1", "SJ_AND_UMISARC", 30),
    ("SJ_AND_UMISARC", "ADMIN_BLOCK", 30),
    ("SJ_AND_UMISARC", "LIBRARY_AND_READING_ROOM", 30),
    ("SJ_AND_UMISARC", "HEALTH_CENTRE", 30),
    ("SJ_AND_UMISARC", "LAW_DEPARTMENT", 30),
    ("SJ_AND_UMISARC", "SCIENCE_BLOCK", 30),
    ("SJ_AND_UMISARC", "GATE_2", 35),
    ("GATE_2", "SJ_AND_UMISARC", 35),
    ("SJ_AND_UMISARC", "PERFORMING_ARTS", 25),
    ("SJ_AND_UMISARC", "PONLAIT", 25),
    ("MEGA_MESS", "GATE_1", 25),
    ("MEGA_MESS", "SJ_AND_UMISARC", 25),
    ("MOTHER_THERESA", "GATE_2", 25),
    ("NARMADA", "RAJIV_GANDHI_STADIUM", 25),
    ("TAGORE", "HEALTH_CENTRE", 25),
]

@pytest.mark.parametrize("pickup,drop,expected_fare", VALIDATION_CASES)
def test_fare_validation_cases(pickup, drop, expected_fare):
    fare = calculate_fare(pickup, drop)
    assert fare == expected_fare, f"Expected fare({pickup} -> {drop}) to be ₹{expected_fare}, got ₹{fare}"

def test_symmetry():
    for pickup in LOCATION_NAMES.keys():
        for drop in LOCATION_NAMES.keys():
            assert calculate_fare(pickup, drop) == calculate_fare(drop, pickup), \
                f"Symmetry broken for {pickup} ↔ {drop}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
