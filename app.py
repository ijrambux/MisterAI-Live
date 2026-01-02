import os
import random
import shutil
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "dz_connect_sovereign_2025"

# --- معالجة ذكية لمجلد الصوت لمنع توقف زر التسجيل ---
static_path = os.path.join(app.root_path, 'static')
audio_path = os.path.join(static_path, 'audio')

if not os.path.exists(static_path):
    os.makedirs(static_path)

# حذف الملف الخاطئ الذي يظهر في صورتك وتحويله لمجلد
if os.path.exists(audio_path) and not os.path.isdir(audio_path):
    os.remove(audio_path)

if not os.path.exists(audio_path):
    os.makedirs(audio_path)

app.config['UPLOAD_FOLDER'] = audio_path
chat_history = []

@app.route('/')
def index(): return render_template('index.html')

@app.route('/join')
def join(): return render_template('register.html')

@app.route('/verify')
def verify(): return render_template('verify.html')

@app.route('/settings')
def settings():
    if 'temp_nick' not in session: return redirect(url_for('join'))
    return render_template('settings.html')

@app.route('/hub')
def hub():
    if 'nickname' not in session: return redirect(url_for('join'))
    return render_template('hub.html')

# --- محرك التحقق (API) الذي يستقبله زر التسجيل ---
@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    nick = data.get('nickname', '').strip()
    phone = data.get('phone', '').strip()
    
    # تنظيف الرقم وتوحيده
    clean_phone = phone.replace('+213', '').replace(' ', '')
    if clean_phone.startswith('0'): clean_phone = clean_phone[1:]
    
    # شرط الرقم الجزائري
    is_valid = len(clean_phone) == 9 and clean_phone[0] in ['5', '6', '7']
    
    if not is_valid:
        return jsonify({"status": "error", "message": "Invalid Algerian Number!"}), 403

    # حماية اسمك المستعار
    if nick.lower() == "misterai" and clean_phone != "554014890": 
        return jsonify({"status": "error", "message": "Admin Reserved!"}), 403
    
    session['temp_nick'] = nick
    session['temp_phone'] = "+213" + clean_phone
    session['v_code'] = "1234"
    return jsonify({"status": "success", "url": "/verify"})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    if request.json.get('code') == session.get('v_code'):
        return jsonify({"status": "success", "url": "/settings"})
    return jsonify({"status": "error", "message": "Wrong Code!"}), 400

@app.route('/api/finalize', methods=['POST'])
def finalize():
    session['nickname'] = session.get('temp_nick')
    return jsonify({"status": "success", "url": "/hub"})

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user = session.get('nickname', 'Guest')
        is_admin = (user.lower() == "misterai")
        if request.is_json:
            msg = request.json.get('msg')
            if msg: chat_history.append({"user": user, "text": msg, "admin": is_admin, "type": "text"})
        elif 'audio' in request.files:
            audio_file = request.files['audio']
            filename = f"{user}_{random.randint(1000, 9999)}.webm"
            audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            chat_history.append({"user": user, "audio_url": f"/static/audio/{filename}", "admin": is_admin, "type": "audio"})
        if len(chat_history) > 30: chat_history.pop(0)
        return jsonify({"status": "ok"})
    return jsonify(chat_history)

if __name__ == '__main__':
    app.run(debug=True)
