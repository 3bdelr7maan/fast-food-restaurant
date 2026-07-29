import os
from flask import render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from config import app, CATEGORIES, MENU_ITEMS, orders_db, users_db

def check_auth():
    return 'user' in session

@app.route('/')
def cashier_dashboard():
    # 1. إذا لم يكن المستخدم مسجلاً، وجهه لصفحة تسجيل الدخول فوراً
    if not check_auth():
        return redirect(url_for('login'))
        
    return render_template(
        'dashboard.html', 
        current_user=session.get('user', 'مستخدم'), 
        role=session.get('role', 'staff')
    )

# --- APIs للطلبات ---

@app.route('/api/orders', methods=['GET'])
def get_orders():
    # إرجاع الطلبات من الأحدث للأقدم
    return jsonify(list(reversed(orders_db)))

# --- APIs للكتالوج والأصناف ---

@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(CATEGORIES)

@app.route('/api/categories/add', methods=['POST'])
def add_category():
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "غير مصرح!"}), 403
    data = request.get_json(silent=True) or request.form
    cat_name = data.get('name')
    cat_icon = data.get('icon', '📌')
    if cat_name:
        cat_id = f"cat_{len(CATEGORIES) + 1}"
        CATEGORIES[cat_id] = {"name": cat_name, "icon": cat_icon}
        return jsonify({"success": True, "cat_id": cat_id})
    return jsonify({"success": False, "message": "اسم القسم مطلوب!"}), 400

@app.route('/api/menu', methods=['GET'])
def get_menu():
    return jsonify(MENU_ITEMS)

@app.route('/api/menu/add', methods=['POST'])
def add_menu_item():
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "غير مصرح!"}), 403
        
    title = request.form.get('title', '').strip()
    price = request.form.get('price', 0)
    unit = request.form.get('unit', '').strip()
    category = request.form.get('category', '')
    
    image_file = request.files.get('image')
    image_filename = ""
    if image_file:
        filename = secure_filename(image_file.filename)
        upload_folder = os.path.join(app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        image_file.save(os.path.join(upload_folder, filename))
        image_filename = filename

    if title and price:
        item_id = f"item_{len(MENU_ITEMS) + 1}"
        MENU_ITEMS[item_id] = {
            "title": title,
            "price": float(price),
            "unit": unit,
            "category": category,
            "image": image_filename,
            "available": True
        }
        return jsonify({"success": True, "item_id": item_id})
    return jsonify({"success": False, "message": "اسم الصنف والسعر مطلوبان!"}), 400

@app.route('/api/menu/delete/<item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "غير مصرح!"}), 403
    if item_id in MENU_ITEMS:
        MENU_ITEMS[item_id]['available'] = False
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "الصنف غير موجود!"}), 404

@app.route('/uploads/<filename>')
def send_upload(filename):
    return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)