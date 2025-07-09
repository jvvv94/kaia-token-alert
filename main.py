import os
import asyncio
import requests
from telegram import Bot

# ⛳ 환경 변수
ADDRESS = os.getenv("ADDRESS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ✅ 감지 대상 API (KAIA Scan)
TOKEN_API_URL = f"https://oapi.kaiascan.io/api/v1/txs?address={ADDRESS}&limit=10"

# 🕓 주기 설정 (10분)
CHECK_INTERVAL = 600  # 초

# 🤖 텔레그램 봇 초기화
bot = Bot(token=TELEGRAM_TOKEN)

# ✅ 이미 본 트랜잭션 해시 저장용
seen_token_hashes = set()

async def check_new_token_txs():
    print("[INFO] Checking new token txs...")
    try:
        res = requests.get(TOKEN_API_URL)
        data = res.json()
        txs = data.get("data", [])

        for tx in txs:
            tx_hash = tx.get("txHash")
            to_addr = tx.get("to")
            symbol = tx.get("symbol")
            decimals = int(tx.get("decimals", 18))
            amount = int(tx.get("amount", 0)) / (10 ** decimals)

            # 🧐 새로운 트랜잭션이면서 내 주소로 입금된 경우
            if tx_hash not in seen_token_hashes and to_addr and to_addr.lower() == ADDRESS.lower():
                message = (
                    f"📥 [Token Received]\n"
                    f"Token: {symbol}\n"
                    f"Amount: {amount:.4f}\n"
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
    asyncio.run(main_loop())
