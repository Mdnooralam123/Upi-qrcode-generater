# app.py - Premium UPI QR Generator with Animations
from flask import Flask, render_template_string, request, jsonify
import qrcode
import io
import base64
import urllib.parse
import time

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>UPIPE - UPI QR Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background-image: 
                radial-gradient(ellipse at 10% 20%, rgba(102, 126, 234, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 90% 80%, rgba(118, 75, 162, 0.05) 0%, transparent 50%);
        }
        
        .container {
            background: #ffffff;
            border-radius: 28px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08), 0 8px 20px rgba(0, 0, 0, 0.02);
            max-width: 480px;
            width: 100%;
            padding: 32px;
            transition: all 0.3s ease;
        }
        
        .header {
            text-align: center;
            padding-bottom: 24px;
            border-bottom: 1px solid #f0f2f5;
        }
        
        .header h1 {
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            color: #8892a0;
            font-size: 14px;
            margin-top: 4px;
            font-weight: 500;
            -webkit-text-fill-color: #8892a0;
        }
        
        .form-group {
            margin-top: 18px;
        }
        
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 6px;
            letter-spacing: 0.3px;
        }
        
        .form-group label span {
            color: #a0aec0;
            font-weight: 400;
        }
        
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 14px;
            font-size: 15px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            background: #f7fafc;
            color: #2d3748;
        }
        
        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.08);
            transform: scale(1.01);
        }
        
        .form-group input::placeholder, .form-group textarea::placeholder {
            color: #a0aec0;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 56px;
            font-family: inherit;
        }
        
        .btn-primary {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 700;
            margin-top: 24px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            letter-spacing: 0.5px;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(102, 126, 234, 0.35);
        }
        
        .btn-primary:active {
            transform: scale(0.97);
        }
        
        .btn-primary::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.12), transparent);
            transform: rotate(45deg) translateX(-100%);
            transition: 0.8s;
        }
        
        .btn-primary:hover::after {
            transform: rotate(45deg) translateX(100%);
        }
        
        .btn-primary:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none !important;
        }
        
        .qr-section {
            margin-top: 28px;
            padding-top: 28px;
            border-top: 1px solid #f0f2f5;
            text-align: center;
            opacity: 0;
            transform: translateY(30px) scale(0.95);
            transition: all 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
            display: none;
        }
        
        .qr-section.show {
            opacity: 1;
            transform: translateY(0) scale(1);
            display: block;
        }
        
        .qr-wrapper {
            position: relative;
            display: inline-block;
            padding: 8px;
        }
        
        .qr-container {
            background: white;
            padding: 24px;
            border-radius: 20px;
            display: inline-block;
            position: relative;
            min-height: 220px;
            min-width: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #f0f2f5;
            transition: all 0.5s ease;
        }
        
        .qr-container.glow {
            animation: glowPulse 2.5s ease-in-out infinite;
            border-color: #667eea;
        }
        
        @keyframes glowPulse {
            0% {
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.2);
            }
            50% {
                box-shadow: 0 0 40px 10px rgba(102, 126, 234, 0.15), 0 0 80px 20px rgba(102, 126, 234, 0.05);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.2);
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
                transform: scale(0.3) rotate(-8deg);
            }
            60% {
                transform: scale(1.05) rotate(1deg);
            }
            100% {
                opacity: 1;
                transform: scale(1) rotate(0deg);
            }
        }
        
        /* Scanning animation overlay */
        .qr-container.scanning::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
            animation: scanLine 2s ease-in-out infinite;
            z-index: 3;
            border-radius: 20px;
        }
        
        @keyframes scanLine {
            0% {
                top: 0;
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                top: 100%;
                opacity: 0;
            }
        }
        
        .qr-placeholder {
            color: #a0aec0;
            font-size: 15px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
        
        .payment-info {
            margin-top: 20px;
        }
        
        .payment-info .amount {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }
        
        .payment-info .name {
            font-size: 16px;
            color: #4a5568;
            margin-top: 4px;
            font-weight: 500;
        }
        
        .payment-info .subtitle {
            font-size: 13px;
            color: #a0aec0;
            margin-top: 2px;
        }
        
        .actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn-secondary {
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        
        .btn-secondary:active {
            transform: scale(0.95);
        }
        
        .btn-open {
            background: #48bb78;
            color: white;
        }
        
        .btn-open:hover {
            background: #38a169;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(72, 187, 120, 0.3);
        }
        
        .btn-copy {
            background: #edf2f7;
            color: #2d3748;
        }
        
        .btn-copy:hover {
            background: #e2e8f0;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
        }
        
        .btn-download {
            background: #ebf4ff;
            color: #4299e1;
        }
        
        .btn-download:hover {
            background: #dbeafe;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(66, 153, 225, 0.2);
        }
        
        .btn-clear-action {
            background: #f7fafc;
            color: #718096;
        }
        
        .btn-clear-action:hover {
            background: #edf2f7;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04);
        }
        
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, #ebf4ff 0%, #e0e7ff 100%);
            color: #4a5568;
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 12px;
            margin-top: 16px;
            font-weight: 600;
            border: 1px solid #e2e8f0;
        }
        
        .status {
            margin-top: 16px;
            padding: 14px;
            border-radius: 12px;
            font-size: 14px;
            text-align: center;
            display: none;
            animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            font-weight: 500;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .status.success {
            display: block;
            background: #f0fff4;
            color: #22543d;
            border: 1px solid #c6f6d5;
        }
        
        .status.error {
            display: block;
            background: #fff5f5;
            color: #9b2c2c;
            border: 1px solid #fed7d7;
        }
        
        .status.processing {
            display: block;
            background: #ebf8ff;
            color: #2a69ac;
            border: 1px solid #bee3f8;
            animation: processingPulse 1.5s ease-in-out infinite;
        }
        
        @keyframes processingPulse {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
        }
        
        .spinner {
            display: none;
            width: 36px;
            height: 36px;
            margin: 16px auto 0;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Payment processing bar */
        .processing-bar {
            display: none;
            margin-top: 16px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
            border-radius: 12px;
            border: 1px solid #c6f6d5;
        }
        
        .processing-bar.show {
            display: block;
            animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        .processing-bar .bar-title {
            font-size: 14px;
            font-weight: 600;
            color: #22543d;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .processing-bar .bar-track {
            margin-top: 8px;
            width: 100%;
            height: 6px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .processing-bar .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            border-radius: 10px;
            width: 0%;
            transition: width 0.5s ease;
            animation: fillBar 3s ease-in-out forwards;
        }
        
        @keyframes fillBar {
            0% { width: 0%; }
            30% { width: 30%; }
            60% { width: 65%; }
            85% { width: 90%; }
            100% { width: 100%; }
        }
        
        .processing-bar .bar-status {
            font-size: 12px;
            color: #48bb78;
            margin-top: 6px;
            font-weight: 500;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 20px;
                border-radius: 20px;
            }
            
            .actions {
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .header h1 {
                font-size: 28px;
            }
            
            .payment-info .amount {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>UPIPE</h1>
            <p>UPI Payment Request</p>
        </div>
        
        <form id="qrForm">
            <div class="form-group">
                <label>UPI ID</label>
                <input type="text" id="upiId" placeholder="yourname@bank" required>
            </div>
            
            <div class="form-group">
                <label>Your Name <span>(optional)</span></label>
                <input type="text" id="payeeName" placeholder="Enter your name">
            </div>
            
            <div class="form-group">
                <label>Amount (₹)</label>
                <input type="text" id="amount" placeholder="0.00" value="0.00">
            </div>
            
            <div class="form-group">
                <label>Note <span>(optional)</span></label>
                <textarea id="note" placeholder="Payment for..."></textarea>
            </div>
            
            <button type="submit" class="btn-primary" id="generateBtn">
                ✨ Generate QR
            </button>
        </form>
        
        <div class="spinner" id="spinner"></div>
        
        <!-- Processing Payment Bar -->
        <div class="processing-bar" id="processingBar">
            <div class="bar-title">
                <span>🔄</span> Processing Payment
            </div>
            <div class="bar-track">
                <div class="bar-fill" id="barFill"></div>
            </div>
            <div class="bar-status" id="barStatus">Initializing...</div>
        </div>
        
        <div class="qr-section" id="qrSection">
            <div class="qr-wrapper">
                <div class="qr-container" id="qrContainer">
                    <div class="qr-placeholder">✨ Your QR will appear here</div>
                </div>
            </div>
            
            <div class="payment-info">
                <div class="amount" id="amountDisplay"></div>
                <div class="name" id="nameDisplay"></div>
                <div class="subtitle" id="subtitleDisplay"></div>
            </div>
            
            <div class="actions">
                <button class="btn-secondary btn-open" id="openBtn">📱 Open in UPI</button>
                <button class="btn-secondary btn-copy" id="copyBtn">📋 Copy Link</button>
                <button class="btn-secondary btn-download" id="downloadBtn">💾 Download QR</button>
                <button class="btn-secondary btn-clear-action" id="clearBtn">🗑️ Clear</button>
            </div>
            
            <div class="badge">✨ Works with every UPI app</div>
        </div>
        
        <div id="status" class="status"></div>
    </div>
    
    <script>
        let currentUpiLink = '';
        let currentQrData = '';
        let qrGenerated = false;
        
        document.getElementById('qrForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const upiId = document.getElementById('upiId').value.trim();
            const name = document.getElementById('payeeName').value.trim();
            const amount = document.getElementById('amount').value.trim();
            const note = document.getElementById('note').value.trim();
            
            if (!upiId) {
                showStatus('Please enter a UPI ID', 'error');
                return;
            }
            
            // Show spinner
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = '⏳ Generating...';
            
            // Hide previous QR section
            document.getElementById('qrSection').classList.remove('show');
            document.getElementById('qrSection').style.display = 'none';
            document.getElementById('processingBar').classList.remove('show');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ upiId, name, amount, note })
                });
                
                const data = await response.json();
                
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('generateBtn').textContent = '✨ Generate QR';
                
                if (data.success) {
                    currentUpiLink = data.upiLink;
                    currentQrData = data.qrData;
                    qrGenerated = true;
                    
                    // Display QR with glow
                    const qrContainer = document.getElementById('qrContainer');
                    qrContainer.innerHTML = `
                        <img src="data:image/png;base64,${data.qrData}" alt="QR Code" id="qrImage">
                    `;
                    
                    // Show QR section with animation
                    const qrSection = document.getElementById('qrSection');
                    qrSection.style.display = 'block';
                    
                    // Trigger show animation after a tiny delay
                    setTimeout(() => {
                        qrSection.classList.add('show');
                    }, 50);
                    
                    // Add glow and scanning animation
                    setTimeout(() => {
                        qrContainer.classList.add('glow');
                        qrContainer.classList.add('scanning');
                    }, 200);
                    
                    // Display payment info
                    if (data.amount && data.amount !== '0.00') {
                        document.getElementById('amountDisplay').textContent = `₹${data.amount}`;
                    } else {
                        document.getElementById('amountDisplay').textContent = '';
                    }
                    
                    if (data.name) {
                        document.getElementById('nameDisplay').textContent = `to ${data.name}`;
                    } else {
                        document.getElementById('nameDisplay').textContent = '';
                    }
                    
                    document.getElementById('subtitleDisplay').textContent = 'Scan to pay securely';
                    
                    // Show processing bar after QR appears
                    setTimeout(() => {
                        showProcessingBar();
                    }, 800);
                    
                    showStatus('✅ QR generated successfully!', 'success');
                    
                    // Remove glow after 6 seconds
                    setTimeout(() => {
                        qrContainer.classList.remove('glow');
                        qrContainer.classList.remove('scanning');
                    }, 6000);
                    
                } else {
                    showStatus('❌ ' + (data.error || 'Failed to generate QR'), 'error');
                }
            } catch (error) {
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('generateBtn').textContent = '✨ Generate QR';
                showStatus('❌ Error: ' + error.message, 'error');
            }
        });
        
        function showProcessingBar() {
            const bar = document.getElementById('processingBar');
            bar.classList.add('show');
            
            const statuses = [
                'Initializing payment...',
                'Connecting to UPI...',
                'Verifying payee...',
                'Payment ready!'
            ];
            
            let index = 0;
            const statusEl = document.getElementById('barStatus');
            
            const interval = setInterval(() => {
                if (index < statuses.length) {
                    statusEl.textContent = statuses[index];
                    index++;
                } else {
                    clearInterval(interval);
                    statusEl.textContent = '✅ Payment link ready!';
                }
            }, 800);
            
            // Reset bar fill for new animation
            const barFill = document.getElementById('barFill');
            barFill.style.animation = 'none';
            barFill.offsetHeight; // Trigger reflow
            barFill.style.animation = 'fillBar 3s ease-in-out forwards';
        }
        
        document.getElementById('openBtn').addEventListener('click', () => {
            if (!qrGenerated) {
                showStatus('Please generate a QR first', 'error');
                return;
            }
            window.open(currentUpiLink, '_blank');
            showStatus('📱 Opening UPI app...', 'success');
        });
        
        document.getElementById('copyBtn').addEventListener('click', async () => {
            if (!qrGenerated) {
                showStatus('Please generate a QR first', 'error');
                return;
            }
            
            try {
                await navigator.clipboard.writeText(currentUpiLink);
                showStatus('✅ Link copied to clipboard!', 'success');
            } catch (err) {
                const textarea = document.createElement('textarea');
                textarea.value = currentUpiLink;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showStatus('✅ Link copied to clipboard!', 'success');
            }
        });
        
        document.getElementById('downloadBtn').addEventListener('click', () => {
            if (!qrGenerated) {
                showStatus('Please generate a QR first', 'error');
                return;
            }
            
            const link = document.createElement('a');
            link.download = 'upi_qr.png';
            link.href = `data:image/png;base64,${currentQrData}`;
            link.click();
            showStatus('💾 QR downloaded!', 'success');
        });
        
        document.getElementById('clearBtn').addEventListener('click', () => {
            document.getElementById('upiId').value = '';
            document.getElementById('payeeName').value = '';
            document.getElementById('amount').value = '0.00';
            document.getElementById('note').value = '';
            document.getElementById('qrContainer').innerHTML = 
                '<div class="qr-placeholder">✨ Your QR will appear here</div>';
            document.getElementById('qrContainer').classList.remove('glow');
            document.getElementById('qrContainer').classList.remove('scanning');
            document.getElementById('amountDisplay').textContent = '';
            document.getElementById('nameDisplay').textContent = '';
            document.getElementById('subtitleDisplay').textContent = '';
            document.getElementById('qrSection').classList.remove('show');
            document.getElementById('qrSection').style.display = 'none';
            document.getElementById('processingBar').classList.remove('show');
            currentUpiLink = '';
            currentQrData = '';
            qrGenerated = false;
            hideStatus();
        });
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
            setTimeout(() => {
                if (status.className === 'status ' + type) {
                    status.className = 'status';
                }
            }, 5000);
        }
        
        function hideStatus() {
            const status = document.getElementById('status');
            status.className = 'status';
            status.textContent = '';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        upi_id = data.get('upiId', '').strip()
        name = data.get('name', '').strip()
        amount = data.get('amount', '').strip()
        note = data.get('note', '').strip()
        
        if not upi_id:
            return jsonify({'success': False, 'error': 'UPI ID is required'})
        
        if amount and amount != '0.00':
            try:
                float(amount)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid amount'})
        
        upi_link = f"upi://pay?pa={upi_id}"
        if name:
            upi_link += f"&pn={urllib.parse.quote(name)}"
        if amount and amount != '0.00':
            upi_link += f"&am={amount}"
        if note:
            upi_link += f"&tn={urllib.parse.quote(note)}"
        upi_link += "&cu=INR"
        
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
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'upiLink': upi_link,
            'qrData': img_base64,
            'amount': amount,
            'name': name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)