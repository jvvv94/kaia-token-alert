import requests
import time
import telegram

# === 설정값 ===
ADDRESS = os.environ["WALLET_ADDRESS"]  # TODO: 감시할 지갑 주소 (0x부터 시작)
TOKEN_API_URL = f"https://api.kaiascan.io/api/v1/txs?address={ADDRESS}&limit=10"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]  # TODO: @BotFather에게 받은 봇 토큰
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # TODO: @userinfobot에게 받은 ID

CHECK_INTERVAL = 600  # 단위: 초 (600초 = 10분)

seen_token_hashes = set()
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def check_new_token_txs():
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

            # 내 주소로 들어온 토큰 입금 + 중복 방지
            if tx_hash not in seen_token_hashes and to_addr and to_addr.lower() == ADDRESS.lower():
                message = (
                    f"[📥 토큰 입금 감지]\n"
                    f"Token: {symbol}\n"
                    f"Amount: {amount}\n"
                    f"From: {tx['from']}\n"
                    f"TxHash: {tx_hash}"
                )
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                seen_token_hashes.add(tx_hash)

    except Exception as e:
        print(f"[오류] {e}")

if __name__ == "__main__":
    while True:
        check_new_token_txs()
        time.sleep(CHECK_INTERVAL)
