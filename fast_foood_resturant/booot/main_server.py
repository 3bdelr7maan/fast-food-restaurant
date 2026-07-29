import threading
from config import app
import dashboard_routes  # تحميل مسارات الداشبورد
import auth_routes       # <--- السطر ده هو اللي كان ناقص وبيسبب خطأ 404!
from bot_handler import start_bot  # تحميل البوت

bot = start_bot()

if __name__ == '__main__':
    # تشغيل البوت في مسار منفصل (Thread)
    polling_thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    polling_thread.start()
    
    print("🚀 Server is running on http://127.0.0.1:5000")
    print("📊 Advanced Cashier Dashboard is Live!")
    
    # تشغيل سيرفر الويب Flask
    app.run(host='0.0.0.0', port=5000, debug=False)