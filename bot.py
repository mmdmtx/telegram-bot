import os, random, string, logging, redis
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# اتصال به دیتابیس Redis
redis_url = os.environ.get("REDIS_URL")
db = redis.from_url(redis_url, decode_responses=True)

web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 5756376686

# --- تنظیمات دقیق کانال‌های شما ---
CHANNELS = {
    "@superfastsub": "https://t.me/superfastsub",
    "-1003889301236": "https://t.me/+QZ96RdAToi0yMjZk",
    "-1003841395873": "https://t.me/+mDVc97uJ6d40N2Y0"
}

waiting_for_post = False

def generate_key(): return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def is_member(bot, user_id):
    """بررسی عضویت در هر ۳ کانال"""
    for channel_id in CHANNELS.keys():
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.error(f"Error checking {channel_id}: {e}")
            return False
    return True

async def send_movie_link(target, key):
    link = db.get(key)
    text = f"مرسی که کانال‌های ما رو فالو کردی 😍🫶🏻\n\n\nروی لینک کلیک کن و از فیلم لذت ببر😋💪🏼\n\n{link}\n{link}"
    if isinstance(target, Update):
        await target.message.reply_text(text)
    else: # برای CallbackQuery
        await target.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = context.args[0] if context.args else None
    context.user_data["key"] = key
    
    # اگر عضو بود، مستقیم لینک رو بده
    if await is_member(context.bot, user_id):
        if key and db.exists(key):
            await send_movie_link(update, key)
        elif key:
            await update.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
        else:
            await update.message.reply_text("سلام! خوش آمدید. برای دریافت لینک فیلم، باید از لینک‌های مخصوص استفاده کنید.")
        return

    # اگر عضو نبود، نمایش دکمه‌ها
    keyboard = [
        [InlineKeyboardButton("کانال زیرنویس فوق سریع", url=CHANNELS["@superfastsub"])],
        [InlineKeyboardButton("کانال دانلود ۱", url=CHANNELS["-1003889301236"])],
        [InlineKeyboardButton("کانال دانلود ۲", url=CHANNELS["-1003841395873"])],
        [InlineKeyboardButton("عضو شدم🙃", callback_data="check")]
    ]
    await update.message.reply_text(
        "لطفا برای دیدن فیلم عضو کانال اصلی و کانال‌های دانلود زیر شوید 🙏🏻🫡",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if await is_member(context.bot, user_id):
        key = context.user_data.get("key")
        if key and db.exists(key):
            await send_movie_link(query, key)
        else:
            await query.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
    else:
        await query.answer("هنوز در تمام کانال‌ها عضو نشدید! ❌", show_alert=True)

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        global waiting_for_post
        waiting_for_post = True
        await update.message.reply_text("لینک پست را بفرستید:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_post
    if update.effective_user.id == ADMIN_ID and waiting_for_post:
        key = generate_key()
        db.set(key, update.message.text)
        waiting_for_post = False
        bot = await context.bot.get_me()
        await update.message.reply_text(f"لینک جدید ساخته شد (ذخیره ابدی):\n\nhttps://t.me/{bot.username}?start={key}")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new))
    app.add_handler(CallbackQueryHandler(check, pattern="check"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
