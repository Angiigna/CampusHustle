from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services.fare_service import LOCATION_CATEGORIES
from app.models.models import Ride

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
@customer_bp.route('/customer')
@login_required
def book():
    if current_user.role == 'RIDER':
        return redirect(url_for('rider.dashboard'))
    elif current_user.role == 'ADMIN':
        return redirect(url_for('admin.dashboard'))

    # Check for active ride (not COMPLETED or CANCELLED or EXPIRED)
    active_ride = Ride.query.filter(
        Ride.customer_id == current_user.id,
        Ride.status.in_(['DISPATCHING', 'ASSIGNED', 'ARRIVING', 'ACTIVE'])
    ).order_by(Ride.requested_at.desc()).first()

    return render_template(
        'customer/book.html',
        location_categories=LOCATION_CATEGORIES,
        active_ride=active_ride.to_dict() if active_ride else None
    )
