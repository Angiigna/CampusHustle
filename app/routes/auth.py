from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.models import User, RiderProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'RIDER':
            return redirect(url_for('rider.dashboard'))
        elif current_user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.book'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            if user.role == 'RIDER':
                return redirect(url_for('rider.dashboard'))
            elif user.role == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('customer.book'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if current_user.is_authenticated:
        return redirect(url_for('customer.book'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if not name or not email or not phone or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/register_customer.html')

        existing_user = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if existing_user:
            flash('An account with this email or phone number already exists.', 'error')
            return render_template('auth/register_customer.html')

        user = User(name=name, email=email, phone=phone, role='CUSTOMER')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Account created successfully! Welcome to CampusRide.', 'success')
        return redirect(url_for('customer.book'))

    return render_template('auth/register_customer.html')

@auth_bp.route('/register/rider', methods=['GET', 'POST'])
def register_rider():
    if current_user.is_authenticated:
        if current_user.role == 'RIDER':
            return redirect(url_for('rider.dashboard'))
        return redirect(url_for('customer.book'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        vehicle_type = request.form.get('vehicle_type', 'Motorbike')
        vehicle_number = request.form.get('vehicle_number', '').strip()

        if not name or not email or not phone or not password:
            flash('All required fields must be filled.', 'error')
            return render_template('auth/register_rider.html')

        existing_user = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if existing_user:
            flash('An account with this email or phone number already exists.', 'error')
            return render_template('auth/register_rider.html')

        user = User(name=name, email=email, phone=phone, role='RIDER')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create Rider Profile (Pending Admin Approval)
        profile = RiderProfile(
            user_id=user.id,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            is_available=False,
            is_approved=False # Pending Admin Approval
        )
        db.session.add(profile)
        db.session.commit()

        login_user(user)
        flash('Rider registration submitted! Your profile is pending campus admin approval.', 'info')
        return redirect(url_for('rider.dashboard'))

    return render_template('auth/register_rider.html')



@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
