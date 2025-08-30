from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from pymongo import MongoClient

# ===== Config =====
BOT_TOKEN = "8357734886:AAHQi1zmj9q8B__7J-2dyYUWVTQrMRr65Dc"
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER_ID = 7363327309

client = MongoClient(MONGO_URI)
db = client["dicebot"]
users = db["users"]

# ===== Helper =====
def get_user(user_id):
    user = users.find_one({"user_id": user_id})
    if not user:
        users.insert_one({"user_id": user_id, "points": 0})
        user = users.find_one({"user_id": user_id})
    return user

# ===== Commands =====
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        await update.message.reply_text("👑 You are the Owner!\n💰 Balance: ♾️ Unlimited coins")
        return
    user = get_user(user_id)
    await update.message.reply_text(f"💰 Your balance: {user['points']} points")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: /Dice {1-6}")
        return

    guess = int(context.args[0])
    if guess < 1 or guess > 6:
        await update.message.reply_text("❌ Please choose a number between 1 and 6")
        return

    keyboard = [
        [InlineKeyboardButton("Play for 10 points", callback_data=f"{user_id}|10|{guess}"),
         InlineKeyboardButton("Play for 20 points", callback_data=f"{user_id}|20|{guess}"),
         InlineKeyboardButton("Play for 30 points", callback_data=f"{user_id}|30|{guess}")],
        [InlineKeyboardButton("play for 40 points", callback_data=f"{user_id}|40|{guess}"),
         InlineKeyboardButton("play for 50 points", callback_data=f"{user_id}|50|{guess}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your bet:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    user_id_from_button, bet_amount, guess = int(data[0]), int(data[1]), int(data[2])
    user_id = query.from_user.id
    user = get_user(user_id)

    if user_id != user_id_from_button:
        await query.edit_message_text("❌ This button is not for you!")
        return

    if user_id != OWNER_ID:
        if user['points'] < bet_amount:
            await query.edit_message_text("❌ You don't have enough points for this bet.")
            return
        users.update_one({"user_id": user_id}, {"$inc": {"points": -bet_amount}})

    dice_message = await query.message.reply_dice(emoji="🎲")
    rolled_number = dice_message.dice.value

    if guess == rolled_number:
        if user_id == OWNER_ID:
            result_text = f"👑 You guessed {guess} and rolled {rolled_number}!\n🎉 You always win with unlimited coins!"
        else:
            users.update_one({"user_id": user_id}, {"$inc": {"points": bet_amount * 2}})
            new_balance = users.find_one({"user_id": user_id})['points']
            result_text = f"🎉 You guessed {guess} and rolled {rolled_number}! You win!\n💰 New balance: {new_balance} points"
    else:
        if user_id == OWNER_ID:
            result_text = f"👑 You guessed {guess} but rolled {rolled_number}.\n❌ You lose nothing because you have unlimited coins!"
        else:
            new_balance = users.find_one({"user_id": user_id})['points']
            result_text = f"❌ You guessed {guess} but rolled {rolled_number}. You lose!\n💰 New balance: {new_balance} points"

    await query.edit_message_text(result_text)

# ===== Flexible Add/Remove Coins =====
async def addpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return

    if update.message.reply_to_message:  # Reply style
        target_id = update.message.reply_to_message.from_user.id
        if len(context.args) != 1:
            await update.message.reply_text("❌ Usage: /addpoint <amount>")
            return
        amount = int(context.args[0])
    else:  # Inline style
        if len(context.args) != 2:
            await update.message.reply_text("❌ Usage: /addpoint <@username/user_id> <amount>")
            return
        target = context.args[0]
        amount = int(context.args[1])
        if target.startswith("@"):
            target_user = await context.bot.get_chat(target)
            target_id = target_user.id
        else:
            target_id = int(target)

    get_user(target_id)
    users.update_one({"user_id": target_id}, {"$inc": {"points": amount}})
    new_balance = users.find_one({"user_id": target_id})["points"]
    
    try:
        chat = await context.bot.get_chat(target_id)
        username = f"@{chat.username}" if chat.username else str(target_id)
    except:
        username = str(target_id)

    await update.message.reply_text(f"✅ Added {amount} points to {username}\n💰 New balance: {new_balance} points")

async def removepoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return

    if update.message.reply_to_message:  # Reply style
        target_id = update.message.reply_to_message.from_user.id
        if len(context.args) != 1:
            await update.message.reply_text("❌ Usage: /removepoint <amount>")
            return
        amount = int(context.args[0])
    else:  # Inline style
        if len(context.args) != 2:
            await update.message.reply_text("❌ Usage: /removepoint <@username/user_id> <amount>")
            return
        target = context.args[0]
        amount = int(context.args[1])
        if target.startswith("@"):
            target_user = await context.bot.get_chat(target)
            target_id = target_user.id
        else:
            target_id = int(target)

    get_user(target_id)
    users.update_one({"user_id": target_id}, {"$inc": {"points": -amount}})
    new_balance = users.find_one({"user_id": target_id})["points"]
    
    try:
        chat = await context.bot.get_chat(target_id)
        username = f"@{chat.username}" if chat.username else str(target_id)
    except:
        username = str(target_id)

    await update.message.reply_text(f"❌ Removed {amount} points from {username}\n💰 New balance: {new_balance} points")

# ===== All Users =====
async def allusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return

    all_users = users.find()
    msg = "👥 Registered Users:\n\n"
    for u in all_users:
        try:
            chat = await context.bot.get_chat(u["user_id"])
            username = f"@{chat.username}" if chat.username else ""
        except:
            username = ""
        balance = "♾️ Unlimited" if u["user_id"] == OWNER_ID else u["points"]
        msg += f"🆔 {u['user_id']} {username} → {balance} points\n"
    await update.message.reply_text(msg)

# ===== Broadcast =====
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    all_users = users.find()
    sent = 0
    for u in all_users:
        try:
            await context.bot.send_message(chat_id=u["user_id"], text=message)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"📢 Broadcast sent to {sent} users.")

# ===== Help =====
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 Available Commands:\n\n"
        "👤 User Commands:\n"
        "/balance → Check your balance\n"
        "/dice {1-6} → Play dice game\n\n"
        "👑 Owner Commands:\n"
        "/addpoint <@username/user_id> <amount> → Add coins\n"
        "/removepoint <@username/user_id> <amount> → Remove coins\n"
        "/allusers → List all users with usernames & balances\n"
        "/broadcast <message> → Send message to all users"
    )
    await update.message.reply_text(help_text)

# ===== Main =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("addpoint", addpoint))
    app.add_handler(CommandHandler("removepoint", removepoint))
    app.add_handler(CommandHandler("allusers", allusers))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot is running...")
    app.run_polling()
