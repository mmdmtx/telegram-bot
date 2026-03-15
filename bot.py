async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = None
    if context.args:
        key = context.args[0]
    
    context.user_data["key"] = key

    # اگر کاربر از قبل عضو بود، مستقیم لینک رو بده
    try:
        member = await context.bot.get_chat_member(MAIN_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            if key and key in links:
                await update.message.reply_text(f"بفرمایید، این هم لینک شما:\n\n{links[key]}")
            else:
                await update.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
            return 
    except Exception:
        pass

    # اگر عضو نبود، این متن و دکمه‌ها رو نشون بده
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
                await query.message.reply_text(f"بفرمایید، این هم لینک شما:\n\n{links[key]}")
            else:
                await query.message.reply_text("لینک منقضی شده یا وجود ندارد. 😔")
        else:
            await query.answer("لطفا اول در کانال عضو شوید! ❌", show_alert=True)
    except Exception as e:
        await query.answer("خطا در بررسی عضویت.", show_alert=True)
