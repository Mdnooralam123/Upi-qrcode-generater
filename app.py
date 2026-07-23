# app.py - UPI QR Generator with JSON API Response
from flask import Flask, jsonify, request
import qrcode
import io
import base64
import urllib.parse
import hashlib
import time
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Store order data (in production, use database)
orders = {}

def generate_order_id(upi_id, amount, name):
    """Generate unique order ID"""
    timestamp = str(int(time.time()))
    data = f"{upi_id}{amount}{name}{timestamp}"
    return f"ORD{hashlib.md5(data.encode()).hexdigest()[:8].upper()}"

def validate_upi_id(upi_id):
    """Validate UPI ID format"""
    # Basic UPI ID validation
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+$'
    return re.match(pattern, upi_id) is not None

def validate_amount(amount):
    """Validate amount is a valid number"""
    try:
        val = float(amount)
        return val >= 0
    except ValueError:
        return False

@app.route('/pay/<path:upi_id>/<path:amount>/<path:name>')
def payment_api_full(upi_id, amount, name):
    """
    API endpoint: /pay/upi_id/amount/name
    Returns JSON response with QR code and payment details
    """
    try:
        # URL decode parameters
        upi_id = urllib.parse.unquote(upi_id)
        amount = urllib.parse.unquote(amount)
        name = urllib.parse.unquote(name)
        
        # Validate parameters
        if not validate_upi_id(upi_id):
            return jsonify({
                'status': 'error',
                'message': 'Invalid UPI ID format. Use: username@bank'
            }), 400
        
        if not validate_amount(amount):
            return jsonify({
                'status': 'error',
                'message': 'Invalid amount. Please enter a valid number'
            }), 400
        
        # Generate order ID
        order_id = generate_order_id(upi_id, amount, name)
        
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
        
        # Convert QR to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Generate QR URL (data URL)
        qr_url = f"data:image/png;base64,{qr_base64}"
        
        # Set expiration (24 hours from now)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Store order data
        orders[order_id] = {
            'upi_id': upi_id,
            'amount': amount,
            'name': name,
            'upi_link': upi_link,
            'qr_data': qr_base64,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        # Return JSON response
        return jsonify({
            'status': 'success',
            'data': {
                'order_id': order_id,
                'qr_url': qr_url,
                'upi_id': upi_id,
                'amount': amount,
                'name': name,
                'upi_link': upi_link,
                'expires_at': expires_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/pay/<path:upi_id>/<path:amount>')
def payment_api_amount(upi_id, amount):
    """
    API endpoint: /pay/upi_id/amount
    Returns JSON with QR code and payment details (without name)
    """
    return payment_api_full(upi_id, amount, '')

@app.route('/pay/<path:upi_id>')
def payment_api_basic(upi_id):
    """
    API endpoint: /pay/upi_id
    Returns JSON with QR code and payment details (without amount and name)
    """
    return payment_api_full(upi_id, '0.00', '')

@app.route('/order/<order_id>')
def get_order(order_id):
    """
    Get order details by order ID
    """
    order = orders.get(order_id)
    if not order:
        return jsonify({
            'status': 'error',
            'message': 'Order not found or expired'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': order
    })

@app.route('/')
def index():
    """Simple HTML page with instructions"""
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ UPI QR API</h1>
            <p style="color: rgba(255,255,255,0.6);">Generate UPI QR codes via API</p>
            
            <h3 style="margin-top: 30px;">📌 API Endpoints</h3>
            
            <div class="endpoint">
                <div><span class="badge">GET</span> <code>/pay/upi_id/amount/name</code></div>
                <div class="example">Example: /pay/example%40bank/100/John%20Doe</div>
            </div>
            
            <div class="endpoint">
                <div><span class="badge">GET</span> <code>/pay/upi_id/amount</code></div>
                <div class="example">Example: /pay/example%40bank/100</div>
            </div>
            
            <div class="endpoint">
                <div><span class="badge">GET</span> <code>/pay/upi_id</code></div>
                <div class="example">Example: /pay/example%40bank</div>
            </div>
            
            <div class="endpoint">
                <div><span class="badge">GET</span> <code>/order/order_id</code></div>
                <div class="example">Example: /order/ORDABC123</div>
            </div>
            
            <h3 style="margin-top: 30px;">📝 Response Format</h3>
            <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; font-size: 12px;">
<pre style="color: #a0aec0; margin: 0;">
{
  "status": "success",
  "data": {
    "order_id": "ORD...",
    "qr_url": "data:image/png;base64,...",
    "upi_id": "example@bank",
    "amount": "100",
    "name": "John Doe",
    "upi_link": "upi://pay?pa=...",
    "expires_at": "2026-04-23T00:46:00+05:30"
  }
}
</pre>
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: rgba(255,255,255,0.3); font-size: 13px;">
                🔗 Works with every UPI app
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)