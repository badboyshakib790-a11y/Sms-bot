import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "9147382802:AAE-dHSe8pChND4I8T9jdHQUGoK1tlFTh-E"
ADMIN_ID = 8474773685  # আপনার টেলিগ্রাম আইডি এখানে দিন
bot = telebot.TeleBot(TOKEN)
API_URL = "https://api-merchant.carrybee.com/api/v2/merchant/register"

user_steps = {}

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # ইউজার টেবিলে রেফারেল কাউন্ট এবং পয়েন্ট ফিল্ড যুক্ত করা হলো
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 5,
            referred_by INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(user_id, username, referrer_id=None):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        # নতুন ইউজার হলে এবং রেফারেল থাকলে তাকে বোনাস পয়েন্ট দেওয়া হবে
        initial_points = 500000
        cursor.execute("INSERT INTO users (user_id, username, points, referred_by) VALUES (?, ?, ?, ?)", 
                       (user_id, username, initial_points, referrer_id))
        conn.commit()
        
        # যদি কেউ রেফার করে থাকে, তবে তাকে ৩ পয়েন্ট দেওয়া হবে
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET points = points + 3 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            try:
                bot.send_message(referrer_id, "🎉 অভিনন্দন! আপনার রেফারল লিংকের মাধ্যমে একজন নতুন ইউজার যুক্ত হয়েছে এবং আপনি **৩ পয়েন্ট** বোনাস পেয়েছেন!")
            except:
                pass
        points = initial_points
    else:
        points = row[0]
    conn.close()
    return points

def update_points(user_id, amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# সাধারণ ইউজার এবং এডমিনের জন্য কিবোর্ড মেনু
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🚀 Register Merchant"),
        KeyboardButton("💰 My Balance"),
        KeyboardButton("🔗 Referral Link"),
        KeyboardButton("🛒 Buy Points"),
        KeyboardButton("🔄 Send Points"),
        KeyboardButton("ℹ️ Developer Info")
    )
    if user_id == ADMIN_ID:
        markup.add(KeyboardButton("🛡️ Admin Panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # রেফারেল আইডি চেক করা (যেমন: /start ref_123456)
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
        except:
            pass

    points = get_user(user_id, username, referrer_id)
    user_steps.pop(user_id, None)
    
    welcome_text = (
        f"স্বাগতম **{message.from_user.first_name}** ভাইয়া! 🎉\n"
        f"আপনার বর্তমান পয়েন্ট: **{points} Pts**\n\n"
        "নিচের মেনু থেকে আপনার প্রয়োজনীয় অপশনটিতে ক্লিক করুন:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# মেনু হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text in [
    "🚀 Register Merchant", "💰 My Balance", "🔗 Referral Link", 
    "🛒 Buy Points", "🔄 Send Points", "ℹ️ Developer Info", "🛡️ Admin Panel"
])
def handle_menu(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "💰 My Balance":
        points = get_user(user_id, message.from_user.username)
        bot.send_message(message.chat.id, f"💰 আপনার বর্তমান ব্যালেন্স: **{points} Pts**", parse_mode="Markdown")
        
    elif text == "🔗 Referral Link":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        ref_text = (
            "🔗 **আপনার রেফারেল লিংক:**\n\n"
            f"`{ref_link}`\n\n"
            "💡 এই লিংকটি আপনার বন্ধুদের সাথে শেয়ার করুন। কেউ এই লিংকে জয়েন করলে প্রতি রেফারে আপনি পাবেন **৩ পয়েন্ট** করে!"
        )
        bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")
        
    elif text == "🛒 Buy Points":
        buy_text = (
            "🛒 **পয়েন্ট ক্রয় করুন (Buy Points):**\n\n"
            "পয়েন্ট কিনতে বা রিচার্জ করতে আমাদের এডমিনের সাথে যোগাযোগ করুন:\n"
            "👨‍💻 Developer: **@Rifat_jahan_12**"
        )
        bot.send_message(message.chat.id, buy_text, parse_mode="Markdown")
        
    elif text == "ℹ️ Developer Info":
        dev_text = (
            "🛠️ **Bot Developer Info:**\n\n"
            "এই প্রজেক্টের ডেভেলপার: **@Rifat_jahan_12**\n"
            "যেকোনো প্রয়োজনে বা কাস্টম ফিচারের জন্য যোগাযোগ করতে পারেন।"
        )
        bot.send_message(message.chat.id, dev_text, parse_mode="Markdown")

    elif text == "🚀 Register Merchant":
        points = get_user(user_id, message.from_user.username)
        if points < 1:
            bot.send_message(message.chat.id, "❌ আপনার পর্যাপ্ত পয়েন্ট নেই! রেজিস্ট্রেশন করতে অন্তত ১ পয়েন্ট প্রয়োজন। পয়েন্ট কিনতে 'Buy Points' অপশন দেখুন।")
            return
        user_steps[user_id] = {"step": "waiting_phone"}
        bot.send_message(message.chat.id, "📞 আপনি যে নাম্বারে এসএমএস পাঠাতে চাচ্ছেন সে নাম্বারটি লিখুন 🇧🇩 ", parse_mode="Markdown")
        
    elif text == "🔄 Send Points":
        bot.send_message(message.chat.id, "অন্য ইউজারকে পয়েন্ট পাঠাতে এই ফরম্যাটে লিখুন:\n`/send [User_ID] [Amount]`", parse_mode="Markdown")
        
    elif text == "🛡️ Admin Panel" and user_id == ADMIN_ID:
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.close()
        
        admin_info = (
            f"🛡️ **অ্যাডমিন কন্ট্রোল প্যানেল (@EHRUMON):**\n\n"
            f"📊 মোট রেজিস্টার্ড ইউজার: `{total_users}` জন\n\n"
            "🔧 **কমান্ড লিস্ট:**\n"
            "• পয়েন্ট যোগ করতে: `/addpoints [User_ID] [Amount]`\n"
            "• পয়েন্ট কাটতে: `/removepoints [User_ID] [Amount]`\n"
            "• সবাইকে মেসেজ পাঠাতে: `/broadcast [Message]`"
        )
        bot.send_message(message.chat.id, admin_info, parse_mode="Markdown")

# ধাপ অনুযায়ী রেজিস্ট্রেশন প্রসেস
@bot.message_handler(func=lambda message: message.from_user.id in user_steps)
def process_registration_steps(message):
    user_id = message.from_user.id
    state = user_steps[user_id]
    
    if state["step"] == "waiting_phone":
        phone = message.text.strip()
        user_steps[user_id]["phone"] = phone
        user_steps[user_id]["step"] = "waiting_name"
        bot.send_message(message.chat.id, "আপনি যে কোম্পানির নামে এসএমএস পাঠাতে চাচ্ছেন এই কোম্পানির নাম লিখুন এক্সাম্পল বিকাশ 😃")
        
    elif state["step"] == "waiting_name":
        name = message.text.strip()
        user_steps[user_id]["name"] = name
        user_steps[user_id]["step"] = "waiting_business"
        bot.send_message(message.chat.id, "আপনি কি এসএমএস পাঠাতে চাচ্ছেন সেটা লিখুন ")
        
    elif state["step"] == "waiting_business":
        business_name = message.text.strip()
        phone = user_steps[user_id]["phone"]
        name = user_steps[user_id]["name"]
        
        user_steps.pop(user_id, None)
        
        if len(business_name) < 3:
            business_name += " Enterprise"

        payload = {"name": name, "phone_number": phone, "business_name": business_name}
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "origin": "https://merchant.carrybee.com",
            "referer": "https://merchant.carrybee.com/"
        }

        processing_msg = bot.send_message(message.chat.id, "⏳ CarryBee API-তে রিকোয়েস্ট পাঠানো হচ্ছে...")

        try:
            response = requests.post(API_URL, json=payload, headers=headers, verify=False, timeout=30)
            res_data = response.json()

            if not res_data.get("error", True):
                update_points(user_id, -1)
                data = res_data.get("data", {})
                success_text = (
                    f"✅ **সফলভাবে রেজিস্টার্ড হয়েছে!** (-1 Point)\n\n"
                    f"👤 **নাম:** {data.get('name')}\n"
                    f"📞 **নম্বর:** {data.get('phone_number')}\n"
                    f"🏢 **বিজনেস:** {data.get('business_name')}\n"
                    f"🔑 **OTP Prefix:** `{data.get('otp_prefix')}`"
                )
                bot.edit_message_text(success_text, chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode="Markdown")
            else:
                bot.edit_message_text(f"❌ **ফেইল করেছে:**\n`{res_data}`", chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ টেকনিক্যাল এরর: `{str(e)}`")

# পয়েন্ট ট্রান্সফার কমান্ড
@bot.message_handler(commands=['send'])
def send_points(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "⚠️ সঠিক নিয়মে লিখুন: `/send [User_ID] [Amount]`")
            return
        target_id = int(args[1])
        amount = int(args[2])
        sender_id = message.from_user.id

        if amount <= 0:
            bot.reply_to(message, "⚠️ পজেটিভ এমাউন্ট দিন।")
            return

        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (sender_id,))
        sender_row = cursor.fetchone()
        if not sender_row or sender_row[0] < amount:
            bot.reply_to(message, "❌ আপনার পর্যাপ্ত পয়েন্ট নেই!")
            conn.close()
            return

        cursor.execute("SELECT points FROM users WHERE user_id = ?", (target_id,))
        if not cursor.fetchone():
            bot.reply_to(message, "❌ যে ইউজারকে পাঠাতে চাচ্ছেন তিনি বটে রেজিস্টার্ড নন।")
            conn.close()
            return

        cursor.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (amount, sender_id))
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ সফলভাবে `{amount}` পয়েন্ট ট্রান্সফার করা হয়েছে!")
        bot.send_message(target_id, f"🎁 আপনি ইউজার `{sender_id}` এর কাছ থেকে `{amount}` পয়েন্ট পেয়েছেন!")
    except Exception as e:
        bot.reply_to(message, f"❌ ত্রুটি ঘটেছে: {str(e)}")

# --- এডমিন ম্যানেজমেন্ট কমান্ডস ---

# পয়েন্ট অ্যাড করা
@bot.message_handler(commands=['addpoints'])
def admin_add_points(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        target_id = int(args[1])
        amount = int(args[2])
        update_points(target_id, amount)
        bot.reply_to(message, f"✅ ইউজার `{target_id}` কে সফলভাবে `{amount}` পয়েন্ট দেওয়া হলো।")
        bot.send_message(target_id, f"🎉 এডমিন আপনাকে `{amount}` পয়েন্ট দিয়েছেন!")
    except:
        bot.reply_to(message, "⚠️ ব্যবহারবিধি: `/addpoints [User_ID] [Amount]`")

# পয়েন্ট রিমুভ করা
@bot.message_handler(commands=['removepoints'])
def admin_remove_points(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        target_id = int(args[1])
        amount = int(args[2])
        update_points(target_id, -amount)
        bot.reply_to(message, f"✅ ইউজার `{target_id}` এর একাউন্ট থেকে `{amount}` পয়েন্ট কেটে নেওয়া হয়েছে।")
        bot.send_message(target_id, f"⚠️ এডমিন আপনার একাউন্ট থেকে `{amount}` পয়েন্ট কেটে নিয়েছেন।")
    except:
        bot.reply_to(message, "⚠️ ব্যবহারবিধি: `/removepoints [User_ID] [Amount]`")

# ব্রডকাস্ট মেসেজ (সব ইউজারের কাছে এক ক্লিকে মেসেজ পাঠানো)
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        bot.reply_to(message, "⚠️ অনুগ্রহ করে মেসেজটি লিখুন: `/broadcast [আপনার মেসেজ]`", parse_mode="Markdown")
        return

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    success_count = 0
    fail_count = 0

    processing_msg = bot.reply_to(message, "🚀 ব্রডকাস্ট মেসেজ পাঠানো শুরু হয়েছে, দয়া করে অপেক্ষা করুন...")

    for row in users:
        u_id = row[0]
        try:
            bot.send_message(u_id, f"📢 **অ্যাডমিন অ্যানাউন্সমেন্ট:**\n\n{text_to_send}", parse_mode="Markdown")
            success_count += 1
        except:
            fail_count += 1

    bot.edit_message_text(
        f"✅ **ব্রডকাস্ট সম্পন্ন হয়েছে!**\n\n"
        f"📤 সফলভাবে পাঠানো হয়েছে: `{success_count}` জনের কাছে\n"
        f"❌ ফেইল করেছে: `{fail_count}` জনের কাছে",
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Ultra Advanced Bot with Refer, Buy, Broadcast is running...")
    bot.infinity_polling()
