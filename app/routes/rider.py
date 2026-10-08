from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import Ride, RiderProfile

rider_bp = Blueprint('rider', __name__)

@rider_bp.route('/rider')
@login_required
def dashboard():
    if current_user.role != 'RIDER':
        flash('Access restricted to registered riders.', 'error')
        return redirect(url_for('customer.book'))

    profile = current_user.rider_profile
    if not profile:
        profile = RiderProfile(user_id=current_user.id, vehicle_type='Motorbike', is_available=False, is_approved=False)
        db.session.add(profile)
        db.session.commit()

    # Block access if rider application is pending admin approval
    if not profile.is_approved:
        return render_template('auth/pending_approval.html', profile=profile.to_dict())

    # Active assigned/arriving/active ride for this rider
    current_ride = Ride.query.filter(
        Ride.rider_id == current_user.id,
        Ride.status.in_(['ASSIGNED', 'ARRIVING', 'ACTIVE'])
    ).first()

    # Pending broadcast rides in DISPATCHING status if rider is available
    pending_rides = []
    if profile.is_available and not current_ride:
        pending_rides = Ride.query.filter_by(status='DISPATCHING').order_by(Ride.requested_at.desc()).all()

    return render_template(
        'rider/dashboard.html',
        profile=profile.to_dict(),
        current_ride=current_ride.to_dict() if current_ride else None,
        pending_rides=[r.to_dict() for r in pending_rides]
    )
