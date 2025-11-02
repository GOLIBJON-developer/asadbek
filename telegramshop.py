import telebot
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN environment variable topilmadi!")
    
ADMIN_IDS = [799317334, 7299166349]
CHANNEL_USERNAME = "@cosmocryptohelp"

bot = telebot.TeleBot(TOKEN)

BLOCKED_USERS_FILE = "blocked_users.txt"
USERS_FILE = "users.txt"

def load_blocked_users():
    try:
        with open(BLOCKED_USERS_FILE, "r") as f:
            return set(int(line.strip()) for line in f.readlines())
    except FileNotFoundError:
        return set()

def save_blocked_users():
    with open(BLOCKED_USERS_FILE, "w") as f:
        for user_id in BLOCKED_USERS:
            f.write(str(user_id) + "\n")

BLOCKED_USERS = load_blocked_users()

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(int(line.strip()) for line in f.readlines())
    except FileNotFoundError:
        return set()

def save_user(user_id):
    if user_id not in USERS:
        USERS.add(user_id)
        with open(USERS_FILE, "a") as f:
            f.write(str(user_id) + "\n")

USERS = load_users()

@bot.message_handler(commands=['block'])
def block_user(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            user_id = int(message.text.split()[1])
            if user_id in BLOCKED_USERS:
                bot.send_message(message.chat.id, f"🚫 {user_id} allaqachon bloklangan.")
            else:
                BLOCKED_USERS.add(user_id)
                save_blocked_users()
                bot.send_message(message.chat.id, f"\❌ Foydalanuvchi {user_id} bloklandi.")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "❌ Xato! Foydalanuvchi ID'sini to‘g‘ri kiriting.\nMasalan: `/block 12345678`")
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            user_id = int(message.text.split()[1])
            if user_id in BLOCKED_USERS:
                BLOCKED_USERS.remove(user_id)
                save_blocked_users()
                bot.send_message(message.chat.id, f"✅ {user_id} blokdan chiqarildi.")
            else:
                bot.send_message(message.chat.id, f"❌ {user_id} bloklangan emas.")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "❌ Xato! Foydalanuvchi ID'sini to‘g‘ri kiriting.\nMasalan: `/unblock 12345678`")
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

@bot.message_handler(func=lambda message: message.chat.id in BLOCKED_USERS)
def blocked_message(message):
    bot.send_message(message.chat.id, "❌ Siz ushbu botdan foydalanish huquqidan mahrum qilindingiz!")

# Asosiy menu
main_keyboard = InlineKeyboardMarkup()
main_keyboard.add(InlineKeyboardButton("⭐️ Stars sotib olish ⭐️", callback_data="buy_stars"))
main_keyboard.add(InlineKeyboardButton("⚡️ Telegram Premium sotib olish ⚡️", callback_data="buy_premium"))
main_keyboard.add(InlineKeyboardButton(" 🎞️Foydalanish qo'llanmasi📷  ", callback_data="buy_nft"))

# Stars va Premium narxlari
stars_options = {
    "50": "14.000", "100": "28.000", "150": "41.980", "200": "56.000",
    "300": "84.000", "500": "140.000", "1000": "280.000", "2000": "560.000",
    "5000": "1.400.000", "10000": "2.800.000"
}

premium_options = {
    "3 oylik": "190.000", "6 oylik": "262.000", "12 oylik": "429.000"
}

orders = {}

def generate_keyboard(options, category):
    keyboard = InlineKeyboardMarkup()
    for key, value in options.items():
        keyboard.add(InlineKeyboardButton(f"{key}⭐️ - {value} so’m", callback_data=f"{category}_{key}_{value}"))
    keyboard.add(InlineKeyboardButton("⬅️ Ortga", callback_data="back"))
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Assalomu alaykum! Kerakli xizmatni tanlang:", reply_markup=main_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "buy_stars")
def show_stars(call):
    bot.edit_message_text("Tanlangan xizmat: ⭐️ Stars sotib olish", call.message.chat.id, call.message.message_id, reply_markup=generate_keyboard(stars_options, "stars"))

@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def show_premium(call):
    bot.edit_message_text("Tanlangan xizmat: ⚡️ Telegram Premium sotib olish", call.message.chat.id, call.message.message_id, reply_markup=generate_keyboard(premium_options, "premium"))

@bot.callback_query_handler(func=lambda call: call.data == "buy_nft")
def buy_nft(call):
    bot.send_message(call.message.chat.id, "Botdan xatosiz foydalanish uchun qo'llanma! https://t.me/cosmocryptohelp/1095 Yodda tuting botga faqat skrinshot yuboring pdf emas! Agar sizda username bo'lmasa bot buyurtmangizni bekor qiladi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_") or call.data.startswith("premium_"))
def handle_payment(call):
    category, amount, price = call.data.split('_')
    product_name = f"{amount}⭐️" if category == "stars" else f"{amount} Telegram Premium"
    payment_text = f"Siz {price} so‘mlik {product_name} paketni tanladingiz.\n💳 To‘lov kartasi:\n🏦 TRASTBANK HUMO   9860180104694591🤵‍♂️ Komiljanov Muhammadmurod\n✅ To‘lovni amalga oshirib, chekni yuboring.Yodda tuting botga faqat skrinshot yuboring pdf emas! Agar sizda username bo'lmasa bot buyurtmangizni bekor qiladi!"
    orders[call.message.chat.id] = {"product": product_name, "amount": price, "status": "pending", "user_id": call.message.chat.id}
    bot.send_message(call.message.chat.id, payment_text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Ortga", callback_data="back")))

@bot.message_handler(content_types=['photo'])
def receive_receipt(message):
    order_id = message.chat.id
    if order_id in orders and orders[order_id]["status"] == "pending":
        orders[order_id]["status"] = "waiting"
        username = message.chat.username if message.chat.username else "Ismi mavjud emas"
        caption = (f"📥 Yangi buyurtma!\n👤 Foydalanuvchi: @{username} ({message.chat.first_name})\n"
                   f"🆔 ID: {order_id}\n"
                   f"💰 To'lov summasi: {orders[order_id]['amount']} so'm\n🛒 Mahsulot: {orders[order_id]['product']}")
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{order_id}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{order_id}")
        )
        msg = bot.send_photo(CHANNEL_USERNAME, message.photo[-1].file_id, caption=caption, reply_markup=markup)
        orders[order_id]["message_id"] = msg.message_id
        bot.send_message(message.chat.id, "Chek qabul qilindi✅. Xizmat holatini @cosmocryptohelp kanalida kuzatib borishingiz mumkin.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_order(call):
    if call.from_user.id in ADMIN_IDS:
        order_id = int(call.data.split("_")[1])
        if order_id in orders and orders[order_id]["status"] == "waiting":
            orders[order_id]["status"] = "confirmed"
            bot.edit_message_caption(call.message.caption + "\n\n✅ To‘lov tasdiqlandi!", CHANNEL_USERNAME, call.message.message_id)
            bot.send_message(order_id, "To‘lov tasdiqlandi! Xizmat tez orada faollashtiriladi. Xizmatimizdan foydalanganingiz uchun rahmat!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_order(call):
    if call.from_user.id in ADMIN_IDS:
        order_id = int(call.data.split("_")[1])
        if order_id in orders and orders[order_id]["status"] == "waiting":
            orders[order_id]["status"] = "cancelled"
            bot.edit_message_caption(call.message.caption + "\n\n❌ To‘lov rad etildi.", CHANNEL_USERNAME, call.message.message_id)
            bot.send_message(order_id, "❌ Sizning to‘lovingiz rad etildi. Iltimos tekshirib qaytadan urinib ko'ring. Savol va murojaatlar uchun @Mr_Sobirjanov ga murojaat qiling. ")

@bot.callback_query_handler(func=lambda call: call.data == "back")
def go_back(call):
    bot.edit_message_text("Kerakli xizmatni tanlang:", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard)
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"))
        keyboard.add(InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast"))
        bot.send_message(message.chat.id, "🛠 Admin panel:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id in ADMIN_IDS:
        total_orders = len(orders)
        pending_orders = sum(1 for o in orders.values() if o["status"] == "pending")
        confirmed_orders = sum(1 for o in orders.values() if o["status"] == "confirmed")
        cancelled_orders = sum(1 for o in orders.values() if o["status"] == "cancelled")
        bot.send_message(call.message.chat.id,
                         f"📊 **Statistika:**\n\n"
                         f"🔹 Jami buyurtmalar: {total_orders}\n"
                         f"🕒 Kutilayotgan: {pending_orders}\n"
                         f"✅ Tasdiqlangan: {confirmed_orders}\n"
                         f"❌ Bekor qilingan: {cancelled_orders}")
    else:
        bot.send_message(call.message.chat.id, "❌ Siz admin emassiz!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_prompt(call):
    if call.from_user.id in ADMIN_IDS:
        msg = bot.send_message(call.message.chat.id, "📢 Hammaga yuboriladigan xabarni yozing:")
        bot.register_next_step_handler(msg, send_broadcast)
    else:
        bot.send_message(call.message.chat.id, "❌ Siz admin emassiz!")

def send_broadcast(message):
    if message.from_user.id in ADMIN_IDS:
        text = message.text
        count = 0
        for user_id in USERS:
            try:
                bot.send_message(user_id, f"📢 **Admin xabari:**\n\n{text}")
                count += 1
            except:
                pass
        bot.send_message(message.chat.id, f"✅ Xabar {count} foydalanuvchiga yuborildi!")
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

bot.polling(none_stop=True)