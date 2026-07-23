# app.py - UPI QR Generator with JSON API + Direct QR Page
from flask import Flask, render_template_string, request, jsonify
import qrcode
import io
import base64
import urllib.parse
import hashlib
import time
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Store order data
orders = {}

# ============== QR DISPLAY PAGE HTML ==============
QR_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>UPI Payment Request</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            position: relative;
            overflow: hidden;
        }
        
        /* Animated Background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 50%, rgba(255, 0, 150, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(0, 255, 200, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 50% 80%, rgba(255, 200, 0, 0.1) 0%, transparent 50%);
            animation: bgFloat 20s ease-in-out infinite;
            z-index: 0;
        }
        
        @keyframes bgFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }
        
        .particle {
            position: absolute;
            border-radius: 50%;
            animation: floatParticle linear infinite;
            opacity: 0.3;
        }
        
        @keyframes floatParticle {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% { opacity: 0.3; }
            90% { opacity: 0.3; }
            100% {
                transform: translateY(-100vh) rotate(720deg);
                opacity: 0;
            }
        }
        
        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(30px);
            border-radius: 32px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 480px;
            width: 100%;
            padding: 36px;
            position: relative;
            z-index: 1;
            animation: containerIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        @keyframes containerIn {
            from {
                opacity: 0;
                transform: translateY(50px) scale(0.9) rotate(-2deg);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1) rotate(0deg);
            }
        }
        
        .header {
            text-align: center;
            padding-bottom: 24px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.05);
            position: relative;
        }
        
        .header::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #ff0080, #ff8c00, #40e0d0);
            border-radius: 10px;
            animation: headerGlow 3s ease-in-out infinite;
        }
        
        @keyframes headerGlow {
            0%, 100% { 
                width: 60px;
                box-shadow: 0 0 20px rgba(255, 0, 128, 0.5);
            }
            50% { 
                width: 120px;
                box-shadow: 0 0 40px rgba(64, 224, 208, 0.5);
            }
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 2px;
            background: linear-gradient(135deg, #ff0080, #ff8c00, #40e0d0, #ff0080);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 4s ease-in-out infinite;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .header .subtitle {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.4);
            margin-top: 4px;
            letter-spacing: 3px;
        }
        
        .payment-info {
            text-align: center;
            padding: 20px 0;
        }
        
        .payment-info .amount {
            font-size: 42px;
            font-weight: 900;
            background: linear-gradient(135deg, #ff0080, #ff8c00, #40e0d0);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 3s ease-in-out infinite;
            letter-spacing: -1px;
        }
        
        .payment-info .amount-label {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.3);
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        
        .payment-info .name {
            font-size: 20px;
            color: rgba(255, 255, 255, 0.9);
            margin-top: 4px;
            font-weight: 700;
        }
        
        .payment-info .note {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.4);
            margin-top: 8px;
            letter-spacing: 1px;
        }
        
        .payment-info .upi-id {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.3);
            margin-top: 4px;
            letter-spacing: 0.5px;
        }
        
        .qr-wrapper {
            position: relative;
            display: inline-block;
            padding: 12px;
            border-radius: 24px;
            background: linear-gradient(135deg, #ff0080, #ff8c00, #40e0d0, #ff0080);
            background-size: 300% 300%;
            animation: borderGlow 3s ease-in-out infinite;
            margin: 10px 0;
        }
        
        @keyframes borderGlow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .qr-container {
            background: white;
            padding: 24px;
            border-radius: 18px;
            display: inline-block;
            position: relative;
            min-height: 220px;
            min-width: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #ffffff;
            overflow: hidden;
        }
        
        .qr-container.glow {
            animation: qrGlowPulse 2s ease-in-out infinite;
        }
        
        @keyframes qrGlowPulse {
            0% {
                box-shadow: 0 0 30px rgba(255, 0, 128, 0.3), 0 0 60px rgba(255, 140, 0, 0.2);
            }
            50% {
                box-shadow: 0 0 60px rgba(64, 224, 208, 0.5), 0 0 120px rgba(255, 0, 128, 0.3), 0 0 180px rgba(255, 140, 0, 0.2);
            }
            100% {
                box-shadow: 0 0 30px rgba(255, 0, 128, 0.3), 0 0 60px rgba(255, 140, 0, 0.2);
            }
        }
        
        .qr-container img {
            max-width: 100%;
            height: auto;
            border-radius: 12px;
            animation: qrAppear 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            z-index: 2;
        }
        
        @keyframes qrAppear {
            0% {
                opacity: 0;
                transform: scale(0.2) rotate(-15deg);
            }
            50% {
                transform: scale(1.1) rotate(2deg);
            }
            70% {
                transform: scale(0.95) rotate(-1deg);
            }
            100% {
                opacity: 1;
                transform: scale(1) rotate(0deg);
            }
        }
        
        .qr-container.scanning::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #ff0080, #40e0d0, transparent);
            animation: scanLine 2.5s ease-in-out infinite;
            z-index: 3;
            border-radius: 20px;
            box-shadow: 0 0 20px rgba(255, 0, 128, 0.5);
        }
        
        @keyframes scanLine {
            0% {
                top: 0;
                opacity: 0;
            }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% {
                top: 100%;
                opacity: 0;
            }
        }
        
        .qr-container .corner {
            position: absolute;
            width: 20px;
            height: 20px;
            border: 3px solid #ff0080;
            z-index: 4;
            opacity: 0.6;
        }
        
        .qr-container .corner.tl { top: 8px; left: 8px; border-right: none; border-bottom: none; }
        .qr-container .corner.tr { top: 8px; right: 8px; border-left: none; border-bottom: none; }
        .qr-container .corner.bl { bottom: 8px; left: 8px; border-right: none; border-top: none; }
        .qr-container .corner.br { bottom: 8px; right: 8px; border-left: none; border-top: none; }
        
        .actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn-secondary {
            padding: 14px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-family: inherit;
            letter-spacing: 0.5px;
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }
        
        .btn-secondary:hover {
            transform: translateY(-3px) scale(1.05);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .btn-secondary:active {
            transform: scale(0.93);
        }
        
        .btn-open {
            background: linear-gradient(135deg, rgba(72, 187, 120, 0.3), rgba(56, 161, 105, 0.3));
            border-color: rgba(72, 187, 120, 0.3);
            color: #48bb78;
        }
        
        .btn-open:hover {
            background: linear-gradient(135deg, rgba(72, 187, 120, 0.5), rgba(56, 161, 105, 0.5));
            box-shadow: 0 10px 30px rgba(72, 187, 120, 0.2);
            border-color: #48bb78;
        }
        
        .btn-download {
            background: linear-gradient(135deg, rgba(66, 153, 225, 0.2), rgba(49, 130, 206, 0.2));
            border-color: rgba(66, 153, 225, 0.2);
            color: #4299e1;
        }
        
        .btn-download:hover {
            background: linear-gradient(135deg, rgba(66, 153, 225, 0.4), rgba(49, 130, 206, 0.4));
            box-shadow: 0 10px 30px rgba(66, 153, 225, 0.2);
            border-color: #4299e1;
        }
        
        .btn-copy {
            background: linear-gradient(135deg, rgba(251, 188, 4, 0.2), rgba(249, 171, 0, 0.2));
            border-color: rgba(251, 188, 4, 0.2);
            color: #fbbc04;
        }
        
        .btn-copy:hover {
            background: linear-gradient(135deg, rgba(251, 188, 4, 0.4), rgba(249, 171, 0, 0.4));
            box-shadow: 0 10px 30px rgba(251, 188, 4, 0.2);
            border-color: #fbbc04;
        }
        
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, rgba(255, 0, 128, 0.2), rgba(64, 224, 208, 0.2));
            color: rgba(255, 255, 255, 0.5);
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 10px;
            margin-top: 18px;
            font-weight: 700;
            border: 1px solid rgba(255, 255, 255, 0.05);
            letter-spacing: 1px;
            backdrop-filter: blur(10px);
        }
        
        .status {
            margin-top: 16px;
            padding: 14px;
            border-radius: 14px;
            font-size: 13px;
            text-align: center;
            display: none;
            animation: slideUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(15px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        .status.success {
            display: block;
            background: rgba(72, 187, 120, 0.15);
            color: #48bb78;
            border-color: rgba(72, 187, 120, 0.2);
        }
        
        .status.error {
            display: block;
            background: rgba(245, 101, 101, 0.15);
            color: #fc8181;
            border-color: rgba(245, 101, 101, 0.2);
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 24px;
                border-radius: 24px;
            }
            
            .actions {
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .payment-info .amount {
                font-size: 34px;
            }
            
            .qr-container {
                min-height: 180px;
                min-width: 180px;
                padding: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    
    <div class="container">
        <div class="header">
            <h1>⚡ UPI Payment</h1>
            <div class="subtitle">✦ PAYMENT REQUEST ✦</div>
        </div>
        
        <div class="payment-info">
            <div class="amount-label">AMOUNT</div>
            <div class="amount">₹{{ amount }}</div>
            {% if name %}
            <div class="name">✦ {{ name }} ✦</div>
            {% endif %}
            <div class="upi-id">📱 {{ upi_id }}</div>
        </div>
        
        <div style="text-align: center;">
            <div class="qr-wrapper">
                <div class="qr-container glow scanning" id="qrContainer">
                    <div class="corner tl"></div>
                    <div class="corner tr"></div>
                    <div class="corner bl"></div>
                    <div class="corner br"></div>
                    <img src="{{ qr_url }}" alt="QR Code">
                </div>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn-secondary btn-open" id="openBtn">📱 OPEN UPI</button>
            <button class="btn-secondary btn-copy" id="copyLinkBtn">📋 COPY LINK</button>
            <button class="btn-secondary btn-download" id="downloadBtn">💾 DOWNLOAD QR</button>
            <button class="btn-secondary" onclick="window.location.href='/'">🏠 HOME</button>
        </div>
        
        <div style="text-align: center;">
            <div class="badge">✦ SCAN TO PAY • INSTANT • SECURE ✦</div>
        </div>
        
        <div id="status" class="status"></div>
    </div>
    
    <script>
        // Create particles
        function createParticles() {
            const container = document.getElementById('particles');
            const colors = ['#ff0080', '#ff8c00', '#40e0d0', '#ff0080', '#ff8c00'];
            
            for (let i = 0; i < 30; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                const size = Math.random() * 6 + 2;
                particle.style.width = size + 'px';
                particle.style.height = size + 'px';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.background = colors[Math.floor(Math.random() * colors.length)];
                particle.style.animationDuration = (Math.random() * 15 + 10) + 's';
                particle.style.animationDelay = (Math.random() * 10) + 's';
                particle.style.boxShadow = `0 0 ${size * 2}px ${colors[Math.floor(Math.random() * colors.length)]}`;
                container.appendChild(particle);
            }
        }
        createParticles();
        
        const upiLink = '{{ upi_link }}';
        const qrData = '{{ qr_url }}';
        
        document.getElementById('openBtn').addEventListener('click', () => {
            window.open(upiLink, '_blank');
            showStatus('📱 Opening UPI app...', 'success');
        });
        
        document.getElementById('copyLinkBtn').addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(window.location.href);
                showStatus('✅ Link copied!', 'success');
            } catch (err) {
                const textarea = document.createElement('textarea');
                textarea.value = window.location.href;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showStatus('✅ Link copied!', 'success');
            }
        });
        
        document.getElementById('downloadBtn').addEventListener('click', () => {
            const link = document.createElement('a');
            link.download = 'upi_payment_qr.png';
            link.href = qrData;
            link.click();
            showStatus('💾 QR Downloaded!', 'success');
        });
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
            setTimeout(() => {
                if (status.className === 'status ' + type) {
                    status.className = 'status';
                }
            }, 4000);
        }
    </script>
</body>
</html>
'''

# ============== HELPER FUNCTIONS ==============
def generate_order_id(upi_id, amount, name):
    timestamp = str(int(time.time()))
    data = f"{upi_id}{amount}{name}{timestamp}"
    return f"ORD{hashlib.md5(data.encode()).hexdigest()[:8].upper()}"

def validate_upi_id(upi_id):
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+$'
    return re.match(pattern, upi_id) is not None

def validate_amount(amount):
    try:
        val = float(amount)
        return val >= 0
    except ValueError:
        return False

def generate_payment_data(upi_id, amount, name):
    """Generate QR and payment data"""
    # Build UPI link
    upi_link = f"upi://pay?pa={upi_id}"
    if name:
        upi_link += f"&pn={urllib.parse.quote(name)}"
    if amount:
        upi_link += f"&am={amount}"
    upi_link += "&cu=INR"
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    qr_url = f"data:image/png;base64,{qr_base64}"
    
    return {
        'upi_link': upi_link,
        'qr_url': qr_url,
        'qr_base64': qr_base64
    }

# ============== ROUTES ==============

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UPI QR API</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                margin: 0;
                color: white;
            }
            .container {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border-radius: 28px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
                border: 1px solid rgba(255,255,255,0.1);
            }
            h1 { 
                background: linear-gradient(135deg, #ff0080, #ff8c00, #40e0d0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 32px;
            }
            .endpoint {
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 12px;
                margin: 10px 0;
                border: 1px solid rgba(255,255,255,0.05);
            }
            .endpoint code {
                color: #40e0d0;
                word-break: break-all;
            }
            .badge {
                display: inline-block;
                background: rgba(255,0,128,0.2);
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                color: #ff0080;
            }
            .example {
                background: rgba(0,0,0,0.3);
                padding: 10px;
                border-radius: 8px;
                font-size: 13px;
                color: #a0aec0;
                margin-top: 5px;
            }
            .highlight {
                background: rgba(255,200,0,0.1);
                border: 1px solid rgba(255,200,0,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ UPI QR API</h1>
            <p style="color: rgba(255,255,255,0.6);">Generate UPI QR codes via API or direct page</p>
            
            <h3 style="margin-top: 30px;">📌 API Endpoints (JSON Response)</h3>
            
            <div class="endpoint">
                <div><span class="badge">GET</span> <code>/pay/upi_id/amount/name</code></div>
                <div class="example">Example: /pay/9304619487%40fam/99/mdnooralam</div>
            </div>
            
            <h3 style="margin-top: 30px;">📱 Direct QR Page (Beautiful UI)</h3>
            
            <div class="endpoint highlight">
                <div><span class="badge" style="background:rgba(255,200,0,0.2);color:#ffc800;">GET</span> <code style="color:#ffc800;">/qr/upi_id/amount/name</code></div>
                <div class="example">Example: <strong>/qr/9304619487@fam/99/mdnooralam</strong></div>
                <div style="margin-top:8px;font-size:12px;color:rgba(255,255,255,0.3);">
                    ✨ Direct QR with glow animation, amount, and name
                </div>
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: rgba(255,255,255,0.3); font-size: 13px;">
                🔗 Works with every UPI app
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/qr/<path:upi_id>/<path:amount>/<path:name>')
def direct_qr_page(upi_id, amount, name):
    """Direct QR display page with beautiful UI"""
    try:
        upi_id = urllib.parse.unquote(upi_id)
        amount = urllib.parse.unquote(amount)
        name = urllib.parse.unquote(name)
        
        # Validate
        if not validate_upi_id(upi_id):
            return "Invalid UPI ID format", 400
        
        if not validate_amount(amount):
            return "Invalid amount", 400
        
        # Generate payment data
        data = generate_payment_data(upi_id, amount, name)
        
        return render_template_string(
            QR_PAGE,
            upi_id=upi_id,
            amount=amount,
            name=name,
            qr_url=data['qr_url'],
            upi_link=data['upi_link']
        )
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/pay/<path:upi_id>/<path:amount>/<path:name>')
def payment_api_full(upi_id, amount, name):
    """JSON API endpoint"""
    try:
        upi_id = urllib.parse.unquote(upi_id)
        amount = urllib.parse.unquote(amount)
        name = urllib.parse.unquote(name)
        
        if not validate_upi_id(upi_id):
            return jsonify({'status': 'error', 'message': 'Invalid UPI ID'}), 400
        
        if not validate_amount(amount):
            return jsonify({'status': 'error', 'message': 'Invalid amount'}), 400
        
        order_id = generate_order_id(upi_id, amount, name)
        data = generate_payment_data(upi_id, amount, name)
        
        expires_at = datetime.now() + timedelta(hours=24)
        
        orders[order_id] = {
            'upi_id': upi_id,
            'amount': amount,
            'name': name,
            'upi_link': data['upi_link'],
            'qr_data': data['qr_base64'],
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'order_id': order_id,
                'qr_url': data['qr_url'],
                'upi_id': upi_id,
                'amount': amount,
                'name': name,
                'upi_link': data['upi_link'],
                'expires_at': expires_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/pay/<path:upi_id>/<path:amount>')
def payment_api_amount(upi_id, amount):
    return payment_api_full(upi_id, amount, '')

@app.route('/pay/<path:upi_id>')
def payment_api_basic(upi_id):
    return payment_api_full(upi_id, '0.00', '')

@app.route('/order/<order_id>')
def get_order(order_id):
    order = orders.get(order_id)
    if not order:
        return jsonify({'status': 'error', 'message': 'Order not found'}), 404
    return jsonify({'status': 'success', 'data': order})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
