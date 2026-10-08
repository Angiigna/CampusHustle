"""
Unit Tests for Papido Database Models
Tests User, RiderProfile, Location, Fare, and Ride serialization and operations.
"""

import pytest
from app import create_app, db
from app.models.models import User, RiderProfile, Location, Fare, Ride

@pytest.fixture
def app_context():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_user_password_hashing(app_context):
    user = User(name="Test Student", email="student@campus.edu", phone="9988776655", role="CUSTOMER")
    user.set_password("secret123")
    assert user.check_password("secret123") is True
    assert user.check_password("wrongpass") is False

def test_user_to_dict(app_context):
    user = User(name="Test Student", email="student@campus.edu", phone="9988776655", role="CUSTOMER")
    user.set_password("secret123")
    db.session.add(user)
    db.session.commit()
    data = user.to_dict()
    assert data['name'] == "Test Student"
    assert data['email'] == "student@campus.edu"
    assert data['role'] == "CUSTOMER"

def test_rider_profile_creation(app_context):
    user = User(name="Test Rider", email="rider@campus.edu", phone="9988776654", role="RIDER")
    user.set_password("secret123")
    db.session.add(user)
    db.session.commit()

    profile = RiderProfile(
        user_id=user.id,
        vehicle_type="Scooter",
        vehicle_number="TS09 AB 1234",
        is_available=True,
        is_approved=False
    )
    db.session.add(profile)
    db.session.commit()

    assert profile.user_id == user.id
    assert profile.is_approved is False
    data = profile.to_dict()
    assert data['vehicle_type'] == "Scooter"
    assert data['vehicle_number'] == "TS09 AB 1234"

def test_location_and_fare_models(app_context):
    loc1 = Location(code="TEST_GATE_1", name="Main Gate 1", category="Gates", latitude=12.0280, longitude=79.8550)
    loc2 = Location(code="TEST_ADMIN_BLOCK", name="Admin Block", category="Academic", latitude=12.0250, longitude=79.8560)
    db.session.add_all([loc1, loc2])
    db.session.commit()

    fare = Fare(pickup_location_id=loc1.id, drop_location_id=loc2.id, amount=25.0)
    db.session.add(fare)
    db.session.commit()

    assert fare.amount == 25.0
    assert loc1.to_dict()['code'] == "TEST_GATE_1"
