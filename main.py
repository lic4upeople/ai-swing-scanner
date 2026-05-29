import yfinance as yf
import requests
import gspread

from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

if os.getenv("GOOGLE_CREDENTIALS"):
    with open("credentials.json", "w") as f:
        f.write(os.getenv("GOOGLE_CREDENTIALS"))
# ==============================
# TELEGRAM SETTINGS
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# GOOGLE SHEET SETTINGS
# ==============================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/19RRDAe2sr2FHdc2s3qO1-fcBFaRQ6NtVNXpCUZO_oOQ/edit?gid=0#gid=0").sheet1

# ==============================
# TELEGRAM FUNCTION
# ==============================

def send_telegram_message(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

# ==============================
# STOCK LIST
# ==============================

stocks = [
    "BEL.NS",
    "HAL.NS",
    "BSE.NS",
    "TRENT.NS",
    "RVNL.NS",
    "KPITTECH.NS",
    "TATAPOWER.NS",
    "ADANIPORTS.NS",
    "COCHINSHIP.NS",
    "POLYCAB.NS"
]

print("\n========== AI SWING TRADING SCANNER ==========\n")

for stock in stocks:

    try:

        # Download data
        df = yf.download(stock, period="6mo", interval="1d", auto_adjust=True)

        # Convert series
        close_series = df['Close'].squeeze()
        volume_series = df['Volume'].squeeze()

        # Indicators
        rsi_indicator = RSIIndicator(close=close_series, window=14)
        ema_indicator = EMAIndicator(close=close_series, window=20)

        df['RSI'] = rsi_indicator.rsi()
        df['EMA20'] = ema_indicator.ema_indicator()

        # Latest values
        close = round(float(close_series.iloc[-1]), 2)
        rsi = round(float(df['RSI'].iloc[-1]), 2)
        ema20 = round(float(df['EMA20'].iloc[-1]), 2)

        latest_volume = float(volume_series.iloc[-1])
        avg_volume = float(volume_series.mean())

        # AI Score
        score = 0

        if rsi > 55 and rsi < 75:
            score += 40

        if close > ema20:
            score += 30

        if latest_volume > avg_volume:
            score += 30

        # Signal
        if score >= 60:
            signal = "STRONG BUY"
        elif score >= 40:
            signal = "WATCH"
        else:
            signal = "AVOID"

        # Entry / SL / Target
        entry = close
        sl = round(close * 0.95, 2)
        target = round(close * 1.08, 2)

        # Save to Google Sheet
        current_date = datetime.now().strftime("%Y-%m-%d")

        sheet.append_row([
            current_date,
            stock,
            close,
            rsi,
            score,
            signal,
            entry,
            sl,
            target
        ])

        # Telegram Alert
        if signal == "STRONG BUY":

            telegram_message = f"""
🔥 AI SWING ALERT 🔥

Stock: {stock}

Price: ₹{close}
RSI: {rsi}
AI Score: {score}/100

Signal: {signal}

Entry: ₹{entry}
Stop Loss: ₹{sl}
Target: ₹{target}
"""

            send_telegram_message(telegram_message)

        print(f"{stock} Done")

    except Exception as e:
        print(f"Error in {stock}: {e}")

print("\nScanner Completed Successfully")
