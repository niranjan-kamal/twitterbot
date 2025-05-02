import tweepy
from datetime import datetime
import yfinance as yf
import pytz
import time
import schedule

from keepalive import keep_alive    # Keep the server alive
keep_alive()  # Start the keepalive service

# Read Twitter keys from environment
api_key = 'Dv8pLXF0bvqJCZdTuwrf4p3Ee'
api_secret = 'IoU2WXXlUo0bJJv5U8V1zkskQJZuwYyxPM4zJqhAsmITMeFki3'
access_token = '1917090769652891648-xwhbwvjZAfNRj0HCSAieNRI5I5wWof'
access_token_secret = 'LPIPzbWuzZ5bT0in6QzQWA3pOX28fjbmcxbzTbNgq3zRK'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAAu30wEAAAAA5s5ab822RYztyYEnMEDLqQSMDbA%3D9nBAKloBcEm2DhtBaxguCecmp1O8pOkgEF5jhk3g4oaZjpNr97'

# Initialize Tweepy Client (API v2)
client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    wait_on_rate_limit=True,
)
# Track the last posted price
last_price = None

# === Fetch current S&P 500 price using yfinance ===
def fetch_sp500():
    try:
        ticker = yf.Ticker("^GSPC")  # S&P 500 index
        price = ticker.history(period="1d", interval="1m")["Close"].dropna().iloc[-1]
        return float(price)
    except Exception as e:
        print("Error fetching S&P 500 via yfinance:", e)
        return None

# === Compose and send tweet ===
def tweet_sp500():
    global last_price
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    hour, minute = ny_time.hour, ny_time.minute

    # Market hours: 9:30 AM to 4 PM (ET)
    if (hour == 9 and minute >= 30) or (10 <= hour < 16):
        price = fetch_sp500()
        if price:
            if last_price is None:
                emoji = "🟢⬆️"  # green up arrow
            elif price > last_price:
                emoji = "🟢⬆️"  # green up arrow
            elif price < last_price:
                emoji = "🔴⬇️"  # red down arrow
            else:
                emoji = "⚪➖"  # white unchanged

            tweet = f"S&P 500 Index: {price:.2f} {emoji}"
            try:
                response = client.create_tweet(text=tweet)
                print(f"[{ny_time.strftime('%H:%M')}] ✅ Tweeted: {tweet}")
                last_price = price
            except Exception as e:
                print(f"❌ Failed to tweet: {e}")
        else:
            print("Could not fetch price.")
    else:
        print(f"[{ny_time.strftime('%H:%M')}] Market closed.")

# === Tweet once immediately at start ===
try:
    client.create_tweet(text="Hi SP500!!!!!! \n\nI am activated!📈🐂💰 ")
except Exception as e:
    print("❌ Failed to tweet:", e)

# === Schedule every hour ===
schedule.every().hour.at(":00").do(tweet_sp500)
schedule.every().hour.at(":30").do(tweet_sp500)

print("Bot running... Tweeting S&P 500 1/2 hour with arrows and color indicators!")

# === Run loop ===
while True:
    schedule.run_pending()
    time.sleep(10)
