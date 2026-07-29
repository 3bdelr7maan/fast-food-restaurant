import os
from flask import Flask

app = Flask(__name__)
app.secret_key = 'super_secret_restaurant_key_change_this_in_production'

TELEGRAM_TOKEN = '8868529974:AAHW-YFlsG45rV2iEGdZOLEqLEbfu56Cczg' # ضع التوكين الخاص بك هنا

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# قواعد البيانات المؤقتة في الذاكرة
users_db = {}     # تخزين المستخدمين {username: {password, role}}
orders_db = []    # الطلبات الواردة
sessions = {}     # جلسات التليجرام

CATEGORIES = {
    "cat_offers": {"name": "🔥 العروض والوجبات الكاملة", "icon": "🍱"},
    "cat_grills": {"name": "🥩 مشويات بالكيلو والوزن", "icon": "🥩"},
    "cat_plates": {"name": "🍽️ أطباق فردية وميكس", "icon": "🍽️"}
}

MENU_ITEMS = {
    "item_1": {
        "title": "كيلو كفتة ضاني مخصوص", 
        "price": 420, 
        "unit": "كيلو",
        "category": "cat_grills",
        "image": "",
        "available": True
    }
}