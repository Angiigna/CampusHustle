"""
Unit Tests for Papido Application Routes & Access Controls
"""

import pytest
from app import create_app, db
from app.models.models import User

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

def test_unauthenticated_redirect(client):
    response = client.get('/customer')
    assert response.status_code == 302
    assert '/login' in response.location

def test_admin_route_protection(client):
    response = client.get('/admin')
    assert response.status_code == 302
    assert '/login' in response.location
