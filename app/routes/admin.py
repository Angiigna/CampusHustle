from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import Ride, RiderProfile, User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def dashboard():
    if current_user.role != 'ADMIN':
        flash('Admin authorization required.', 'error')
        return redirect(url_for('customer.book'))

    today_start = datetime.combine(date.today(), datetime.min.time())

    # Live Metrics
    available_riders = RiderProfile.query.filter_by(is_available=True, is_approved=True).count()
    total_riders = RiderProfile.query.filter_by(is_approved=True).count()
    
    dispatching_count = Ride.query.filter_by(status='DISPATCHING').count()
    active_count = Ride.query.filter(Ride.status.in_(['ASSIGNED', 'ARRIVING', 'ACTIVE'])).count()
    
    completed_today = Ride.query.filter(
        Ride.status == 'COMPLETED',
        Ride.completed_at >= today_start
    ).all()
    
    revenue_today = sum(int(r.fare) for r in completed_today)

    # Pending Rider Registrations Requiring Approval
    pending_riders = RiderProfile.query.filter_by(is_approved=False).all()

    # Active & Recent Rides Table
    active_rides = Ride.query.filter(
        Ride.status.in_(['DISPATCHING', 'ASSIGNED', 'ARRIVING', 'ACTIVE'])
    ).order_by(Ride.requested_at.desc()).all()

    recent_history = Ride.query.filter(
        Ride.status.in_(['COMPLETED', 'CANCELLED', 'EXPIRED'])
    ).order_by(Ride.requested_at.desc()).limit(20).all()

    return render_template(
        'admin/dashboard.html',
        available_riders=available_riders,
        total_riders=total_riders,
        dispatching_count=dispatching_count,
        active_count=active_count,
        completed_count=len(completed_today),
        revenue_today=revenue_today,
        pending_riders=[p.to_dict() for p in pending_riders],
        active_rides=[r.to_dict() for r in active_rides],
        recent_history=[r.to_dict() for r in recent_history]
    )
