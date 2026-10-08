// Shared Socket.IO Client Connection Manager
const socket = io();

socket.on('connect', () => {
    console.log('[Papido Socket] Connected to real-time dispatch server.');
});

socket.on('disconnect', () => {
    console.warn('[Papido Socket] Disconnected from server. Reconnecting...');
});
