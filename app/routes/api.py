import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text
from app import db, socketio
from app.models.models import Ride, RiderProfile, Rating, Location, User
from app.services.fare_service import calculate_fare, get_location_name

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/fare', methods=['GET'])
@login_required
def get_fare():
    pickup = request.args.get('pickup', '').strip()
    drop = request.args.get('drop', '').strip()

    if not pickup or not drop:
        return jsonify({'success': False, 'message': 'Pickup and drop locations required.'}), 400

    fare = calculate_fare(pickup, drop)
    return jsonify({
        'success': True,
        'fare': fare,
        'pickup_code': pickup,
        'pickup_name': get_location_name(pickup),
        'drop_code': drop,
        'drop_name': get_location_name(drop)
    })


@api_bp.route('/rides', methods=['POST'])
@login_required
def create_ride():
    """Customer requests a new ride."""
    data = request.get_json() or {}
    pickup_code = data.get('pickup_code', '').strip()
    drop_code = data.get('drop_code', '').strip()

    if not pickup_code or not drop_code:
        return jsonify({'success': False, 'message': 'Pickup and drop locations required.'}), 400

    if pickup_code == drop_code:
        return jsonify({'success': False, 'message': 'Pickup and drop locations cannot be the same.'}), 400

    # Prevent duplicate active rides for same customer
    existing_ride = Ride.query.filter(
        Ride.customer_id == current_user.id,
        Ride.status.in_(['DISPATCHING', 'ASSIGNED', 'ARRIVING', 'ACTIVE'])
    ).first()

    if existing_ride:
        return jsonify({'success': False, 'message': 'You already have an active ride in progress.'}), 400

    fare_amount = calculate_fare(pickup_code, drop_code)
    pickup_name = get_location_name(pickup_code)
    drop_name = get_location_name(drop_code)

    ride = Ride(
        customer_id=current_user.id,
        pickup_code=pickup_code,
        pickup_name=pickup_name,
        drop_code=drop_code,
        drop_name=drop_name,
        fare=fare_amount,
        status='DISPATCHING',
        requested_at=datetime.utcnow()
    )

    db.session.add(ride)
    db.session.commit()

    ride_dict = ride.to_dict()

    # Real-Time Broadcasts
    socketio.emit('new_ride_request', ride_dict, to='riders')
    socketio.emit('dashboard_update', {'event': 'ride_created', 'ride': ride_dict}, to='admin')

    return jsonify({'success': True, 'ride': ride_dict}), 201


@api_bp.route('/rides/<int:ride_id>/accept', methods=['POST'])
@login_required
def accept_ride(ride_id):
    """
    CRITICAL ATOMIC CONCURRENCY CLAIM ROUTE
    Enforces atomic database lock using SQL UPDATE returning affected row count.
    Guarantees only ONE rider wins the claim, even with simultaneous clicks.
    """
    if current_user.role != 'RIDER':
        return jsonify({'success': False, 'message': 'Only riders can accept rides.'}), 403

    # Generate secure 4-digit OTP
    otp_code = f"{random.randint(1000, 9999)}"
    now = datetime.utcnow()

    # Atomic SQL Update
    result = db.session.execute(
        text("""
            UPDATE rides 
            SET rider_id = :rider_id, 
                status = 'ASSIGNED', 
                assigned_at = :assigned_at, 
                otp = :otp 
            WHERE id = :ride_id AND status = 'DISPATCHING'
        """),
        {
            'rider_id': current_user.id,
            'assigned_at': now,
            'otp': otp_code,
            'ride_id': ride_id
        }
    )
    db.session.commit()

    if result.rowcount == 1:
        # Rider successfully claimed the ride!
        ride = Ride.query.get(ride_id)
        ride_dict = ride.to_dict()

        # Notify the winning customer directly in their room
        socketio.emit('ride_assigned', ride_dict, to=f"user_{ride.customer_id}")

        # Broadcast to all riders to remove request card from their screens
        socketio.emit('ride_claimed', {'ride_id': ride_id, 'claimed_by': current_user.name}, to='riders')

        # Broadcast update to admin dashboard
        socketio.emit('dashboard_update', {'event': 'ride_assigned', 'ride': ride_dict}, to='admin')

        return jsonify({'success': True, 'message': 'Ride accepted successfully!', 'ride': ride_dict})
    else:
        # Atomic lock failed: Another rider already accepted or customer cancelled
        return jsonify({'success': False, 'message': 'Ride is no longer available (already claimed by another rider or cancelled).'}), 409


@api_bp.route('/rides/<int:ride_id>/arrived', methods=['POST'])
@login_required
def rider_arrived(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.rider_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

    if ride.status == 'ASSIGNED':
        ride.status = 'ARRIVING'
        db.session.commit()

        ride_dict = ride.to_dict()
        socketio.emit('ride_arriving', ride_dict, to=f"user_{ride.customer_id}")
        socketio.emit('dashboard_update', {'event': 'ride_arriving', 'ride': ride_dict}, to='admin')
        return jsonify({'success': True, 'ride': ride_dict})

    return jsonify({'success': False, 'message': f'Cannot mark arrived from status {ride.status}'}), 400


@api_bp.route('/rides/<int:ride_id>/verify-otp', methods=['POST'])
@login_required
def verify_otp(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.rider_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

    data = request.get_json() or {}
    submitted_otp = str(data.get('otp', '')).strip()

    if ride.otp and submitted_otp == ride.otp:
        ride.status = 'ACTIVE'
        ride.started_at = datetime.utcnow()
        db.session.commit()

        ride_dict = ride.to_dict()
        socketio.emit('ride_active', ride_dict, to=f"user_{ride.customer_id}")
        socketio.emit('dashboard_update', {'event': 'ride_active', 'ride': ride_dict}, to='admin')
        return jsonify({'success': True, 'message': 'OTP Verified! Ride is now active.', 'ride': ride_dict})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP. Please ask customer to re-read the 4-digit code.'}), 400


@api_bp.route('/rides/<int:ride_id>/complete', methods=['POST'])
@login_required
def complete_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.rider_id != current_user.id and current_user.role != 'ADMIN':
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

    if ride.status in ['ACTIVE', 'ARRIVING', 'ASSIGNED']:
        ride.status = 'COMPLETED'
        ride.completed_at = datetime.utcnow()
        
        # Update rider profile total rides
        if ride.rider and ride.rider.rider_profile:
            ride.rider.rider_profile.total_rides += 1

        db.session.commit()

        ride_dict = ride.to_dict()
        socketio.emit('ride_completed', ride_dict, to=f"user_{ride.customer_id}")
        socketio.emit('dashboard_update', {'event': 'ride_completed', 'ride': ride_dict}, to='admin')
        return jsonify({'success': True, 'message': 'Ride completed successfully!', 'ride': ride_dict})

    return jsonify({'success': False, 'message': f'Cannot complete ride in status {ride.status}'}), 400


@api_bp.route('/rides/<int:ride_id>/cancel', methods=['POST'])
@login_required
def cancel_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.customer_id != current_user.id and current_user.role != 'ADMIN':
        return jsonify({'success': False, 'message': 'Unauthorized to cancel this ride.'}), 403

    if ride.status in ['DISPATCHING', 'ASSIGNED', 'ARRIVING']:
        ride.status = 'CANCELLED'
        ride.cancelled_at = datetime.utcnow()
        data = request.get_json() or {}
        ride.cancellation_reason = data.get('reason', 'Cancelled by user')
        db.session.commit()

        ride_dict = ride.to_dict()
        socketio.emit('ride_cancelled', ride_dict, to=f"user_{ride.customer_id}")
        if ride.rider_id:
            socketio.emit('ride_cancelled', ride_dict, to=f"user_{ride.rider_id}")
        socketio.emit('ride_claimed', {'ride_id': ride_id}, to='riders')
        socketio.emit('dashboard_update', {'event': 'ride_cancelled', 'ride': ride_dict}, to='admin')

        return jsonify({'success': True, 'message': 'Ride cancelled.', 'ride': ride_dict})

    return jsonify({'success': False, 'message': 'Ride cannot be cancelled at this stage.'}), 400


@api_bp.route('/rides/<int:ride_id>/rate', methods=['POST'])
@login_required
def rate_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.customer_id != current_user.id:
        return jsonify({'success': False, 'message': 'Only the customer can rate this ride.'}), 403

    if ride.status != 'COMPLETED':
        return jsonify({'success': False, 'message': 'Can only rate completed rides.'}), 400

    data = request.get_json() or {}
    rating_val = int(data.get('rating', 5))
    feedback_text = data.get('feedback', '').strip()

    rating_entry = Rating.query.filter_by(ride_id=ride_id).first()
    if not rating_entry:
        rating_entry = Rating(
            ride_id=ride_id,
            customer_id=current_user.id,
            rider_id=ride.rider_id,
            rating=rating_val,
            feedback=feedback_text
        )
        db.session.add(rating_entry)
    else:
        rating_entry.rating = rating_val
        rating_entry.feedback = feedback_text

    db.session.commit()

    # Recalculate average rating for rider
    if ride.rider and ride.rider.rider_profile:
        ratings = Rating.query.filter_by(rider_id=ride.rider_id).all()
        if ratings:
            avg_rating = sum(r.rating for r in ratings) / len(ratings)
            ride.rider.rider_profile.rating = avg_rating
            db.session.commit()

    return jsonify({'success': True, 'message': 'Thank you for your rating!'})


@api_bp.route('/rider/toggle-status', methods=['POST'])
@login_required
def toggle_rider_status():
    if current_user.role != 'RIDER':
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

    profile = current_user.rider_profile
    if not profile:
        profile = RiderProfile(user_id=current_user.id)
        db.session.add(profile)

    if not profile.is_approved:
        return jsonify({'success': False, 'message': 'Rider profile pending admin authorization.'}), 403

    data = request.get_json() or {}
    if 'is_available' in data:
        profile.is_available = bool(data['is_available'])
    else:
        profile.is_available = not profile.is_available

    db.session.commit()
    
    socketio.emit('dashboard_update', {'event': 'rider_status_changed'}, to='admin')
    return jsonify({'success': True, 'is_available': profile.is_available})


@api_bp.route('/admin/riders/<int:profile_id>/approve', methods=['POST'])
@login_required
def admin_approve_rider(profile_id):
    if current_user.role != 'ADMIN':
        return jsonify({'success': False, 'message': 'Admin authorization required.'}), 403

    profile = RiderProfile.query.get_or_404(profile_id)
    profile.is_approved = True
    db.session.commit()

    socketio.emit('dashboard_update', {'event': 'rider_approved'}, to='admin')
    return jsonify({'success': True, 'message': f'Rider {profile.user.name} approved successfully!'})


@api_bp.route('/admin/riders/<int:profile_id>/reject', methods=['POST'])
@login_required
def admin_reject_rider(profile_id):
    if current_user.role != 'ADMIN':
        return jsonify({'success': False, 'message': 'Admin authorization required.'}), 403

    profile = RiderProfile.query.get_or_404(profile_id)
    user = profile.user
    db.session.delete(profile)
    db.session.delete(user)
    db.session.commit()

    socketio.emit('dashboard_update', {'event': 'rider_rejected'}, to='admin')
    return jsonify({'success': True, 'message': 'Rider application rejected.'})
