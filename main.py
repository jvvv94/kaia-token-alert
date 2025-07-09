import requests
import asyncio
import os
from telegram import Bot

# 환경 변수로부터 값 가져오기
ADDRESS = os.getenv("ADDRESS")
TOKEN_API_URL = f"https://api.kaiascan.io/api/v1/txs?address={ADDRESS}&limit=10"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 반복 주기 (초 단위)
CHECK_INTERVAL = 600  # 10분

# 봇 객체 초기화
bot = Bot(token=TELEGRAM_TOKEN)
seen_token_hashes = set()

async def check_new_token_txs():
    try:
        print("[INFO] Checking new token txs...")  # Railway log 확인용
        res = requests.get(TOKEN_API_URL, timeout=10)
        res.raise_for_status()
        data = res.json()
        txs = data.get("data", [])

        for tx in txs:
            tx_hash = tx.get("txHash")
            to_addr = tx.get("to")
            symbol = tx.get("symbol")
            decimals = int(tx.get("decimals", 18))
            amount = int(tx.get("amount", 0)) / (10 ** decimals)

            if tx_hash not in seen_token_hashes and to_addr and to_addr.lower() == ADDRESS.lower():
                message = (
                    f"[📥 토큰 입금 감지]\n"
                    f"Token: {symbol}\n"
                    f"Amount: {amount}\n"
                    f"From: {tx['from']}\n"
                    f"TxHash: {tx_hash}"
                )
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                seen_token_hashes.add(tx_hash)

    except Exception as e:
        print(f"[ERROR] {e}")

async def main_loop():
    while True:
        await check_new_token_txs()
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("[STOP] Bot manually stopped.")
