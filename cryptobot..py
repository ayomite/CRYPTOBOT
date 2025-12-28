from telethon import TelegramClient
import asyncio
from datetime import datetime, timedelta
from collections import Counter
import re
import schedule
import time

api_id = 37993462
api_hash = '7c1330238eb31eee84767fb8112b20e3'

SOURCE_CHANNEL = 'https://t.me/REKTbinance'
DESTINATION_CHANNEL = 'ElearnerTrader'

pattern = r'([A-Z]{2,10}USDT)\s*(BUY|SELL)'

async def fetch_analyze_and_post():
    async with TelegramClient('crypto_session', api_id, api_hash) as client:
        source = await client.get_entity(SOURCE_CHANNEL)
        destination = await client.get_entity(DESTINATION_CHANNEL)

        messages = await client.get_messages(source, limit=1000)
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)

        buy_counter = Counter()
        sell_counter = Counter()

        for msg in messages:
            if msg.message and msg.date.replace(tzinfo=None) >= one_minute_ago:
                text = msg.message.upper()
                matches = re.findall(pattern, text)
                for coin, action in matches:
                    if action == 'BUY':
                        buy_counter[coin] += 1
                    elif action == 'SELL':
                        sell_counter[coin] += 1

        now = datetime.now().strftime('%H:%M:%S')

        message = f"Market Activity ({now})\n\n"

        if buy_counter:
            message += "Most Bought Coins:\n"
            for coin, count in buy_counter.most_common():
                message += f"{coin} ({count})\n"
        else:
            message += "Most Bought Coins: None\n"

        if sell_counter:
            message += "\nMost Sold Coins:\n"
            for coin, count in sell_counter.most_common():
                message += f"{coin} ({count})\n"
        else:
            message += "Most Sold Coins: None\n"

        print(message)
        await client.send_message(destination, message)

def run_bot():
    asyncio.run(fetch_analyze_and_post())

schedule.every(1).minutes.do(run_bot)

print("Bot running. Press Ctrl+C to stop.")

while True:
    schedule.run_pending()
    time.sleep(1)
