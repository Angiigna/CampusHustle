async function approveRider(profileId) {
    if (!confirm('Approve this rider for campus operations?')) return;

    try {
        const response = await fetch(`/api/admin/riders/${profileId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || 'Failed to approve rider.');
        }
    } catch (err) {
        console.error('Error approving rider:', err);
    }
}

async function rejectRider(profileId) {
    if (!confirm('Reject and delete this rider registration application?')) return;

    try {
        const response = await fetch(`/api/admin/riders/${profileId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || 'Failed to reject rider application.');
        }
    } catch (err) {
        console.error('Error rejecting rider:', err);
    }
}

async function adminCancelRide(rideId) {
    if (!confirm(`Are you sure you want to force cancel ride #${rideId}?`)) return;

    try {
        const response = await fetch(`/api/rides/${rideId}/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: 'Admin emergency override' })
        });
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        }
    } catch (err) {
        console.error('Error cancelling ride:', err);
    }
}

// Socket.IO Listener for Real-Time Admin Dashboard Refresh
socket.on('dashboard_update', (data) => {
    console.log('[Admin Socket] Dashboard Update Signal:', data);
    // Reload admin dashboard to fetch live metric & table state
    window.location.reload();
});
