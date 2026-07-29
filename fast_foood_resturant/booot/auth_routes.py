from flask import render_template, request, jsonify, session, redirect, url_for
from config import app, users_db

@app.route('/login', methods=['GET', 'POST'])
def login():
    has_admin = any(u.get('role') == 'admin' for u in users_db.values())

    if request.method == 'GET':
        # إذا كان مسجل دخول بالفعل، يدخل فوراً للوحة التحكم
        if 'user' in session:
            return redirect(url_for('cashier_dashboard'))
        return render_template('login.html', has_admin=has_admin)

    # معالجة بيانات الـ POST
    data = request.get_json(silent=True) or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "message": "يرجى كتابة اسم المستخدم وكلمة السر!"}), 400

    # 1. إنشاء حساب الآدمن الأول
    if not has_admin:
        users_db[username] = {
            "password": password,
            "role": "admin"
        }
        session['user'] = username
        session['role'] = 'admin'
        return jsonify({"success": True, "message": "تم إنشاء حساب الأدمن بنجاح!", "redirect": "/"})

    # 2. تسجيل الدخول للحسابات الحالية
    user = users_db.get(username)
    if user and user['password'] == password:
        session['user'] = username
        session['role'] = user['role']
        return jsonify({"success": True, "redirect": "/"})

    return jsonify({"success": False, "message": "اسم المستخدم أو كلمة السر غير صحيحة!"}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/users/add', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "غير مصرح لك بإضافة مستخدمين!"}), 403

    data = request.get_json(silent=True) or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'staff')

    if not username or not password:
        return jsonify({"success": False, "message": "بيانات غير مكتملة!"}), 400

    if username in users_db:
        return jsonify({"success": False, "message": "اسم المستخدم موجود بالفعل!"}), 400

    users_db[username] = {"password": password, "role": role}
    return jsonify({"success": True, "message": f"تم إضافة المستخدم {username} بنجاح!"})