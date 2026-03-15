import os
import random
import string
import logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# روشن کردن سیستم لاگ برای دیدن دقیق ارورها
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- وب‌سرور برای رندر ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# ------------------------

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 5756376686
MAIN_CHANNEL = "@superfastsub"
MAIN_CHANNEL_LINK = "https://t.me/superfastsub"

links = {}
waiting_for_post = False

def generate_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = context.args[0] if context.args else None
    context.user_data["key"] = key

    try:
        member = await context.bot.get_chat_member(MAIN_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            if key and key in links:
                # پیام موفقیت برای کاربرانی که از قبل عضو هستند
                await update.message.reply_text(
                    f"مرسی که کانال اصلی رو فالو کردی 😍🫶🏻\n\n\nروی لینک کلیک کن و از فیلم لذت ببر😋💪🏼\n\n{links[key]}\n{links[key]}"
                )
            else:
                await update.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
            return 
    except Exception as e:
        logging.error(f"Error in start: {e}")

    keyboard = [
        [InlineKeyboardButton("کانال زیرنویس فوق سریع", url=MAIN_CHANNEL_LINK)],
        [InlineKeyboardButton("عضو شدم🙃", callback_data="check")]
    ]
    await update.message.reply_text(
        "لطفا برای دیدن فیلم عضو کانال اصلی زیرنویس فوق سریع شوید 🙏🏻🫡",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    try:
        member = await context.bot.get_chat_member(MAIN_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            key = context.user_data.get("key")
            if key and key in links:
                # پیام موفقیت برای کاربرانی که تازه عضو شدند و دکمه چک رو زدند
                await query.message.reply_text(
                    f"مرسی که کانال اصلی رو فالو کردی 😍🫶🏻\n\n\nروی لینک کلیک کن و از فیلم لذت ببر😋💪🏼\n\n{links[key]}\n{links[key]}"
                )
            else:
                await query.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
        else:
            await query.answer("لطفا اول در کانال عضو شوید! ❌", show_alert=True)
    except Exception as e:
        logging.error(f"Error in check: {e}")
        await query.answer("خطا در بررسی عضویت.", show_alert=True)

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_post
    if update.effective_user.id != ADMIN_ID:
        return
    waiting_for_post = True
    await update.message.reply_text("لینک پست را بفرستید:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_post
    if update.effective_user.id != ADMIN_ID:
        return
    if waiting_for_post:
        post_link = update.message.text
        key = generate_key()
        links[key] = post_link
        waiting_for_post = False
        bot_username = (await context.bot.get_me()).username
        entry_link = f"https://t.me/{bot_username}?start={key}"
        await update.message.reply_text(f"لینک جدید ساخته شد:\n\n{entry_link}")

if __name__ == '__main__':
    if not TOKEN:
        print("CRITICAL ERROR: BOT_TOKEN is missing!")
    else:
        keep_alive()
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("new", new))
        app.add_handler(CallbackQueryHandler(check, pattern="check"))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        print("Bot is running perfectly...")
        app.run_polling()
