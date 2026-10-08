"""
Unit Tests for Papido REST API Endpoints
Tests /api/fare and ride creation APIs with authenticated test client.
"""

import pytest
from app import create_app, db
from app.models.models import User, RiderProfile, Location, Fare

@pytest.fixture
def authenticated_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            user = User(name="API Student", email="apistudent@campus.edu", phone="9988112233", role="CUSTOMER")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            # Log in
            client.post('/login', data={'email': 'apistudent@campus.edu', 'password': 'pass123'})
            yield client
            db.session.remove()
            db.drop_all()

def test_api_fare_calculation(authenticated_client):
    response = authenticated_client.get('/api/fare?pickup=KANNAGI&drop=SJ_AND_UMISARC')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['fare'] == 30.0

def test_api_fare_missing_params(authenticated_client):
    response = authenticated_client.get('/api/fare')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

def test_unauthenticated_api_fare(authenticated_client):
    authenticated_client.get('/logout')
    response = authenticated_client.get('/api/fare?pickup=KANNAGI&drop=SJ_AND_UMISARC')
    assert response.status_code == 302
