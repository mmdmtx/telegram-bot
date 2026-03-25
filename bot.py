import os, random, string, logging, redis, asyncio, json
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# اتصال به دیتابیس
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

# آیدی و لینک کانال‌ها
CHANNELS = {
    "@superfastsob": "https://t.me/superfastsob",
}

def generate_key(): return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# تابع حذف گروهی پیام‌ها (فیلم‌ها + متن هشدار)
async def delete_multiple_msgs_task(bot, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            logging.error(f"Error in deleting msg: {e}")
    try:
        await bot.send_message(chat_id=chat_id, text="Deleted Message")
    except:
        pass

async def is_member(bot, user_id):
    for channel_id in CHANNELS.keys():
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.error(f"Bot cannot check {channel_id}: {e}")
            return False 
    return True

# تابع ارسال فیلم‌ها و پیام هشدار
async def send_movie_link(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    user_id = update.effective_user.id
    data = db.get(key)
    
    if not data:
        return

    target = update.callback_query.message if update.callback_query else update.message
    sent_messages = []

    # ارسال فایل‌های ویدیویی به کاربر
    if data.startswith('['): # بررسی اینکه آیا لینک مربوط به سیستم جدید است (آرایه از آیدی فایل‌ها)
        file_ids = json.loads(data)
        for msg_id in file_ids:
            try:
                # ربات دقیقاً همون فایلی که تو فرستادی رو با کپشن برای کاربر کپی میکنه
                sent_msg = await context.bot.copy_message(
                    chat_id=target.chat_id,
                    from_chat_id=ADMIN_ID,
                    message_id=msg_id
                )
                sent_messages.append(sent_msg.message_id)
            except Exception as e:
                logging.error(f"Error copying message: {e}")
    else: # پشتیبانی از لینک‌های متنی قدیمی (اگر قبلا ساخته بودی)
        text = f"مرسی که کانال‌های ما رو فالو کردی 😍🫶🏻\n\n\nروی لینک کلیک کن و از فیلم لذت ببر😋💪🏼\n\n{data}"
        sent_msg = await target.reply_text(text)
        sent_messages.append(sent_msg.message_id)

    # ارسال پیام هشدار در پایین فایل‌ها
    warning_text = "⚠️ **توجه مهم:**\n\nاین ویدیوها و پیام‌ها تا **۵۰ ثانیه دیگر** به صورت کاملاً خودکار پاک خواهند شد!\n\nلطفاً همین الان فیلم‌ها را در **پیام‌های ذخیره‌شده (Saved Messages)** خود فوروارد کنید تا آن‌ها را از دست ندهید. ⏳"
    warn_msg = await context.bot.send_message(chat_id=target.chat_id, text=warning_text)
    sent_messages.append(warn_msg.message_id)

    # تایمر ۵۰ ثانیه‌ای برای پاک کردن همه پیام‌های فرستاده شده (به جز ادمین)
    if user_id != ADMIN_ID:
        asyncio.create_task(delete_multiple_msgs_task(context.bot, target.chat_id, sent_messages, 50))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = context.args[0] if context.args else None
    context.user_data["key"] = key
    
    if await is_member(context.bot, user_id):
        if key and db.exists(key):
            await send_movie_link(update, context, key)
        elif key:
            await update.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
        return

    keyboard = [
        [InlineKeyboardButton("کانال زیرنویس فوق سریع", url=CHANNELS["@superfastsob"])],
        [InlineKeyboardButton("عضو شدم🙃", callback_data="check")]
    ]
    await update.message.reply_text(
        "لطفا برای دیدن فیلم عضو کانال های زیر شوید 🙏🏻🫡",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if await is_member(context.bot, user_id):
        key = context.user_data.get("key")
        if key and db.exists(key):
            await send_movie_link(update, context, key)
        else:
            await query.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
    else:
        await query.answer("هنوز در تمام کانال‌ها عضو نشدید! ❌", show_alert=True)

# دستور جدید ساخت پست
async def new_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        context.user_data['uploading'] = True
        context.user_data['file_ids'] = [] # آماده‌سازی لیست برای دریافت فایل‌ها
        await update.message.reply_text("📥 حالت آپلود فعال شد!\n\nحالا فیلم‌ها رو (با کپشن یا کیفیت‌های مختلف) یکی یکی اینجا بفرست یا فوروارد کن.\n\n✅ هر وقت همه فایل‌های مربوط به این لینک رو فرستادی، دستور /done رو بفرست تا لینک نهایی ساخته بشه.")

# دستور پایان آپلود و دریافت لینک
async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        if context.user_data.get('uploading'):
            file_ids = context.user_data.get('file_ids', [])
            if not file_ids:
                await update.message.reply_text("❌ تو هنوز هیچ فایلی نفرستادی! اول فایل‌ها رو بفرست.")
                return
            
            key = generate_key()
            # ذخیره لیست آیدی پیام‌ها در دیتابیس
            db.set(key, json.dumps(file_ids))
            
            # خروج از حالت آپلود
            context.user_data['uploading'] = False
            context.user_data['file_ids'] = []
            
            bot = await context.bot.get_me()
            await update.message.reply_text(f"🎉 لینک دریافت فیلم‌های شما ساخته شد:\n\nhttps://t.me/{bot.username}?start={key}\n\n⚠️ نکته فوق‌العاده مهم: این فیلم‌هایی که الان برای من فرستادی رو هیچ‌وقت از چت با من پاک نکن، وگرنه ربات نمی‌تونه برای بقیه بفرستتشون.")
        else:
            await update.message.reply_text("شما اول باید دستور /new رو بزنید.")

# دریافت فایل‌ها از ادمین
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        if context.user_data.get('uploading'):
            # ثبت آیدی پیامی که ادمین فرستاده
            context.user_data['file_ids'].append(update.message.message_id)
            count = len(context.user_data['file_ids'])
            await update.message.reply_text(f"✅ فایل شماره {count} دریافت شد.\n\nاگر بازم کیفیت دیگه‌ای مونده بفرست، اگر نه دستور /done رو بزن.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_cmd)) # کامند جدید
    app.add_handler(CommandHandler("done", done_cmd)) # کامند اتمام
    app.add_handler(CallbackQueryHandler(check, pattern="check"))
    # دریافت هر نوع فایل و متنی به جای فقط متن
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    app.run_polling()
