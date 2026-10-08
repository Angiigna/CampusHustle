from datetime import datetime
from flask import request
from flask_login import current_user
from flask_socketio import join_room, leave_room
from app import db, socketio
from app.models.models import Ride

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        # Join individual user room for private events (e.g., user_1)
        user_room = f"user_{current_user.id}"
        join_room(user_room)
        
        # Join role-based rooms
        if current_user.role == 'RIDER':
            join_room('riders')
        elif current_user.role == 'ADMIN':
            join_room('admin')
            
        print(f"[Socket.IO] Connected: User {current_user.name} ({current_user.role}) joined rooms: {user_room}")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        print(f"[Socket.IO] Disconnected: User {current_user.name}")


@socketio.on('join_ride_room')
def handle_join_ride_room(data):
    """Allows customer, assigned rider, or admin to subscribe to live updates for a specific ride."""
    if not current_user.is_authenticated:
        return

    ride_id = data.get('ride_id')
    if not ride_id:
        return

    ride = Ride.query.get(ride_id)
    if not ride:
        return

    # SECURITY AUTHORIZATION CHECK:
    # Only the customer of this ride, assigned rider, or admin can join the tracking room.
    is_authorized = (
        current_user.id == ride.customer_id or
        current_user.id == ride.rider_id or
        current_user.role == 'ADMIN'
    )

    if is_authorized:
        room_name = f"ride_{ride_id}"
        join_room(room_name)
        print(f"[Socket.IO] User {current_user.name} joined ride tracking room: {room_name}")


@socketio.on('rider_location_update')
def handle_rider_location_update(data):
    """
    CRITICAL SECURITY & LIVE TRACKING HANDLER
    Accepts GPS location updates ONLY from the authenticated assigned rider of an active ride.
    """
    if not current_user.is_authenticated or current_user.role != 'RIDER':
        return

    ride_id = data.get('ride_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    accuracy = data.get('accuracy', 0.0)

    if not ride_id or lat is None or lng is None:
        return

    ride = Ride.query.get(ride_id)
    if not ride:
        return

    # STRICT SECURITY VALIDATION:
    # 1. Ride MUST belong to the current authenticated rider
    # 2. Ride status MUST be active/trackable (ASSIGNED, ARRIVING, ACTIVE)
    if ride.rider_id != current_user.id or ride.status not in ['ASSIGNED', 'ARRIVING', 'ACTIVE']:
        print(f"[Socket.IO Security Alert] Unauthorized GPS update attempt for ride #{ride_id} by user #{current_user.id}")
        return

    # Store ONLY the latest known location in DB
    now = datetime.utcnow()
    ride.latest_latitude = float(lat)
    ride.latest_longitude = float(lng)
    ride.location_accuracy = float(accuracy) if accuracy else None
    ride.location_updated_at = now
    db.session.commit()

    update_payload = {
        'ride_id': ride_id,
        'latitude': float(lat),
        'longitude': float(lng),
        'accuracy': float(accuracy) if accuracy else None,
        'timestamp': now.isoformat(),
        'seconds_ago': 0
    }

    # Broadcast to customer in ride room and admin room
    socketio.emit('live_location_update', update_payload, to=f"ride_{ride_id}")
    socketio.emit('live_location_update', update_payload, to='admin')
