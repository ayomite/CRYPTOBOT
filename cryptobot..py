import os
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import re
import schedule
import time
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
DESTINATION_CHANNEL = os.getenv("DESTINATION_CHANNEL")

# Regex pattern to capture coin, action, amount, and price
pattern = r'([A-Z0-9]{2,10}USDT)\s+(BUY|SELL)\s+([\d\.]+)\s+@\s+([\d\.]+)'

# Whale trade threshold
WHALE_THRESHOLD = 10000  # $10,000 per single trade

async def fetch_analyze_and_post():
    async with TelegramClient('crypto_session', api_id, api_hash) as client:
        destination = await client.get_entity(DESTINATION_CHANNEL)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

        coin_stats = defaultdict(lambda: {"BUY": 0, "SELL": 0, "buy_value": 0.0, "sell_value": 0.0})
        whale_trades = []

        # Fetch messages from source channel
        source = await client.get_entity(SOURCE_CHANNEL)
        messages = await client.get_messages(source, limit=1000)

        for msg in messages:
            if msg.message and msg.date.replace(tzinfo=None) >= five_minutes_ago:
                text = msg.message.upper()
                matches = re.findall(pattern, text)

                for coin, action, amount, price in matches:
                    amount = float(amount)
                    price = float(price)
                    value = amount * price

                    if action == 'BUY':
                        coin_stats[coin]["BUY"] += 1
                        coin_stats[coin]["buy_value"] += value
                    else:
                        coin_stats[coin]["SELL"] += 1
                        coin_stats[coin]["sell_value"] += value

                    if value >= WHALE_THRESHOLD:
                        whale_trades.append((coin, action, round(amount,2), round(price,4), round(value,2)))

        now = datetime.now().strftime('%H:%M:%S')
        message = f"Market Summary (Last 5 Minutes) {now}\n\n"

        # Build summary for coins with at least 20 trades
        for coin, data in coin_stats.items():
            total_trades = data["BUY"] + data["SELL"]
            total_value = data["buy_value"] + data["sell_value"]
            if total_trades >= 20:
                buy_dom = (data["buy_value"] / total_value) * 100 if total_value else 0
                sell_dom = (data["sell_value"] / total_value) * 100 if total_value else 0

                message += (
                    f"{coin}\n"
                    f"Total trades: {total_trades}\n"
                    f"Buy: {data['BUY']} | Sell: {data['SELL']}\n"
                    f"Total trade value: ${round(total_value,2)}\n"
                    f"Total buy value: ${round(data['buy_value'],2)} | Total sell value: ${round(data['sell_value'],2)}\n"
                    f"Buy Dominance: {round(buy_dom,2)}% | Sell Dominance: {round(sell_dom,2)}%\n\n"
                )

        # Whale trades
        if whale_trades:
            message += "Whale Trades:\n"
            for coin, action, amount, price, value in whale_trades:
                message += f"{coin} {action} {amount} @ {price} = ${value}\n"

        # Send to destination
        print(message)
        # Split long messages to avoid Telegram limit
        CHUNK_SIZE = 4000
        for i in range(0, len(message), CHUNK_SIZE):
            await client.send_message(destination, message[i:i+CHUNK_SIZE])

def run_bot():
    asyncio.run(fetch_analyze_and_post())

# Schedule to run every 5 minutes
schedule.every(5).minutes.do(run_bot)

print("Bot running. Press Ctrl+C to stop.")

while True:
    schedule.run_pending()
    time.sleep(1)
