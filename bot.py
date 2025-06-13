import tweepy
from datetime import datetime
import yfinance as yf
import pytz
import time
import schedule


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
market_close_tweeted = False
last_open_date = None
last_close_date = None


def is_market_open_today():
    nyse = mcal.get_calendar('NYSE')
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    schedule_today = nyse.schedule(start_date=ny_time.date(), end_date=ny_time.date())
    return not schedule_today.empty  # True if market open today, False if weekend/holiday


# === Fetch current S&P 500 price using yfinance ===
def fetch_sp500():
    try:
        ticker = "^GSPC" # S&P 500 index
        price = yf.download(ticker, period='1d', interval='30m', progress=False)
        price = (price['Close'].iloc[-1].item())
        return float(price)
    except Exception as e:
        print("Error fetching S&P 500 via yfinance:", e)
        return None
    


# === Compose and send tweet ===
def tweet_sp500():
    global last_price, market_open_tweeted, market_close_tweeted, last_open_date, last_close_date
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    hour, minute = ny_time.hour, ny_time.minute
    today = ny_time.date()

    # Skip if market closed
    if not is_market_open_today():
        print(f"[{ny_time.strftime('%Y-%m-%d %H:%M')}] Market closed today.")
        market_open_tweeted = False
        market_close_tweeted = False
        last_open_date = None
        last_close_date = None
        return

    # Market Open tweet once per day at or after 9:30 AM ET
    if (hour == 9 and minute >= 30) or (hour > 9):
        if last_open_date != today:
            try:
                client.create_tweet(text="Market Open")
                print(f"[{ny_time.strftime('%H:%M')}] ✅ Tweeted: Market Open")
                last_open_date = today
            except Exception as e:
                print(f"❌ Failed to tweet Market Open: {e}")

    # Market Close tweet once per day exactly at 16:01 ET
    if hour == 16 and minute == 1:
        if last_close_date != today:
            try:
                client.create_tweet(text="Market Close")
                print(f"[{ny_time.strftime('%H:%M')}] ✅ Tweeted: Market Close")
                last_close_date = today
                last_price = None  # reset price
                market_open_tweeted = False
                market_close_tweeted = True
            except Exception as e:
                print(f"❌ Failed to tweet Market Close: {e}")
        return  # skip price tweet this minute

    # Market price tweets during market hours 9:30 - 16:00
    if (hour == 9 and minute >= 30) or (10 <= hour <= 16):
        price = fetch_sp500()
        if price is None:
            print(f"[{ny_time.strftime('%H:%M')}] Could not fetch price.")
            return

        if last_price is None:
            emoji = "🟢⬆️"
        elif price > last_price:
            emoji = "🟢⬆️"
        elif price < last_price:
            emoji = "🔴⬇️"
        else:
            emoji = "⚪➖"

        tweet = f"S&P 500 Index: {price:.2f} {emoji}"
        try:
            client.create_tweet(text=tweet)
            print(f"[{ny_time.strftime('%H:%M')}] ✅ Tweeted: {tweet}")
            last_price = price
        except Exception as e:
            print(f"❌ Failed to tweet price: {e}")
    else:
        print(f"[{ny_time.strftime('%H:%M')}] Market closed (outside trading hours).")

# === Schedule every hour ===
schedule.every().hour.at(":08").do(tweet_sp500)
schedule.every().hour.at(":30").do(tweet_sp500)

print("Bot running... Tweeting S&P 500 1/2 hour with arrows and color indicators!")

# === Run loop ===
while True:
    schedule.run_pending()
    time.sleep(10)