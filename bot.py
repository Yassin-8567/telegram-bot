import telebot
from telebot import types
import os
import subprocess
import time
import sys
import logging

logging.basicConfig(level=logging.INFO)

# تم إزالة التوكن من الكود للأمان، هيتم وضعه في إعدادات السيرفر
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("Error: BOT_TOKEN is not set.")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# حط الآيدي بتاعك هنا (رقم)
DEVELOPER_ID = 123456789  
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

running_processes = {}

def is_admin(user_id):
    return user_id == DEVELOPER_ID

def main_menu():
    mar = types.InlineKeyboardMarkup(row_width=2)
    mar.add(
        types.InlineKeyboardButton("📥 - رفع ملف", callback_data="upload"),
        types.InlineKeyboardButton("🗑 - حذف ملف", callback_data="delete_file"),
    )
    mar.add(
        types.InlineKeyboardButton("🛠 - تحميل مكتبة", callback_data="install_lib"),
        types.InlineKeyboardButton("📝 - انشاء بوت", callback_data="make_bot"),
    )
    mar.add(
        types.InlineKeyboardButton("⛔ إيقاف بوت محدد", callback_data="stop_one"),
        types.InlineKeyboardButton("🟢 تشغيل بوت محدد", callback_data="start_one"),
    )
    mar.add(
        types.InlineKeyboardButton("📂 - ملفاتي", callback_data="list_files"),
        types.InlineKeyboardButton("👨🏻‍💻 مبرمج البوت", callback_data="dev"),
    )
    return mar

@bot.message_handler(commands=["start"])
def start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ هذا البوت مخصص للمطور فقط.")
        return
    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك في <b>مدير البوتات المتطور</b>!\n\n"
        "🔽 استخدم الأزرار للتحكم:\n",
        reply_markup=main_menu(),
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ أنت لست المطور.")
        return

    data = call.data
    chat_id = call.message.chat.id

    if data == "upload":
        bot.edit_message_text("📤 أرسل ملف Python (.py) لرفعه وتشغيله:", chat_id, call.message.id)
    elif data == "delete_file":
        msg = bot.edit_message_text("🗑 أرسل اسم الملف الذي تريد حذفه:", chat_id, call.message.id)
        bot.register_next_step_handler(msg, delete_file_step)
    elif data == "install_lib":
        msg = bot.edit_message_text("📦 أرسل اسم المكتبة التي تريد تحميلها (مثال: requests):", chat_id, call.message.id)
        bot.register_next_step_handler(msg, install_lib_step)
    elif data == "make_bot":
        msg = bot.edit_message_text("✏️ أرسل كود البوت بصيغة <code>.py</code>:", chat_id, call.message.id)
        bot.register_next_step_handler(msg, make_bot_step)
    elif data == "stop_one":
        msg = bot.edit_message_text("⛔ أرسل اسم البوت الذي تريد إيقافه:", chat_id, call.message.id)
        bot.register_next_step_handler(msg, stop_one_step)
    elif data == "start_one":
        msg = bot.edit_message_text("🟢 أرسل اسم البوت الذي تريد تشغيله:", chat_id, call.message.id)
        bot.register_next_step_handler(msg, start_one_step)
    elif data == "list_files":
        files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".py")]
        if not files:
            bot.edit_message_text("📂 لا توجد ملفات مرفوعة حالياً.", chat_id, call.message.id, reply_markup=main_menu())
            return
        msg = "📋 ملفاتك:\n\n"
        for f in files:
            status = "🟢 شغال" if f in running_processes else "🔴 متوقف"
            size = os.path.getsize(os.path.join(UPLOAD_FOLDER, f)) // 1024
            msg += f"• {f} ({size} KB) — {status}\n"
        bot.edit_message_text(msg, chat_id, call.message.id, reply_markup=main_menu())
    elif data == "dev":
        bot.edit_message_text(f"👨🏻‍💻 مبرمج البوت: @KemoElYouTuber", chat_id, call.message.id, reply_markup=main_menu())

def delete_file_step(message):
    filename = message.text.strip()
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        bot.reply_to(message, "❌ الملف غير موجود.")
        return
    size = os.path.getsize(path) // 1024
    status = "🟢 شغال" if filename in running_processes else "🔴 متوقف"
    confirm = types.InlineKeyboardMarkup()
    confirm.add(types.InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"confirm_delete_{filename}"))
    confirm.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="back"))
    bot.reply_to(message, f"📂 <b>{filename}</b>\nالحجم: {size} KB\nالحالة: {status}\n\nهل تريد الحذف؟", reply_markup=confirm)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def confirm_delete(call):
    if not is_admin(call.from_user.id): return
    filename = call.data.replace("confirm_delete_", "")
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        if filename in running_processes:
            running_processes[filename].terminate()
            del running_processes[filename]
        os.remove(path)
        bot.edit_message_text(f"🗑 تم حذف الملف: {filename}", call.message.chat.id, call.message.id, reply_markup=main_menu())
    else:
        bot.edit_message_text("❌ الملف غير موجود.", call.message.chat.id, call.message.id, reply_markup=main_menu())

def install_lib_step(message):
    lib_name = message.text.strip()
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib_name])
        bot.reply_to(message, f"📦 تم تحميل المكتبة: {lib_name}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ فشل تحميل المكتبة:\n{e}")

def make_bot_step(message):
    code = message.text
    filename = f"userbot_{int(time.time())}.py"
    path = os.path.join(UPLOAD_FOLDER, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    msg = bot.reply_to(message, "⏳ جاري تشغيل البوت...")
    try:
        p = subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running_processes[filename] = p
        bot.edit_message_text(f"✅ تم إنشاء وتشغيل البوت: {filename}", message.chat.id, msg.id, reply_markup=main_menu())
    except Exception as e:
        bot.edit_message_text(f"❌ فشل تشغيل البوت: {e}", message.chat.id, msg.id, reply_markup=main_menu())

def stop_one_step(message):
    filename = message.text.strip()
    if filename in running_processes:
        running_processes[filename].terminate()
        del running_processes[filename]
        bot.reply_to(message, f"⛔ تم إيقاف البوت: {filename}")
    else:
        bot.reply_to(message, "❌ البوت غير مشغل أو غير موجود.")

def start_one_step(message):
    filename = message.text.strip()
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        bot.reply_to(message, "❌ الملف غير موجود.")
        return
    if filename in running_processes:
        bot.reply_to(message, "⚠️ البوت شغال بالفعل.")
        return
    try:
        p = subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running_processes[filename] = p
        bot.reply_to(message, f"🟢 تم تشغيل البوت: {filename}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل التشغيل: {e}")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ أنت لست المطور.")
        return

    document = message.document
    if not document.file_name.endswith(".py"):
        bot.reply_to(message, "❌ يجب أن يكون الملف بصيغة .py")
        return

    file_info = bot.get_file(document.file_id)
    file_path = os.path.join(UPLOAD_FOLDER, document.file_name)
    downloaded = bot.download_file(file_info.file_path)
    with open(file_path, "wb") as f:
        f.write(downloaded)

    bot.reply_to(message, f"📁 تم رفع الملف: {document.file_name}")

    if document.file_name in running_processes:
        running_processes[document.file_name].terminate()
        del running_processes[document.file_name]
    
    try:
        p = subprocess.Popen([sys.executable, file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running_processes[document.file_name] = p
        bot.reply_to(message, f"✅ تم تشغيل البوت: {document.file_name}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل التشغيل: {e}")

print("🚀 البوت يعمل الآن...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
