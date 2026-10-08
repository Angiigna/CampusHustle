"""
Unit Tests for Papido Authentication Routes
Tests login, customer registration, rider registration, and authorization checks.
"""

import pytest
from app import create_app, db
from app.models.models import User, RiderProfile

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Papido' in response.data

def test_customer_registration_flow(client):
    response = client.post('/register/customer', data={
        'name': 'Priya Sharma',
        'email': 'priya@campus.edu',
        'phone': '9876543210',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    user = User.query.filter_by(email='priya@campus.edu').first()
    assert user is not None
    assert user.role == 'CUSTOMER'

def test_rider_registration_flow(client):
    response = client.post('/register/rider', data={
        'name': 'Vikram Singh',
        'email': 'vikram@campus.edu',
        'phone': '9876543211',
        'password': 'password123',
        'vehicle_type': 'Motorbike',
        'vehicle_number': 'AP09 AB 1234'
    }, follow_redirects=True)
    assert response.status_code == 200
    user = User.query.filter_by(email='vikram@campus.edu').first()
    assert user is not None
    assert user.role == 'RIDER'
    profile = RiderProfile.query.filter_by(user_id=user.id).first()
    assert profile is not None
    assert profile.is_approved is False

def test_duplicate_email_prevention(client):
    # First registration
    client.post('/register/customer', data={
        'name': 'Student One',
        'email': 'duplicate@campus.edu',
        'phone': '9876500001',
        'password': 'password123'
    }, follow_redirects=True)
    # Logout to clear session
    client.get('/logout')
    # Duplicate registration
    response = client.post('/register/customer', data={
        'name': 'Student Two',
        'email': 'duplicate@campus.edu',
        'phone': '9876500002',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'already exists' in response.data
