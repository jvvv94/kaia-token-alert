import requests
import time
import telegram
import os
import logging

# === 로깅 설정 ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === 환경 변수 읽기 ===
ADDRESS = os.getenv("ADDRESS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 600  # 초 단위 (600초 = 10분)

# === 환경변수 체크 ===
if not ADDRESS or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("환경변수(ADDRESS, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)를 모두 설정해주세요.")

# === API URL 정의 ===
TOKEN_API_URL = f"https://api.kaiascan.io/api/v1/txs?address={ADDRESS}&limit=10"

# === Telegram 봇 설정 ===
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# === 중복 트랜잭션 방지용 캐시 ===
MAX_SEEN = 20
seen_token_hashes = []

def check_new_token_txs():
    try:
        res = requests.get(TOKEN_API_URL)
        res.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        data = res.json()
        txs = data.get("data", [])

        for tx in txs:
            tx_hash = tx.get("txHash")
            to_addr = tx.get("to")
            symbol = tx.get("symbol")
            decimals = int(tx.get("decimals", 18))
            amount = int(tx.get("amount", 0)) / (10 ** decimals)

            # 입금 감지 + 중복 방지
            if tx_hash not in seen_token_hashes and to_addr and to_addr.lower() == ADDRESS.lower():
                message = (
                    f"[📥 토큰 입금 감지]\n"
                    f"Token: {symbol}\n"
                    f"Amount: {amount}\n"
                    f"From: {tx['from']}\n"
                    f"TxHash: {tx_hash}"
                )
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                logging.info(f"📬 알림 전송됨: {tx_hash}")

                # 해시 추가 및 리스트 제한
                seen_token_hashes.append(tx_hash)
                if len(seen_token_hashes) > MAX_SEEN:
                    seen_token_hashes.pop(0)

    except Exception as e:
        logging.error(f"[오류 발생] {e}")

# === 루프 실행 ===
if __name__ == "__main__":
    logging.info("🔍 토큰 입금 감지기 실행 시작")
    while True:
        check_new_token_txs()
        time.sleep(CHECK_INTERVAL)
