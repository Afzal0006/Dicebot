from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8357734886:AAHQi1zmj9q8B__7J-2dyYUWVTQrMRr65Dc"  # <-- Yahan apna bot token daalein

# /Dice command handler
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice_message = await update.message.reply_dice(emoji="🎲")
    print("Rolled number:", dice_message.dice.value)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("Dice", dice))
    print("Bot is running...")
    app.run_polling()
