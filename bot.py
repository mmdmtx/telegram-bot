import os
import random
import string
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- بخش زنده نگه داشتن سرور ---
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
# ----------------------------

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
            if key in links:
                await update.message.reply_text(f"بفرمایید، این هم لینک شما:\n\n{links[key]}")
            else:
                await update.message.reply_text("لینک مورد نظر یافت نشد یا منقضی شده است. 😔")
            return
    except:
        pass

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
            if key in links:
                await query.message.reply_text(f"بفرمایید، این هم لینک شما:\n\n{links[key]}")
            else:
                await query.message.reply_text("لینک منقضی شده است. 😔")
        else:
            await query.answer("لطفا اول در کانال عضو شوید! ❌", show_alert=True)
    except:
        await query.answer("خطا در بررسی عضویت. دوباره تلاش کنید.", show_alert=True)

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_post
    if update.effective_user.id != ADMIN_ID: return
    waiting_for_post = True
    await update.message.reply_text("لینک پست را بفرستید:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_post
    if update.effective_user.id != ADMIN_ID or not waiting_for_post: return
    
    post_link = update.message.text
    key = generate_key()
    links[key] = post_link
    waiting_for_post = False
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(f"لینک جدید ساخته شد:\n\nhttps://t.me/{bot_username}?start={key}")

if __name__ == '__main__':
    keep_alive()
    if TOKEN:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("new", new))
        app.add_handler(CallbackQueryHandler(check, pattern="check"))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
