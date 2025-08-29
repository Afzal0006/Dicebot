from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from pymongo import MongoClient
import random

# ===== Config =====
BOT_TOKEN = "8357734886:AAHQi1zmj9q8B__7J-2dyYUWVTQrMRr65Dc"
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["dicebot"]
users = db["users"]

# Helper: get or create user
def get_user(user_id):
    user = users.find_one({"user_id": user_id})
    if not user:
        users.insert_one({"user_id": user_id, "points": 0})
        user = users.find_one({"user_id": user_id})
    return user

# /Balance command
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    await update.message.reply_text(f"💰 Your balance: {user['points']} points")

# /Dice command
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ Usage: /Dice {1-6}")
        return

    guess = int(context.args[0])
    if guess < 1 or guess > 6:
        # Show inline bet buttons
        keyboard = [
            [InlineKeyboardButton("10 ✅", callback_data=f"{user_id}|10|{guess}"),
             InlineKeyboardButton("20 ✅", callback_data=f"{user_id}|20|{guess}"),
             InlineKeyboardButton("30 ✅", callback_data=f"{user_id}|30|{guess}")],
            [InlineKeyboardButton("40 ✅", callback_data=f"{user_id}|40|{guess}"),
             InlineKeyboardButton("50 ✅", callback_data=f"{user_id}|50|{guess}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose your bet:", reply_markup=reply_markup)
        return

    # If guess valid 1-6, allow inline bet selection
    keyboard = [
        [InlineKeyboardButton("10 ✅", callback_data=f"{user_id}|10|{guess}"),
         InlineKeyboardButton("20 ✅", callback_data=f"{user_id}|20|{guess}"),
         InlineKeyboardButton("30 ✅", callback_data=f"{user_id}|30|{guess}")],
        [InlineKeyboardButton("40 ✅", callback_data=f"{user_id}|40|{guess}"),
         InlineKeyboardButton("50 ✅", callback_data=f"{user_id}|50|{guess}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your bet:", reply_markup=reply_markup)

# Callback for inline button
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    user_id_from_button, bet_amount, guess = int(data[0]), int(data[1]), int(data[2])
    user_id = query.from_user.id
    user = get_user(user_id)

    # Check if the correct user clicked
    if user_id != user_id_from_button:
        await query.edit_message_text("❌ This button is not for you!")
        return

    # Check if user has enough points
    if user['points'] < bet_amount:
        await query.edit_message_text("❌ You don't have enough points for this bet.")
        return

    # Deduct bet points
    users.update_one({"user_id": user_id}, {"$inc": {"points": -bet_amount}})

    # Roll dice animation
    dice_message = await query.message.reply_dice(emoji="🎲")
    rolled_number = dice_message.dice.value

    # Check win or lose
    if guess == rolled_number:
        # Win → add double bet
        users.update_one({"user_id": user_id}, {"$inc": {"points": bet_amount * 2}})
        new_balance = users.find_one({"user_id": user_id})['points']
        result_text = f"🎉 You guessed {guess} and rolled {rolled_number}! You win!\n💰 New balance: {new_balance} points"
    else:
        new_balance = users.find_one({"user_id": user_id})['points']
        result_text = f"❌ You guessed {guess} but rolled {rolled_number}. You lose!\n💰 New balance: {new_balance} points"

    await query.edit_message_text(result_text)

# ===== Main =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("Balance", balance))
    app.add_handler(CommandHandler("Dice", dice))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()
