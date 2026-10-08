let activeRiderRideId = null;
let riderWatchId = null;
let lastLocationEmitTime = 0;

async function toggleRiderAvailability() {
    const toggle = document.getElementById('availabilityToggle');
    try {
        const response = await fetch('/api/rider/toggle-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_available: toggle.checked })
        });
        const data = await response.json();
        if (data.success) {
            if (!toggle.checked) {
                document.getElementById('broadcastSection').classList.add('hidden');
            } else if (!activeRiderRideId) {
                document.getElementById('broadcastSection').classList.remove('hidden');
            }
        }
    } catch (err) {
        console.error('Error toggling rider availability:', err);
    }
}

// Atomic Accept Ride Action
async function acceptRide(rideId) {
    try {
        const response = await fetch(`/api/rides/${rideId}/accept`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.success) {
            activeRiderRideId = data.ride.id;
            updateRiderActiveCard(data.ride);
            document.getElementById('broadcastSection').classList.add('hidden');
        } else {
            alert(data.message || 'Ride is no longer available.');
            removeBroadcastCard(rideId);
        }
    } catch (err) {
        console.error('Error accepting ride:', err);
        alert('Network error accepting ride.');
    }
}

function declineRideCard(rideId) {
    removeBroadcastCard(rideId);
}

function removeBroadcastCard(rideId) {
    const card = document.querySelector(`.ride-request-card[data-ride-id="${rideId}"]`);
    if (card) {
        card.remove();
    }
    const container = document.getElementById('pendingRidesContainer');
    if (container && container.children.length === 0) {
        document.getElementById('noRidesMsg').classList.remove('hidden');
    }
    updateBroadcastCount();
}

function updateBroadcastCount() {
    const container = document.getElementById('pendingRidesContainer');
    const count = container ? container.children.length : 0;
    const badge = document.getElementById('broadcastCountBadge');
    if (badge) {
        badge.textContent = `${count} Request(s)`;
    }
}

function updateRiderActiveCard(ride) {
    if (!ride) return;
    activeRiderRideId = ride.id;

    const activeCard = document.getElementById('riderActiveRideCard');
    activeCard.classList.remove('hidden');

    document.getElementById('activeRideStatusText').textContent = ride.status;
    document.getElementById('activeCustomerName').textContent = ride.customer_name;
    document.getElementById('activeCustomerPhone').href = `tel:${ride.customer_phone}`;
    document.getElementById('activePickupText').textContent = ride.pickup_name;
    document.getElementById('activeDropText').textContent = ride.drop_name;
    document.getElementById('activeFareText').textContent = `₹${ride.fare}`;

    const assignedGroup = document.getElementById('assignedActionGroup');
    const arrivingGroup = document.getElementById('arrivingActionGroup');
    const activeGroup = document.getElementById('activeActionGroup');

    assignedGroup.classList.add('hidden');
    arrivingGroup.classList.add('hidden');
    activeGroup.classList.add('hidden');

    if (ride.status === 'ASSIGNED') {
        assignedGroup.classList.remove('hidden');
    } else if (ride.status === 'ARRIVING') {
        arrivingGroup.classList.remove('hidden');
    } else if (ride.status === 'ACTIVE') {
        activeGroup.classList.remove('hidden');
    }

    // Start Live GPS Location Sharing if Ride is Active/Assigned
    if (['ASSIGNED', 'ARRIVING', 'ACTIVE'].includes(ride.status)) {
        socket.emit('join_ride_room', { ride_id: ride.id });
        startLocationTracking(ride.id);
    } else {
        stopLocationTracking();
    }
}

// Browser Geolocation Live Tracking Engine
function startLocationTracking(rideId) {
    if (riderWatchId !== null) return;

    if (!navigator.geolocation) {
        console.warn('Geolocation not supported by this browser.');
        updateGpsStatusUI('DENIED', 'Geolocation unavailable in browser');
        return;
    }

    updateGpsStatusUI('SEARCHING', 'Acquiring GPS fix...');

    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 2000
    };

    riderWatchId = navigator.geolocation.watchPosition(
        (position) => {
            const now = Date.now();
            // Throttle GPS broadcast to once every ~2.5 seconds
            if (now - lastLocationEmitTime >= 2500) {
                lastLocationEmitTime = now;
                const payload = {
                    ride_id: rideId,
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };
                socket.emit('rider_location_update', payload);
                updateGpsStatusUI('ACTIVE', 'Live GPS Location Sharing Active');
            }
        },
        (error) => {
            console.warn('Geolocation error:', error);
            if (error.code === error.PERMISSION_DENIED) {
                updateGpsStatusUI('DENIED', 'Location permission denied');
            } else {
                updateGpsStatusUI('SEARCHING', 'Acquiring campus GPS signal...');
            }
        },
        options
    );
}

function stopLocationTracking() {
    if (riderWatchId !== null) {
        navigator.geolocation.clearWatch(riderWatchId);
        riderWatchId = null;
        console.log('[Rider Tracking] GPS location sharing stopped.');
    }
}

function updateGpsStatusUI(state, message) {
    const textEl = document.getElementById('gpsStatusText');
    const badgeEl = document.getElementById('gpsSignalBadge');
    if (!textEl || !badgeEl) return;

    textEl.textContent = message;

    if (state === 'ACTIVE') {
        badgeEl.textContent = 'GPS ON';
        badgeEl.className = 'text-[10px] font-bold text-emerald-400 uppercase bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30';
    } else if (state === 'DENIED') {
        badgeEl.textContent = 'DENIED';
        badgeEl.className = 'text-[10px] font-bold text-rose-400 uppercase bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/30';
    } else {
        badgeEl.textContent = 'SEARCHING';
        badgeEl.className = 'text-[10px] font-bold text-amber-400 uppercase bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30';
    }
}

async function markRiderArrived() {
    if (!activeRiderRideId && window.INITIAL_RIDER_RIDE) {
        activeRiderRideId = window.INITIAL_RIDER_RIDE.id;
    }
    if (!activeRiderRideId) {
        console.error('No active ride ID found for rider.');
        return;
    }

    try {
        const response = await fetch(`/api/rides/${activeRiderRideId}/arrived`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            updateRiderActiveCard(data.ride);
        } else {
            alert(data.message || 'Failed to mark arrival.');
        }
    } catch (err) {
        console.error('Error marking arrived:', err);
    }
}

function openOtpModal() {
    document.getElementById('otpInput').value = '';
    document.getElementById('otpModal').classList.remove('hidden');
}

function closeOtpModal() {
    document.getElementById('otpModal').classList.add('hidden');
}

async function submitOtpVerification() {
    if (!activeRiderRideId && window.INITIAL_RIDER_RIDE) {
        activeRiderRideId = window.INITIAL_RIDER_RIDE.id;
    }
    if (!activeRiderRideId) return;
    const otp = document.getElementById('otpInput').value.trim();

    if (otp.length !== 4) {
        alert('Please enter a valid 4-digit numeric OTP.');
        return;
    }

    try {
        const response = await fetch(`/api/rides/${activeRiderRideId}/verify-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp: otp })
        });
        const data = await response.json();

        if (data.success) {
            closeOtpModal();
            updateRiderActiveCard(data.ride);
        } else {
            alert(data.message || 'Invalid OTP. Please verify with customer.');
        }
    } catch (err) {
        console.error('Error verifying OTP:', err);
    }
}

async function completeCurrentRide() {
    if (!activeRiderRideId && window.INITIAL_RIDER_RIDE) {
        activeRiderRideId = window.INITIAL_RIDER_RIDE.id;
    }
    if (!activeRiderRideId) return;
    if (!confirm('Confirm customer has paid via Cash/UPI and ride is complete?')) return;

    try {
        const response = await fetch(`/api/rides/${activeRiderRideId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.success) {
            stopLocationTracking();
            activeRiderRideId = null;
            window.INITIAL_RIDER_RIDE = null;
            document.getElementById('riderActiveRideCard').classList.add('hidden');
            document.getElementById('broadcastSection').classList.remove('hidden');
        }
    } catch (err) {
        console.error('Error completing ride:', err);
    }
}

// Socket.IO Real-Time Rider Listeners
socket.on('new_ride_request', (ride) => {
    console.log('[Rider Socket] Incoming New Ride Request:', ride);
    
    // Play audio alert chime
    const chime = document.getElementById('requestChime');
    if (chime) {
        chime.play().catch(e => console.log('Audio autoplay prevented'));
    }

    const container = document.getElementById('pendingRidesContainer');
    document.getElementById('noRidesMsg').classList.add('hidden');

    const cardHtml = `
    <div class="ride-request-card bg-slate-900 border border-emerald-500/40 rounded-2xl p-4 shadow-xl space-y-3 animate-in fade-in duration-200" data-ride-id="${ride.id}">
        <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Campus Ride Request</span>
            <span class="font-heading font-black text-xl text-emerald-400">₹${ride.fare}</span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
                <span class="text-[10px] text-slate-500 uppercase font-bold block">Pickup</span>
                <span class="font-bold text-slate-200">${ride.pickup_name}</span>
            </div>
            <div>
                <span class="text-[10px] text-slate-500 uppercase font-bold block">Drop</span>
                <span class="font-bold text-slate-200">${ride.drop_name}</span>
            </div>
        </div>

        <div class="grid grid-cols-2 gap-2 pt-1">
            <button onclick="declineRideCard(${ride.id})" class="py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-400 font-semibold rounded-xl text-xs transition-colors">
                Decline
            </button>
            <button onclick="acceptRide(${ride.id})" class="py-2.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-emerald-600/30 flex items-center justify-center space-x-1">
                <i class="fa-solid fa-check"></i>
                <span>ACCEPT RIDE</span>
            </button>
        </div>
    </div>`;

    if (container) {
        container.insertAdjacentHTML('afterbegin', cardHtml);
    }
    updateBroadcastCount();
});

socket.on('ride_claimed', (data) => {
    console.log('[Rider Socket] Ride claimed by another rider:', data);
    removeBroadcastCard(data.ride_id);
});

// Auto-restore rider active ride state on page load/reload
document.addEventListener('DOMContentLoaded', () => {
    if (window.INITIAL_RIDER_RIDE) {
        updateRiderActiveCard(window.INITIAL_RIDER_RIDE);
    }
});
