from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

from typing import Dict, Any, Optional

class User(UserMixin, db.Model):
    """User account model for Customers, Riders, and Admins."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='CUSTOMER', index=True) # CUSTOMER, RIDER, ADMIN
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rider_profile = db.relationship('RiderProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    rides_as_customer = db.relationship('Ride', foreign_keys='Ride.customer_id', backref='customer', lazy='dynamic')
    rides_as_rider = db.relationship('Ride', foreign_keys='Ride.rider_id', backref='rider', lazy='dynamic')

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password hash against input password."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize User object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'role': self.role
        }

@login_manager.user_loader
def load_user(user_id: str) -> Optional['User']:
    """Flask-Login user loader callback."""
    return User.query.get(int(user_id))


class RiderProfile(db.Model):
    """Profile extension for Partner Riders with availability & approval status."""
    __tablename__ = 'rider_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(50), nullable=False, default='Motorbike')
    vehicle_number = db.Column(db.String(30), nullable=True)
    is_available = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_approved = db.Column(db.Boolean, default=True, nullable=False, index=True) # Requires Admin Approval
    rating = db.Column(db.Float, default=5.0)
    total_rides = db.Column(db.Integer, default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize RiderProfile to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.name if self.user else '',
            'phone': self.user.phone if self.user else '',
            'email': self.user.email if self.user else '',
            'vehicle_type': self.vehicle_type,
            'vehicle_number': self.vehicle_number or 'N/A',
            'is_available': self.is_available,
            'is_approved': self.is_approved,
            'rating': round(self.rating, 1),
            'total_rides': self.total_rides
        }


class Location(db.Model):
    """Campus geographic location node model."""
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    active = db.Column(db.Boolean, default=True, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Location to dictionary."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'active': self.active
        }


class Fare(db.Model):
    """Bidirectional fixed fare lookup table."""
    __tablename__ = 'fares'

    id = db.Column(db.Integer, primary_key=True)
    pickup_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    drop_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)


class Ride(db.Model):
    """Core Ride lifecycle & real-time dispatch state machine model."""
    __tablename__ = 'rides'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    pickup_code = db.Column(db.String(50), nullable=False)
    pickup_name = db.Column(db.String(100), nullable=False)
    drop_code = db.Column(db.String(50), nullable=False)
    drop_name = db.Column(db.String(100), nullable=False)
    fare = db.Column(db.Float, nullable=False)
    otp = db.Column(db.String(4), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='DISPATCHING', index=True) 
    # Valid statuses: REQUESTED, DISPATCHING, ASSIGNED, ARRIVING, ACTIVE, COMPLETED, CANCELLED, EXPIRED
    cancellation_reason = db.Column(db.String(255), nullable=True)
    
    # Real-time Live Tracking fields (stores only latest known coordinates)
    latest_latitude = db.Column(db.Float, nullable=True)
    latest_longitude = db.Column(db.Float, nullable=True)
    location_accuracy = db.Column(db.Float, nullable=True)
    location_updated_at = db.Column(db.DateTime, nullable=True)

    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    rating_entry = db.relationship('Rating', backref='ride', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        pickup_loc = Location.query.filter_by(code=self.pickup_code).first()
        drop_loc = Location.query.filter_by(code=self.drop_code).first()

        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else 'Student',
            'customer_phone': self.customer.phone if self.customer else '',
            'rider_id': self.rider_id,
            'rider_name': self.rider.name if self.rider else None,
            'rider_phone': self.rider.phone if self.rider else None,
            'vehicle_info': f"{self.rider.rider_profile.vehicle_type} ({self.rider.rider_profile.vehicle_number})" if (self.rider and self.rider.rider_profile) else 'Bike Taxi',
            'pickup_code': self.pickup_code,
            'pickup_name': self.pickup_name,
            'pickup_lat': pickup_loc.latitude if pickup_loc else None,
            'pickup_lng': pickup_loc.longitude if pickup_loc else None,
            'drop_code': self.drop_code,
            'drop_name': self.drop_name,
            'drop_lat': drop_loc.latitude if drop_loc else None,
            'drop_lng': drop_loc.longitude if drop_loc else None,
            'fare': int(self.fare),
            'otp': self.otp if self.status in ['ASSIGNED', 'ARRIVING'] else None,
            'status': self.status,
            'cancellation_reason': self.cancellation_reason,
            'latest_latitude': self.latest_latitude,
            'latest_longitude': self.latest_longitude,
            'location_accuracy': self.location_accuracy,
            'location_updated_at': self.location_updated_at.isoformat() if self.location_updated_at else None,
            'location_updated_seconds_ago': int((datetime.utcnow() - self.location_updated_at).total_seconds()) if self.location_updated_at else None,
            'requested_at': self.requested_at.strftime('%H:%M:%S') if self.requested_at else '',
            'assigned_at': self.assigned_at.strftime('%H:%M:%S') if self.assigned_at else '',
            'started_at': self.started_at.strftime('%H:%M:%S') if self.started_at else '',
            'completed_at': self.completed_at.strftime('%H:%M:%S') if self.completed_at else '',
            'rating': self.rating_entry.rating if self.rating_entry else None
        }


class Rating(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
