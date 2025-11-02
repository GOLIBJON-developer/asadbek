import os
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
from requests.exceptions import ConnectionError

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN environment variable topilmadi!")

ADMIN_IDS = [799317334, 7299166349]
CHANNEL_USERNAME = "@cosmocryptohelp"

bot = telebot.TeleBot(TOKEN)

BLOCKED_USERS_FILE = "blocked_users.txt"
USERS_FILE = "users.txt"


# === Foydalanuvchilarni saqlash va yuklash ===
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


BLOCKED_USERS = load_blocked_users()
USERS = load_users()


# === ADMIN komandalar ===
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
                bot.send_message(message.chat.id, f"❌ Foydalanuvchi {user_id} bloklandi.")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "❌ Xato! /block 12345678 formatda kiriting.")
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
            bot.send_message(message.chat.id, "❌ Xato! /unblock 12345678 formatda kiriting.")
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")


@bot.message_handler(func=lambda message: message.chat.id in BLOCKED_USERS)
def blocked_message(message):
    bot.send_message(message.chat.id, "❌ Siz ushbu botdan foydalanish huquqidan mahrum qilindingiz!")


# === Asosiy menu ===
main_keyboard = InlineKeyboardMarkup()
main_keyboard.add(InlineKeyboardButton("⭐️ Stars sotib olish ⭐️", callback_data="buy_stars"))
main_keyboard.add(InlineKeyboardButton("⚡️ Telegram Premium sotib olish ⚡️", callback_data="buy_premium"))
main_keyboard.add(InlineKeyboardButton("🎞️ Foydalanish qo'llanmasi 📷", callback_data="buy_nft"))

# === Narxlar ===
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


# === Start komandasi ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.send_message(message.chat.id, "Assalomu alaykum! Kerakli xizmatni tanlang:", reply_markup=main_keyboard)


# === Xizmatlar bo‘limlari ===
@bot.callback_query_handler(func=lambda call: call.data == "buy_stars")
def show_stars(call):
    try:
        bot.edit_message_text("Tanlangan xizmat: ⭐️ Stars sotib olish", call.message.chat.id,
                              call.message.message_id, reply_markup=generate_keyboard(stars_options, "stars"))
    except Exception as e:
        print(f"⚠️ show_stars xatosi: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def show_premium(call):
    try:
        bot.edit_message_text("Tanlangan xizmat: ⚡️ Telegram Premium sotib olish", call.message.chat.id,
                              call.message.message_id, reply_markup=generate_keyboard(premium_options, "premium"))
    except Exception as e:
        print(f"⚠️ show_premium xatosi: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "buy_nft")
def buy_nft(call):
    bot.send_message(call.message.chat.id,
                     "Botdan xatosiz foydalanish uchun qo‘llanma: https://t.me/cosmocryptohelp/1095\n"
                     "📸 Faqat skrinshot yuboring (PDF emas). Agar username bo‘lmasa, buyurtma bekor qilinadi!")


# === Buyurtma tanlash ===
@bot.callback_query_handler(func=lambda call: call.data.startswith(("stars_", "premium_")))
def handle_payment(call):
    category, amount, price = call.data.split('_')
    product_name = f"{amount}⭐️" if category == "stars" else f"{amount} Telegram Premium"
    text = (f"Siz {price} so‘mlik {product_name} paketni tanladingiz.\n"
            f"💳 To‘lov kartasi:\n🏦 TRASTBANK HUMO 9860180104694591\n"
            f"🤵‍♂️ Komiljanov Muhammadmurod\n\n✅ To‘lovni amalga oshirib, skrinshotni yuboring (PDF emas).")
    orders[call.message.chat.id] = {"product": product_name, "amount": price, "status": "pending"}
    bot.send_message(call.message.chat.id, text, reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton("⬅️ Ortga", callback_data="back")))


# === Foydalanuvchi chek yuborganda ===
@bot.message_handler(content_types=['photo'])
def receive_receipt(message):
    order_id = message.chat.id
    if order_id in orders and orders[order_id]["status"] == "pending":
        orders[order_id]["status"] = "waiting"
        username = message.chat.username or "Ismi mavjud emas"
        caption = (f"📥 Yangi buyurtma!\n👤 @{username} ({message.chat.first_name})\n"
                   f"🆔 ID: {order_id}\n💰 {orders[order_id]['amount']} so‘m\n🛒 {orders[order_id]['product']}")
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{order_id}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{order_id}")
        )
        try:
            msg = bot.send_photo(CHANNEL_USERNAME, message.photo[-1].file_id, caption=caption, reply_markup=markup)
            orders[order_id]["message_id"] = msg.message_id
            bot.send_message(message.chat.id, "✅ Chek qabul qilindi. Natijani @cosmocryptohelp kanalidan kuzating.")
        except Exception as e:
            print(f"⚠️ Foto yuborishda xato: {e}")


# === Buyurtmani tasdiqlash / bekor qilish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_order(call):
    if call.from_user.id in ADMIN_IDS:
        try:
            order_id = int(call.data.split("_")[1])
            if order_id in orders and orders[order_id]["status"] == "waiting":
                orders[order_id]["status"] = "confirmed"
                bot.edit_message_caption(call.message.caption + "\n\n✅ To‘lov tasdiqlandi!",
                                         CHANNEL_USERNAME, call.message.message_id)
                bot.send_message(order_id, "✅ To‘lov tasdiqlandi! Xizmat tez orada faollashtiriladi.")
        except Exception as e:
            print(f"⚠️ confirm_order xatosi: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_order(call):
    if call.from_user.id in ADMIN_IDS:
        try:
            order_id = int(call.data.split("_")[1])
            if order_id in orders and orders[order_id]["status"] == "waiting":
                orders[order_id]["status"] = "cancelled"
                bot.edit_message_caption(call.message.caption + "\n\n❌ To‘lov rad etildi.",
                                         CHANNEL_USERNAME, call.message.message_id)
                bot.send_message(order_id, "❌ To‘lov rad etildi. Savollar uchun @Mr_Sobirjanov ga yozing.")
        except Exception as e:
            print(f"⚠️ cancel_order xatosi: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "back")
def go_back(call):
    try:
        bot.edit_message_text("Kerakli xizmatni tanlang:", call.message.chat.id,
                              call.message.message_id, reply_markup=main_keyboard)
    except Exception as e:
        print(f"⚠️ go_back xatosi: {e}")


# === Admin panel ===
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
        total = len(orders)
        pending = sum(1 for o in orders.values() if o["status"] == "pending")
        confirmed = sum(1 for o in orders.values() if o["status"] == "confirmed")
        cancelled = sum(1 for o in orders.values() if o["status"] == "cancelled")
        bot.send_message(call.message.chat.id,
                         f"📊 **Statistika:**\n\n🔹 Jami: {total}\n🕒 Kutilmoqda: {pending}\n✅ Tasdiqlangan: {confirmed}\n❌ Bekor: {cancelled}")
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
            except Exception:
                pass
        bot.send_message(message.chat.id, f"✅ Xabar {count} foydalanuvchiga yuborildi!")


# === Doimiy polling: to‘xtamasligi uchun ===
def run_bot():
    while True:
        try:
            print("🤖 Bot ishga tushdi...")
            bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)
        except (ConnectionError, apihelper.ApiTelegramException) as e:
            print(f"⚠️ API yoki tarmoq xatosi: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Noma’lum xato: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
