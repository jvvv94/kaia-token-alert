import os
import asyncio
import requests
import json
from telegram import Bot

# ⛳ 환경 변수
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
KAIASCAN_API_KEY = os.getenv("KAIASCAN_API_KEY")

# 📦 여러 주소 감시: JSON 배열 형태로 받아 처리
ADDRESS_LIST = json.loads(os.getenv("ADDRESS_LIST", "[]"))

# 🕓 주기 설정 (10분)
CHECK_INTERVAL = 600  # 초

# 🤖 텔레그램 봇 초기화
bot = Bot(token=TELEGRAM_TOKEN)

# ✅ 이미 본 트랜잭션 해시 저장용
seen_token_hashes = set()

async def check_new_token_txs():
    try:
        print("[INFO] Checking token txs for all wallets...")

        headers = {"x-api-key": KAIASCAN_API_KEY}

        for address in ADDRESS_LIST:
            url = f"https://mainnet-oapi.kaiascan.io/api/v1/accounts/{address}/token-transfers"
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()
            txs = data.get("results", [])  # ← 수정됨

            for tx in txs:
                tx_hash = tx.get("txHash")
                to_addr = tx.get("to", "").lower()
                from_addr = tx.get("from", "").lower()
                symbol = tx.get("symbol")
                decimals = int(tx.get("decimals", 18))
                amount = float(tx.get("amount", 0))  # ← 수정됨

                # 중복 방지
                if tx_hash in seen_token_hashes:
                    continue

                # 입금 또는 출금 여부 판단
                direction = None
                if to_addr == address.lower():
                    direction = "📥 [Token Received]"
                elif from_addr == address.lower():
                    direction = "📤 [Token Sent]"

                if direction:
                    message = (
                        f"{direction}\n"
                        f"Address: {address}\n"
                        f"Token: {symbol}\n"
                        f"Amount: {amount:.4f}\n"
                        f"From: {tx['from']}\n"
                        f"To: {tx['to']}\n"
                        f"TxHash: {tx_hash}"
                    )
                    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                    seen_token_hashes.add(tx_hash)

    except Exception as e:
        print(f"[ERROR] {e}")

async def main_loop():
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🔔 Monitoring started for token transfers (입출금 포함).")
    while True:
        await check_new_token_txs()
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())
