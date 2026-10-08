let currentActiveRideId = null;
let selectedStarRating = 5;

// Leaflet Map State Handles
let leafletMap = null;
let pickupMarker = null;
let dropMarker = null;
let riderMarker = null;
let lastRiderUpdateTimestamp = null;
let freshnessTimer = null;

// Swap pickup & drop selections
function swapLocations() {
    const pickup = document.getElementById('pickupSelect');
    const drop = document.getElementById('dropSelect');
    const temp = pickup.value;
    pickup.value = drop.value;
    drop.value = temp;
    calculateAndPreviewFare();
}

// Client-side rule engine for instant zero-latency fare calculation & button activation
const GIRLS_NODES = new Set(["KANNAGI", "SAVITRIBAI_PHULE", "NARMADA", "KALPANA_CHAWLA", "MADAM_CURIE", "YAMUNA", "GANGA", "SARASWATHI", "CAUVERY", "MOTHER_THERESA"]);

function getClientFare(pickup, drop) {
    const p = (pickup || '').toUpperCase();
    const d = (drop || '').toUpperCase();

    if ((p === "SJ_AND_UMISARC" && d === "GATE_2") || (d === "SJ_AND_UMISARC" && p === "GATE_2")) {
        return 35;
    }
    if ((p === "SJ_AND_UMISARC" && GIRLS_NODES.has(d)) || (d === "SJ_AND_UMISARC" && GIRLS_NODES.has(p))) {
        return 30;
    }
    const sj30Targets = new Set(["GATE_1", "ADMIN_BLOCK", "LIBRARY_AND_READING_ROOM", "HEALTH_CENTRE", "LAW_DEPARTMENT", "SCIENCE_BLOCK"]);
    if ((p === "SJ_AND_UMISARC" && sj30Targets.has(d)) || (d === "SJ_AND_UMISARC" && sj30Targets.has(p))) {
        return 30;
    }
    return 25;
}

// Live Fare Calculation & Instant Button Activation
function calculateAndPreviewFare() {
    const pickupEl = document.getElementById('pickupSelect');
    const dropEl = document.getElementById('dropSelect');
    const previewBox = document.getElementById('farePreviewBox');
    const fareAmountText = document.getElementById('previewFareAmount');
    const confirmBtn = document.getElementById('confirmRideBtn');

    if (!pickupEl || !dropEl || !previewBox || !confirmBtn) return;

    const pickup = pickupEl.value;
    const drop = dropEl.value;

    if (!pickup || !drop || pickup === drop) {
        previewBox.classList.add('hidden');
        confirmBtn.disabled = true;
        confirmBtn.className = "w-full py-3.5 px-4 bg-slate-800 text-slate-500 font-bold rounded-xl text-sm cursor-not-allowed";
        return;
    }

    // 1. Instant client-side activation so button becomes active immediately
    const fare = getClientFare(pickup, drop);
    fareAmountText.textContent = `₹${fare}`;
    previewBox.classList.remove('hidden');
    confirmBtn.disabled = false;
    confirmBtn.className = "w-full py-3.5 px-4 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-bold rounded-xl text-sm transition-all shadow-lg shadow-emerald-600/30 cursor-pointer flex items-center justify-center space-x-2";

    // 2. Async verification with backend API
    fetch(`/api/fare?pickup=${encodeURIComponent(pickup)}&drop=${encodeURIComponent(drop)}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.fare) {
                fareAmountText.textContent = `₹${data.fare}`;
            }
        })
        .catch(err => console.log('Backend fare sync:', err));
}

function openConfirmationModal() {
    const pickupSelect = document.getElementById('pickupSelect');
    const dropSelect = document.getElementById('dropSelect');
    
    const pickupText = pickupSelect.options[pickupSelect.selectedIndex].text;
    const dropText = dropSelect.options[dropSelect.selectedIndex].text;
    const fareText = document.getElementById('previewFareAmount').textContent;

    document.getElementById('modalPickupText').textContent = pickupText;
    document.getElementById('modalDropText').textContent = dropText;
    document.getElementById('modalFareText').textContent = fareText;

    document.getElementById('confirmModal').classList.remove('hidden');
}

function closeConfirmationModal() {
    document.getElementById('confirmModal').classList.add('hidden');
}

// Create Ride Request
async function submitRideRequest() {
    const pickup = document.getElementById('pickupSelect').value;
    const drop = document.getElementById('dropSelect').value;
    closeConfirmationModal();

    try {
        const response = await fetch('/api/rides', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pickup_code: pickup, drop_code: drop })
        });
        const data = await response.json();

        if (data.success) {
            currentActiveRideId = data.ride.id;
            updateCustomerRideUI(data.ride);
        } else {
            alert(data.message || 'Failed to request ride.');
        }
    } catch (err) {
        console.error('Error requesting ride:', err);
        alert('Network error requesting ride.');
    }
}

// Update Customer UI view based on ride state
function updateCustomerRideUI(ride) {
    if (!ride) return;
    currentActiveRideId = ride.id;

    document.getElementById('bookingCard').classList.add('hidden');
    const card = document.getElementById('activeRideCard');
    card.classList.remove('hidden');

    document.getElementById('rideStatusBadge').textContent = ride.status;
    document.getElementById('rideFareDisplay').textContent = `₹${ride.fare}`;
    document.getElementById('ridePickupText').textContent = ride.pickup_name;
    document.getElementById('rideDropText').textContent = ride.drop_name;

    const dispatchingView = document.getElementById('dispatchingView');
    const assignedView = document.getElementById('assignedView');
    const activeView = document.getElementById('activeView');
    const mapContainer = document.getElementById('liveTrackingMapContainer');

    dispatchingView.classList.add('hidden');
    assignedView.classList.add('hidden');
    activeView.classList.add('hidden');
    mapContainer.classList.add('hidden');

    if (ride.status === 'DISPATCHING') {
        dispatchingView.classList.remove('hidden');
    } else if (ride.status === 'ASSIGNED' || ride.status === 'ARRIVING' || ride.status === 'ACTIVE') {
        if (ride.status === 'ACTIVE') {
            activeView.classList.remove('hidden');
        } else {
            assignedView.classList.remove('hidden');
            document.getElementById('riderNameText').textContent = ride.rider_name || 'Rider Assigned';
            document.getElementById('riderVehicleText').textContent = ride.vehicle_info || 'Bike Taxi';
            document.getElementById('riderPhoneCallBtn').href = `tel:${ride.rider_phone || ''}`;
            document.getElementById('otpDisplay').textContent = ride.otp || '----';
        }

        // Show Leaflet Map & Join Socket Room
        mapContainer.classList.remove('hidden');
        socket.emit('join_ride_room', { ride_id: ride.id });
        initOrUpdateCustomerMap(ride);
    }
}

// Initialize & Update Leaflet OpenStreetMap
function initOrUpdateCustomerMap(ride) {
    const defaultCenter = [12.0230, 79.8550]; // Campus Center
    const pickupCoords = (ride.pickup_lat && ride.pickup_lng) ? [ride.pickup_lat, ride.pickup_lng] : defaultCenter;
    const dropCoords = (ride.drop_lat && ride.drop_lng) ? [ride.drop_lat, ride.drop_lng] : defaultCenter;

    if (!leafletMap) {
        leafletMap = L.map('customerMap').setView(pickupCoords, 16);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(leafletMap);
    }

    // Custom Icon Pins
    const pickupIcon = L.divIcon({
        className: 'custom-map-icon',
        html: `<div style="background-color: #22c55e; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px rgba(34,197,94,0.8);"></div>`,
        iconSize: [14, 14]
    });

    const dropIcon = L.divIcon({
        className: 'custom-map-icon',
        html: `<div style="background-color: #f43f5e; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px rgba(244,63,94,0.8);"></div>`,
        iconSize: [14, 14]
    });

    const riderIcon = L.divIcon({
        className: 'custom-map-icon',
        html: `<div style="background-color: #f59e0b; width: 22px; height: 22px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: black; font-size: 10px; font-weight: bold; box-shadow: 0 0 10px rgba(245,158,11,0.9);"><i class="fa-solid fa-motorcycle"></i></div>`,
        iconSize: [22, 22]
    });

    // Add or Update Pickup Marker
    if (!pickupMarker) {
        pickupMarker = L.marker(pickupCoords, { icon: pickupIcon }).addTo(leafletMap).bindPopup(`<b>Pickup:</b> ${ride.pickup_name}`);
    } else {
        pickupMarker.setLatLng(pickupCoords);
    }

    // Add or Update Drop Marker
    if (!dropMarker) {
        dropMarker = L.marker(dropCoords, { icon: dropIcon }).addTo(leafletMap).bindPopup(`<b>Drop:</b> ${ride.drop_name}`);
    } else {
        dropMarker.setLatLng(dropCoords);
    }

    // Initial Rider Position if available from DB
    if (ride.latest_latitude && ride.latest_longitude) {
        const riderCoords = [ride.latest_latitude, ride.latest_longitude];
        if (!riderMarker) {
            riderMarker = L.marker(riderCoords, { icon: riderIcon }).addTo(leafletMap).bindPopup(`<b>Rider:</b> ${ride.rider_name || 'Bike Taxi'}`);
        } else {
            riderMarker.setLatLng(riderCoords);
        }
        lastRiderUpdateTimestamp = Date.now();
        updateLocationFreshnessBadge(ride.location_updated_seconds_ago || 0);
    } else {
        updateLocationFreshnessBadge(null);
    }

    // Fit map bounds to show points
    const boundsPoints = [pickupCoords, dropCoords];
    if (riderMarker) boundsPoints.push(riderMarker.getLatLng());
    leafletMap.fitBounds(L.latLngBounds(boundsPoints), { padding: [30, 30] });

    // Invalidate map size after DOM render
    setTimeout(() => {
        if (leafletMap) leafletMap.invalidateSize();
    }, 300);

    // Start Freshness Monitoring Interval
    startFreshnessMonitor();
}

function updateLocationFreshnessBadge(secondsAgo) {
    const badge = document.getElementById('locationFreshnessBadge');
    if (!badge) return;

    if (secondsAgo === null || secondsAgo === undefined) {
        badge.textContent = 'Waiting for rider GPS fix...';
        badge.className = 'text-[10px] text-amber-400 font-mono';
    } else if (secondsAgo > 30) {
        badge.textContent = `Rider location temporarily unavailable (${secondsAgo}s ago)`;
        badge.className = 'text-[10px] text-rose-400 font-mono';
    } else if (secondsAgo === 0) {
        badge.textContent = 'Updated just now';
        badge.className = 'text-[10px] text-emerald-400 font-mono font-bold';
    } else {
        badge.textContent = `Updated ${secondsAgo}s ago`;
        badge.className = 'text-[10px] text-emerald-400 font-mono';
    }
}

function startFreshnessMonitor() {
    if (freshnessTimer) clearInterval(freshnessTimer);

    freshnessTimer = setInterval(() => {
        if (lastRiderUpdateTimestamp) {
            const secondsAgo = Math.floor((Date.now() - lastRiderUpdateTimestamp) / 1000);
            updateLocationFreshnessBadge(secondsAgo);
        }
    }, 3000);
}

async function cancelActiveRide() {
    if (!currentActiveRideId) return;
    if (!confirm('Are you sure you want to cancel this ride request?')) return;

    try {
        const response = await fetch(`/api/rides/${currentActiveRideId}/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: 'Cancelled by customer' })
        });
        const data = await response.json();
        if (data.success) {
            resetCustomerBookingUI();
        }
    } catch (err) {
        console.error('Error cancelling ride:', err);
    }
}

function resetCustomerBookingUI() {
    currentActiveRideId = null;
    if (freshnessTimer) clearInterval(freshnessTimer);
    
    document.getElementById('activeRideCard').classList.add('hidden');
    document.getElementById('bookingCard').classList.remove('hidden');
    document.getElementById('fareForm').reset();
    calculateAndPreviewFare();
}

// Rating Modal Logic
function setStarRating(stars) {
    selectedStarRating = stars;
    const starBtns = document.querySelectorAll('.star-btn');
    starBtns.forEach((btn, index) => {
        if (index < stars) {
            btn.className = "star-btn text-2xl text-amber-400 transition-colors";
        } else {
            btn.className = "star-btn text-2xl text-slate-700 hover:text-amber-400 transition-colors";
        }
    });
}

async function submitRating() {
    if (!currentActiveRideId) return;
    const feedback = document.getElementById('feedbackText').value;

    try {
        const response = await fetch(`/api/rides/${currentActiveRideId}/rate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rating: selectedStarRating, feedback: feedback })
        });
        const data = await response.json();
        if (data.success) {
            document.getElementById('ratingModal').classList.add('hidden');
            resetCustomerBookingUI();
        }
    } catch (err) {
        console.error('Error submitting rating:', err);
    }
}

// Socket.IO Real-Time Customer Listeners
socket.on('ride_assigned', (data) => {
    console.log('[Customer Socket] Ride Assigned!', data);
    updateCustomerRideUI(data);
});

socket.on('ride_arriving', (data) => {
    console.log('[Customer Socket] Rider Arriving!', data);
    updateCustomerRideUI(data);
});

socket.on('ride_active', (data) => {
    console.log('[Customer Socket] Ride Active!', data);
    updateCustomerRideUI(data);
});

socket.on('live_location_update', (data) => {
    console.log('[Customer Socket] Live Location Update Received:', data);
    if (!leafletMap) return;

    const riderCoords = [data.latitude, data.longitude];

    const riderIcon = L.divIcon({
        className: 'custom-map-icon',
        html: `<div style="background-color: #f59e0b; width: 22px; height: 22px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: black; font-size: 10px; font-weight: bold; box-shadow: 0 0 10px rgba(245,158,11,0.9);"><i class="fa-solid fa-motorcycle"></i></div>`,
        iconSize: [22, 22]
    });

    if (!riderMarker) {
        riderMarker = L.marker(riderCoords, { icon: riderIcon }).addTo(leafletMap).bindPopup(`<b>Assigned Rider</b>`);
    } else {
        riderMarker.setLatLng(riderCoords);
    }

    lastRiderUpdateTimestamp = Date.now();
    updateLocationFreshnessBadge(0);
});

socket.on('ride_completed', (data) => {
    console.log('[Customer Socket] Ride Completed!', data);
    currentActiveRideId = data.id;
    if (freshnessTimer) clearInterval(freshnessTimer);
    document.getElementById('activeRideCard').classList.add('hidden');
    document.getElementById('ratingModal').classList.remove('hidden');
});

socket.on('ride_cancelled', (data) => {
    console.log('[Customer Socket] Ride Cancelled.', data);
    alert('Ride request was cancelled.');
    resetCustomerBookingUI();
});

// Auto-restore customer active ride state & attach form change listeners
document.addEventListener('DOMContentLoaded', () => {
    if (window.INITIAL_ACTIVE_RIDE) {
        updateCustomerRideUI(window.INITIAL_ACTIVE_RIDE);
    }

    const pickupSelect = document.getElementById('pickupSelect');
    const dropSelect = document.getElementById('dropSelect');
    if (pickupSelect) {
        pickupSelect.addEventListener('change', calculateAndPreviewFare);
        pickupSelect.addEventListener('input', calculateAndPreviewFare);
    }
    if (dropSelect) {
        dropSelect.addEventListener('change', calculateAndPreviewFare);
        dropSelect.addEventListener('input', calculateAndPreviewFare);
    }
});
