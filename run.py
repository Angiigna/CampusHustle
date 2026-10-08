from gevent import monkey
monkey.patch_all()

import os
import sys
from app import create_app, socketio

# Ensure unbuffered logging
sys.stdout.reconfigure(line_buffering=True)

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" Papido — Campus Bike-Taxi Mobility Platform ")
    print(f" Running on port: {port} ")
    print(f"=======================================================\n")
    sys.stdout.flush()
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
