from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random
import string

TOKEN = "8778094095:AAFc4hcaaOo0Z5ja9OmxqbYF89GvBwIq2AY"

ADMIN_ID = 5756376686

MAIN_CHANNEL = "@superfastsub"
MAIN_CHANNEL_LINK = "https://t.me/superfastsub"

links = {}
waiting_for_post = False


def generate_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    key = None
    if context.args:
        key = context.args[0]

    context.user_data["key"] = key

    keyboard = [
        [InlineKeyboardButton("Join Channel", url=MAIN_CHANNEL_LINK)],
        [InlineKeyboardButton("Check", callback_data="check")]
    ]

    await update.message.reply_text(
        "Join the channel then press check.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(MAIN_CHANNEL, user_id)

    if member.status in ["member", "administrator", "creator"]:

        key = context.user_data.get("key")

        if key in links:

            await query.message.reply_text(
                f"Your link:\n\n{links[key]}"
            )

        else:

            await query.message.reply_text(
                "Link expired."
            )

    else:

        await query.answer("Join channel first", show_alert=True)


async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global waiting_for_post

    if update.effective_user.id != ADMIN_ID:
        return

    waiting_for_post = True

    await update.message.reply_text(
        "Send the post link."
    )


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

        await update.message.reply_text(
            f"New link created:\n\n{entry_link}"
        )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("new", new))

app.add_handler(CallbackQueryHandler(check, pattern="check"))

app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("Bot running...")

app.run_polling()
