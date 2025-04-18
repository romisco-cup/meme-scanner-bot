import time
import requests
import threading
from flask import Flask

import os
import telebot

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Simple web server to keep Render happy
@app.route("/")
def home():
    return "Meme bot is running."

def fetch_new_tokens():
    while True:
        try:
            url = "https://api.dexscreener.com/latest/dex/pairs/solana"
            response = requests.get(url)
            data = response.json()
            new_tokens = [pair for pair in data["pairs"] if "meme" in pair["baseToken"]["name"].lower()]
            
            for token in new_tokens:
                name = token["baseToken"]["name"]
                symbol = token["baseToken"]["symbol"]
                url = token["url"]
                price = token["priceUsd"]
                volume = token["volume"]["h24"]
                liquidity = token["liquidity"]["usd"]

                message = f"New Meme Coin Detected:\nName: {name} ({symbol})\nPrice: ${price}\nVolume: ${volume}\nLiquidity: ${liquidity}\nLink: {url}"
                bot.send_message(ALERT_CHAT_ID, message)
            
        except Exception as e:
            print("Error:", e)
        
        time.sleep(60)  # wait before checking again

def run_bot():
    thread = threading.Thread(target=fetch_new_tokens)
    thread.start()

# Start bot and web app
if __name__ == "__main__":
    run_bot()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
