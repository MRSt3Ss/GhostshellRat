import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ganti-ini-sesuka-hati'

# SocketIO untuk realtime
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True
)

# Penyimpanan notifikasi (sementara di memory)
notifications = []
notification_counter = 1

# Dapatkan URL dari Railway
RAILWAY_URL = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost:5000')
if RAILWAY_URL and not RAILWAY_URL.startswith('http'):
    RAILWAY_URL = f"https://{RAILWAY_URL}"

@app.route('/')
def index():
    """Halaman dashboard"""
    return render_template('index.html', server_url=RAILWAY_URL)

@app.route('/api/notifications')
def get_notifications():
    """Ambil semua notifikasi"""
    return jsonify({
        'success': True,
        'data': notifications[::-1]  # Balik biar yang baru di atas
    })

@app.route('/api/send-notification', methods=['POST'])
def receive_notification():
    """
    ⭐ INI ENDPOINT YANG DIPAKAI ANDROID APP ⭐
    URL: https://nama-projek-mu.up.railway.app/api/send-notification
    """
    global notification_counter
    
    try:
        # Ambil data dari Android app
        data = request.json
        logger.info(f"📱 NOTIF DARI ANDROID: {data}")
        
        # Buat format notifikasi
        notification = {
            'id': notification_counter,
            'waktu': datetime.now().strftime('%H:%M:%S %d/%m/%Y'),
            'dari': data.get('type', 'ANDROID'),
            'pengirim': data.get('sender', 'Android App'),
            'konten': data.get('content', 'No content'),
            'ip': request.remote_addr
        }
        
        # Simpan
        notifications.append(notification)
        notification_counter += 1
        
        # Hapus kalau kebanyakan (optional)
        if len(notifications) > 100:
            notifications.pop(0)
        
        # Kirim ke semua yang lagi buka web dashboard
        socketio.emit('new_notification', notification)
        
        return jsonify({'success': True, 'id': notification['id']})
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/health')
def health():
    """Cek apakah server hidup"""
    return jsonify({
        'status': 'ALIVE',
        'time': datetime.now().isoformat(),
        'total_notif': len(notifications),
        'server_url': RAILWAY_URL
    })

@socketio.on('connect')
def handle_connect():
    """Kalau ada yang buka web"""
    logger.info('🌐 Ada yang buka dashboard')
    emit('server_info', {'url': RAILWAY_URL})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info("="*50)
    logger.info("🚀 SERVER NOTIFICATION READY")
    logger.info("="*50)
    logger.info(f"📊 Dashboard: https://{RAILWAY_URL}/")
    logger.info(f"📱 Android kirim ke: https://{RAILWAY_URL}/api/send-notification")
    logger.info("="*50)
    socketio.run(app, host='0.0.0.0', port=port)
