import time
import requests
import threading
from flask import Flask
import os
import telebot
from flask import render_template
from database import log_token, get_db_connection, update_token_alert_status
from datetime import datetime, timedelta
from twitter import get_trending_tickers

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Dexscreener Filters
MAX_LIQUIDITY = 100000
MAX_VOLUME = 200000
MIN_AGE_HOURS = 48
MAX_HOLDERS = 500
MEME_KEYWORDS = ["doge", "pepe", "inu", "elon"]

# Simple web server to keep Render happy
@app.route("/")
def home():
    return "Meme bot is running."

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    tokens = conn.execute('SELECT * FROM tokens ORDER BY discovered_at DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', tokens=tokens)

def get_holder_count(token_address):
    try:
        url = f"https://api.solana.fm/v1/tokens/{token_address}/holders"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("totalItemCount", 0)
        else:
            print(f"Failed to get holder count for {token_address}: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error getting holder count for {token_address}: {e}")
        return 0

def get_rugcheck_url(token_address):
    return f"https://rugcheck.xyz/tokens/{token_address}"

def get_bubblemap_url(token_address):
    return f"https://bubblemaps.io/solana/{token_address}"

def get_tweetscout_url(token_symbol):
    return f"https://tweetscout.io/search?q=%24{token_symbol}"

def send_telegram_alert(token):
    twitter_status = "🔥 *Trending on Twitter!*" if token['twitter_trending'] else ""
    message = f"""
    *New Meme Coin Gem Found!* 💎 {twitter_status}

    *Name:* {token['name']} (${token['symbol']})
    *Contract Address:* `{token['address']}`

    *Price:* ${token['price']}
    *Volume (24h):* ${token['volume']}
    *Liquidity:* ${token['liquidity']}

    *Dexscreener:* [View Chart]({token['dexscreener_url']})

    *Safety Checks:*
    - [Rugcheck]({token['rugcheck_url']})
    - [BubbleMap]({token['bubblemap_url']})
    - [TweetScout]({token['tweetscout_url']})
    """
    try:
        bot.send_message(ALERT_CHAT_ID, message, parse_mode='Markdown')
        update_token_alert_status(token['address'])
        print(f"Alert sent for {token['name']}")
    except Exception as e:
        print(f"Failed to send Telegram alert for {token['name']}: {e}")

def process_tokens():
    while True:
        try:
            trending_tickers = get_trending_tickers()

            # Fetch new tokens from Dexscreener and log them
            url = "https://api.dexscreener.com/latest/dex/pairs/solana"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("pairs"):
                    for pair in data["pairs"]:
                        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
                        volume = float(pair.get("volume", {}).get("h24", 0))
                        pair_created_at = datetime.fromtimestamp(pair.get("pairCreatedAt", 0) / 1000)
                        token_address = pair["baseToken"]["address"]
                        holder_count = get_holder_count(token_address)
                        token_name = pair["baseToken"]["name"].lower()
                        token_symbol = pair["baseToken"]["symbol"]

                        if (liquidity <= MAX_LIQUIDITY and
                            volume <= MAX_VOLUME and
                            datetime.utcnow() - pair_created_at >= timedelta(hours=MIN_AGE_HOURS) and
                            holder_count <= MAX_HOLDERS and
                            any(keyword in token_name for keyword in MEME_KEYWORDS)):

                            token_data = {
                                "name": pair["baseToken"]["name"],
                                "symbol": token_symbol,
                                "address": token_address,
                                "price": float(pair.get("priceUsd", 0)),
                                "volume": volume,
                                "liquidity": liquidity,
                                "holders": holder_count,
                                "age_hours": (datetime.utcnow() - pair_created_at).total_seconds() / 3600,
                                "dexscreener_url": pair.get("url"),
                                "rugcheck_url": get_rugcheck_url(token_address),
                                "bubblemap_url": get_bubblemap_url(token_address),
                                "tweetscout_url": get_tweetscout_url(token_symbol),
                                "twitter_trending": token_symbol in trending_tickers
                            }
                            log_token(token_data)
                            print(f"Token logged: {token_data['name']}")

            # Fetch unsent tokens from DB and send alerts
            conn = get_db_connection()
            unsent_tokens = conn.execute('SELECT * FROM tokens WHERE telegram_alert_sent = FALSE').fetchall()
            conn.close()

            for token in unsent_tokens:
                send_telegram_alert(dict(token))

        except Exception as e:
            print(f"An error occurred in process_tokens: {e}")
        
        time.sleep(60)  # wait before checking again

def run_bot():
    thread = threading.Thread(target=process_tokens)
    thread.start()

# Start bot and web app
if __name__ == "__main__":
    run_bot()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
