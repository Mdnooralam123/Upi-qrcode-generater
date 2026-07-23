# app.py - Complete UPI QR Generator with Payment Page
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import qrcode
import io
import base64
import urllib.parse
import json
import hashlib

app = Flask(__name__)

# Store payment data temporarily (in production use database)
payment_data = {}

# Main Page HTML
MAIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KHAN UPI - Premium QR Generator</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Orbitron', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            position: relative;
            overflow: hidden;
        }
        
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
            max-width: 500px;
            width: 100%;
            padding: 32px;
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
            font-size: 34px;
            font-weight: 900;
            letter-spacing: 2px;
            background: linear-gradient(135deg, #ff0080, #ff8c00, #40e0d0, #ff0080);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 4s ease-in-out infinite;
            text-shadow: 0 0 40px rgba(255, 0, 128, 0.3);
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .header .subtitle {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 6px;
            letter-spacing: 3px;
            font-weight: 400;
        }
        
        .form-group {
            margin-top: 20px;
        }
        
        .form-group label {
            display: block;
            font-size: 11px;
            font-weight: 700;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 8px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        
        .form-group label span {
            color: rgba(255, 255, 255, 0.3);
            font-weight: 400;
        }
        
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 14px 18px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            font-size: 15px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            font-family: inherit;
            backdrop-filter: blur(10px);
        }
        
        .form-group input::placeholder, .form-group textarea::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }
        
        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: #ff0080;
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 30px rgba(255, 0, 128, 0.15), inset 0 0 30px rgba(255, 0, 128, 0.05);
            transform: scale(1.02);
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 50px;
        }
        
        .btn-primary {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #ff0080, #ff8c00);
            color: white;
            border: none;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 700;
            margin-top: 24px;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            letter-spacing: 1px;
            font-family: inherit;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 15px 40px rgba(255, 0, 128, 0.4), 0 0 60px rgba(255, 0, 128, 0.2);
        }
        
        .btn-primary:active {
            transform: scale(0.95);
        }
        
        .btn-primary::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.15), transparent);
            transform: rotate(45deg) translateX(-100%);
            transition: 0.8s;
        }
        
        .btn-primary:hover::before {
            transform: rotate(45deg) translateX(100%);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }
        
        .btn-primary span {
            position: relative;
            z-index: 2;
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
            width: 100%;
        }
        
        .btn-secondary:hover {
            transform: translateY(-3px) scale(1.05);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .btn-secondary:active {
            transform: scale(0.93);
        }
        
        .btn-copy-link {
            background: linear-gradient(135deg, rgba(251, 188, 4, 0.2), rgba(249, 171, 0, 0.2));
            border-color: rgba(251, 188, 4, 0.2);
            color: #fbbc04;
        }
        
        .btn-copy-link:hover {
            background: linear-gradient(135deg, rgba(251, 188, 4, 0.4), rgba(249, 171, 0, 0.4));
            box-shadow: 0 10px 30px rgba(251, 188, 4, 0.2);
            border-color: #fbbc04;
        }
        
        .link-container {
            margin-top: 16px;
            padding: 14px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            display: none;
        }
        
        .link-container.show {
            display: block;
            animation: slideUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        .link-container .link-label {
            font-size: 10px;
            color: rgba(255, 255, 255, 0.3);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        
        .link-container .link-box {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .link-container .link-box input {
            flex: 1;
            padding: 10px 14px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
            font-family: inherit;
            cursor: pointer;
        }
        
        .link-container .link-box input:focus {
            outline: none;
            border-color: #ff0080;
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
        
        .spinner {
            display: none;
            width: 40px;
            height: 40px;
            margin: 20px auto 0;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #ff0080;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            box-shadow: 0 0 30px rgba(255, 0, 128, 0.2);
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, rgba(255, 0, 128, 0.2), rgba(64, 224, 208, 0.2));
            color: rgba(255, 255, 255, 0.6);
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 10px;
            margin-top: 18px;
            font-weight: 700;
            border: 1px solid rgba(255, 255, 255, 0.05);
            letter-spacing: 1px;
            backdrop-filter: blur(10px);
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 20px;
                border-radius: 24px;
            }
            
            .header h1 {
                font-size: 28px;
            }
            
            .link-container .link-box {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    
    <div class="container">
        <div class="header">
            <h1>⚡ KHAN UPI</h1>
            <div class="subtitle">✦ PREMIUM PAYMENT REQUEST ✦</div>
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
                <input type="text" id="amount" placeholder="0.00" value="">
            </div>
            
            <div class="form-group">
                <label>Note <span>(optional)</span></label>
                <textarea id="note" placeholder="Payment for..."></textarea>
            </div>
            
            <button type="submit" class="btn-primary" id="generateBtn">
                <span>✨ GENERATE QR</span>
            </button>
        </form>
        
        <div class="spinner" id="spinner"></div>
        
        <div class="link-container" id="linkContainer">
            <div class="link-label">✦ SHAREABLE PAYMENT LINK</div>
            <div class="link-box">
                <input type="text" id="paymentLink" readonly>
                <button class="btn-secondary btn-copy-link" id="copyLinkBtn">📋 COPY</button>
            </div>
        </div>
        
        <div id="status" class="status"></div>
        
        <div style="text-align: center;">
            <div class="badge">✦ WORKS WITH EVERY UPI APP ✦</div>
        </div>
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
        
        document.getElementById('qrForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const upiId = document.getElementById('upiId').value.trim();
            const name = document.getElementById('payeeName').value.trim();
            const amount = document.getElementById('amount').value.trim();
            const note = document.getElementById('note').value.trim();
            
            if (!upiId) {
                showStatus('⚠️ Please enter a UPI ID', 'error');
                return;
            }
            
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').querySelector('span').textContent = '⏳ GENERATING...';
            document.getElementById('linkContainer').classList.remove('show');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ upiId, name, amount, note })
                });
                
                const data = await response.json();
                
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('generateBtn').querySelector('span').textContent = '✨ GENERATE QR';
                
                if (data.success) {
                    // Show the payment link
                    const linkInput = document.getElementById('paymentLink');
                    const fullUrl = window.location.origin + '/pay/' + data.paymentId;
                    linkInput.value = fullUrl;
                    document.getElementById('linkContainer').classList.add('show');
                    
                    showStatus('✅ Payment link generated! Share it with anyone.', 'success');
                } else {
                    showStatus('❌ ' + (data.error || 'Failed to generate'), 'error');
                }
            } catch (error) {
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('generateBtn').querySelector('span').textContent = '✨ GENERATE QR';
                showStatus('❌ Error: ' + error.message, 'error');
            }
        });
        
        document.getElementById('copyLinkBtn').addEventListener('click', async () => {
            const linkInput = document.getElementById('paymentLink');
            if (!linkInput.value) {
                showStatus('⚠️ Generate a link first', 'error');
                return;
            }
            
            try {
                await navigator.clipboard.writeText(linkInput.value);
                showStatus('✅ Link copied!', 'success');
            } catch (err) {
                linkInput.select();
                document.execCommand('copy');
                showStatus('✅ Link copied!', 'success');
            }
        });
        
        // Click on link input to select
        document.getElementById('paymentLink').addEventListener('click', function() {
            this.select();
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
    </script>
</body>
</html>
'''

# Payment Page HTML
PAYMENT_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KHAN UPI - Payment Request</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Orbitron', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            position: relative;
            overflow: hidden;
        }
        
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
        
        .not-found {
            text-align: center;
            padding: 40px 20px;
        }
        
        .not-found .icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        .not-found h2 {
            color: rgba(255, 255, 255, 0.8);
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .not-found p {
            color: rgba(255, 255, 255, 0.4);
            font-size: 14px;
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
        {% if payment %}
        <div class="header">
            <h1>⚡ KHAN UPI</h1>
            <div class="subtitle">✦ PAYMENT REQUEST ✦</div>
        </div>
        
        <div class="payment-info">
            <div class="amount-label">AMOUNT</div>
            <div class="amount">₹{{ payment.amount if payment.amount else '0.00' }}</div>
            {% if payment.name %}
            <div class="name">✦ {{ payment.name }} ✦</div>
            {% endif %}
            {% if payment.note %}
            <div class="note">📝 {{ payment.note }}</div>
            {% endif %}
            <div class="upi-id">📱 {{ payment.upi_id }}</div>
        </div>
        
        <div style="text-align: center;">
            <div class="qr-wrapper">
                <div class="qr-container glow scanning" id="qrContainer">
                    <div class="corner tl"></div>
                    <div class="corner tr"></div>
                    <div class="corner bl"></div>
                    <div class="corner br"></div>
                    <img src="data:image/png;base64,{{ payment.qr_data }}" alt="QR Code">
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
            
            const upiLink = '{{ payment.upi_link }}';
            const qrData = '{{ payment.qr_data }}';
            
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
                link.download = 'khan_upi_payment.png';
                link.href = `data:image/png;base64,${qrData}`;
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
        {% else %}
        <div class="not-found">
            <div class="icon">🔗</div>
            <h2>Payment Not Found</h2>
            <p>The payment link you're trying to access has expired or doesn't exist.</p>
            <br>
            <button class="btn-secondary" onclick="window.location.href='/'" style="display: inline-block; padding: 12px 30px;">
                🏠 Create New Payment
            </button>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(MAIN_PAGE)

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
        
        # Validate amount
        if amount:
            try:
                float(amount)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid amount'})
        
        # Build UPI link
        upi_link = f"upi://pay?pa={upi_id}"
        if name:
            upi_link += f"&pn={urllib.parse.quote(name)}"
        if amount:
            upi_link += f"&am={amount}"
        if note:
            upi_link += f"&tn={urllib.parse.quote(note)}"
        upi_link += "&cu=INR"
        
        # Generate QR
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
        
        # Create unique payment ID
        payment_id = hashlib.md5(f"{upi_id}{name}{amount}{note}".encode()).hexdigest()[:12]
        
        # Store payment data
        payment_data[payment_id] = {
            'upi_id': upi_id,
            'name': name,
            'amount': amount,
            'note': note,
            'upi_link': upi_link,
            'qr_data': img_base64
        }
        
        return jsonify({
            'success': True,
            'paymentId': payment_id,
            'upiLink': upi_link
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pay/<payment_id>')
def payment_page(payment_id):
    payment = payment_data.get(payment_id)
    return render_template_string(PAYMENT_PAGE, payment=payment)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)