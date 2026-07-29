import telebot
from telebot import types
from datetime import datetime
from config import TELEGRAM_TOKEN, CATEGORIES, MENU_ITEMS, orders_db, sessions

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def start_bot():
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        chat_id = message.chat.id
        sessions[chat_id] = {"step": "WAITING_NAME", "cart": {}}
        
        welcome_msg = (
            "أهلاً بك في مطعم المشويات الفاخر! 🥩🔥\n"
            "يسعدنا خدمتك اليوم.\n\n"
            "عشان ننفذ طلبك بسرعة، ممكن نتعرف باسمك؟"
        )
        bot.send_message(chat_id, welcome_msg)

    @bot.message_handler(func=lambda msg: True)
    def handle_conversation(message):
        chat_id = message.chat.id
        text = message.text.strip()
        
        # خيار إعادة البداية من الخيارات أو الرسائل
        if text == "🔄 بداية جديدة / Restart":
            sessions[chat_id] = {"step": "WAITING_NAME", "cart": {}}
            bot.send_message(chat_id, "أهلاً بك من جديد! 🔄\nممكن نتعرف باسمك؟")
            return

        if chat_id not in sessions:
            sessions[chat_id] = {"step": "WAITING_NAME", "cart": {}}
            bot.send_message(chat_id, "أهلاً بك! ممكن نتعرف باسمك الأول؟")
            return
            
        step = sessions[chat_id].get("step")
        
        if step == "WAITING_NAME":
            sessions[chat_id]["name"] = text
            sessions[chat_id]["step"] = "WAITING_ADDRESS"
            bot.send_message(chat_id, f"أهلاً بك يا {text} ❤️\nممكن عنوان التوصيل بالتفصيل؟")
            
        elif step == "WAITING_ADDRESS":
            sessions[chat_id]["address"] = text
            sessions[chat_id]["step"] = "WAITING_PHONE"
            bot.send_message(chat_id, "تمام جداً! برجاء تزويدنا برقم الموبايل للتواصل عند التوصيل:")
            
        elif step == "WAITING_PHONE":
            sessions[chat_id]["phone"] = text
            sessions[chat_id]["step"] = "BROWSING_MENU"
            send_categories_menu(chat_id)

    def send_categories_menu(chat_id, text_prefix=""):
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for cat_id, cat_info in CATEGORIES.items():
            btn_text = f"{cat_info['icon']} {cat_info['name']}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"show_cat_{cat_id}"))
            
        markup.add(types.InlineKeyboardButton("🛒 عرض السلة وتأكيد الطلب", callback_data="view_cart"))
        markup.add(types.InlineKeyboardButton("🔄 بداية جديدة / Restart", callback_data="restart_flow"))
        
        msg_text = text_prefix + "📋 **اختر القسم الذي تريد التصفح منه:**"
        bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

    def send_category_items(chat_id, cat_id):
        cat_info = CATEGORIES.get(cat_id, {})
        bot.send_message(chat_id, f"📌 **قسم: {cat_info.get('name', '')}**\nتصفح الأصناف والأوزان المتاحة:")
        
        has_items = False
        for item_id, item in MENU_ITEMS.items():
            if item.get("category") == cat_id and item.get("available", True):
                has_items = True
                send_single_item(chat_id, item_id, item)
                
        if not has_items:
            bot.send_message(chat_id, "عفواً، لا توجد أصناف متاحة في هذا القسم حالياً.")

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_back = types.InlineKeyboardButton("🔙 العودة للأقسام", callback_data="back_to_categories")
        btn_cart = types.InlineKeyboardButton("🛒 تأكيد الطلب", callback_data="view_cart")
        markup.add(btn_back, btn_cart)
        
        bot.send_message(chat_id, "👇 يمكنك العودة للتصفح أو الانتقال لتأكيد الطلب:", reply_markup=markup)

    def send_single_item(chat_id, item_id, item):
        cart = sessions.get(chat_id, {}).get("cart", {})
        qty = cart.get(item_id, 0)
        
        unit_str = f" [{item.get('unit', '')}]" if item.get('unit') else ""
        caption = f"🍽️ **{item['title']}**{unit_str}\n💰 السعر: {item['price']} ج.م\n🛒 المطلوب بالسلة: {qty}"
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn_minus = types.InlineKeyboardButton("➖", callback_data=f"dec_{item_id}")
        btn_qty = types.InlineKeyboardButton(f"العدد: {qty}", callback_data="ignore")
        btn_plus = types.InlineKeyboardButton("➕", callback_data=f"inc_{item_id}")
        markup.add(btn_minus, btn_qty, btn_plus)
        
        if item.get("image"):
            image_url = f"http://127.0.0.1:5000/uploads/{item['image']}"
            try:
                bot.send_photo(chat_id, photo=image_url, caption=caption, reply_markup=markup, parse_mode="Markdown")
            except:
                bot.send_message(chat_id, text=caption, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, text=caption, reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        chat_id = call.message.chat.id
        data = call.data
        
        if data == "restart_flow":
            sessions[chat_id] = {"step": "WAITING_NAME", "cart": {}}
            bot.answer_callback_query(call.id, "تم البدء من جديد!")
            bot.send_message(chat_id, "أهلاً بك من جديد! 🔄\nممكن نتعرف باسمك؟")
            return

        if chat_id not in sessions:
            bot.answer_callback_query(call.id, "انتهت الجلسة، اضغط /start من جديد")
            return

        cart = sessions[chat_id].setdefault("cart", {})

        if data.startswith("show_cat_"):
            cat_id = data.replace("show_cat_", "")
            bot.answer_callback_query(call.id)
            send_category_items(chat_id, cat_id)

        elif data == "back_to_categories":
            bot.answer_callback_query(call.id)
            send_categories_menu(chat_id, "🔄 ")

        elif data.startswith("inc_"):
            item_id = data.replace("inc_", "")
            cart[item_id] = cart.get(item_id, 0) + 1
            bot.answer_callback_query(call.id, text="تمت الزيادة (+1)")
            update_item_message(call, item_id)

        elif data.startswith("dec_"):
            item_id = data.replace("dec_", "")
            if cart.get(item_id, 0) > 0:
                cart[item_id] -= 1
                bot.answer_callback_query(call.id, text="تم الإنقاص (-1)")
                update_item_message(call, item_id)
            else:
                bot.answer_callback_query(call.id, text="الكمية 0")

        elif data == "view_cart":
            show_cart_and_confirm(chat_id, call.id)

        elif data == "confirm_final_order":
            process_final_order(chat_id, call.id)

    def update_item_message(call, item_id):
        chat_id = call.message.chat.id
        item = MENU_ITEMS.get(item_id)
        cart = sessions.get(chat_id, {}).get("cart", {})
        qty = cart.get(item_id, 0)
        
        unit_str = f" [{item.get('unit', '')}]" if item.get('unit') else ""
        caption = f"🍽️ **{item['title']}**{unit_str}\n💰 السعر: {item['price']} ج.م\n🛒 المطلوب بالسلة: {qty}"
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn_minus = types.InlineKeyboardButton("➖", callback_data=f"dec_{item_id}")
        btn_qty = types.InlineKeyboardButton(f"العدد: {qty}", callback_data="ignore")
        btn_plus = types.InlineKeyboardButton("➕", callback_data=f"inc_{item_id}")
        markup.add(btn_minus, btn_qty, btn_plus)
        
        try:
            bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=caption, reply_markup=markup, parse_mode="Markdown")
        except:
            pass

    def show_cart_and_confirm(chat_id, callback_id):
        cart = sessions.get(chat_id, {}).get("cart", {})
        final_items = []
        total_price = 0
        
        for item_id, qty in cart.items():
            if qty > 0 and item_id in MENU_ITEMS:
                item = MENU_ITEMS[item_id]
                total_price += item["price"] * qty
                unit_str = f" ({item.get('unit', '')})" if item.get('unit') else ""
                final_items.append(f"• {item['title']}{unit_str} - العدد: {qty} = {item['price'] * qty} ج.م")
                
        if not final_items:
            bot.answer_callback_query(callback_id, text="السلة فارغة! اختر بعض الاصناف أولاً.", show_alert=True)
            return
            
        bot.answer_callback_query(callback_id)
        summary_text = "🛒 **ملخص سلة الطلبات الخاصة بك:**\n\n" + "\n".join(final_items) + f"\n\n💰 **الإجمالي الكلي:** {total_price} ج.م"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_confirm = types.InlineKeyboardButton("🚀 تأكيد وإرسال الطلب", callback_data="confirm_final_order")
        btn_back = types.InlineKeyboardButton("➕ إضافة المزيد", callback_data="back_to_categories")
        markup.add(btn_confirm, btn_back)
        
        bot.send_message(chat_id, summary_text, reply_markup=markup, parse_mode="Markdown")

    def process_final_order(chat_id, callback_id):
        cart = sessions.get(chat_id, {}).get("cart", {})
        user_info = sessions.get(chat_id, {})
        final_items = []
        total_price = 0
        
        for item_id, qty in cart.items():
            if qty > 0 and item_id in MENU_ITEMS:
                item = MENU_ITEMS[item_id]
                total_price += item["price"] * qty
                unit_str = f" [{item.get('unit', '')}]" if item.get('unit') else ""
                final_items.append(f"{item['title']}{unit_str} (x{qty})")
                
        if not final_items:
            bot.answer_callback_query(callback_id, text="السلة فارغة!", show_alert=True)
            return

        new_order = {
            "id": len(orders_db) + 1,
            "customer_name": user_info.get("name", "غير محدد"),
            "address": user_info.get("address", "غير محدد"),
            "phone": user_info.get("phone", "غير محدد"),
            "items": "\n".join(final_items),
            "total_price": f"{total_price} ج.م",
            "timestamp": datetime.now().strftime("%I:%M %p | %Y-%m-%d"),
            "platform": "TELEGRAM"
        }
        
        orders_db.append(new_order)
        bot.answer_callback_query(callback_id, text="تم تسجيل طلبك بنجاح!")
        
        confirmation_msg = (
            f"✅ **تم إرسال طلبك للمطعم بنجاح!**\n\n"
            f"👤 **الاسم:** {new_order['customer_name']}\n"
            f"📍 **العنوان:** {new_order['address']}\n"
            f"📞 **الرقم:** {new_order['phone']}\n\n"
            f"🛒 **الطلبات:**\n{new_order['items']}\n\n"
            f"💰 **الحساب الكلي:** {new_order['total_price']}\n\n"
            f"سيتم التواصل معك فوراً للتأكيد."
        )
        bot.send_message(chat_id, confirmation_msg, parse_mode="Markdown")
        sessions.pop(chat_id, None)

    return bot