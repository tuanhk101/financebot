
from flask import Flask, request
from telegram import Update
from bot import updater  # Import từ bot.py đã có

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    updater.dispatcher.process_update(update)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
