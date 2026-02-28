import requests
import json
import os

# --- 環境変数（GitHub Secretsから取得） ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
CREATOR_ID = "2c_ichimiyayui"
LIST_API = f"https://api.marche-yell.com/api/public/products?creator_marche_id={CREATOR_ID}&limit=20&page=1"
DB_FILE = "last_inventory.json"

def send_line(message):
    if not LINE_TOKEN or not USER_ID:
        print("LINE設定が不足しています")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def get_detail(p_id, headers):
    url = f"https://api.marche-yell.com/api/public/products/{p_id}?creator_marche_id={CREATOR_ID}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json()
    except:
        return None

def main():
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            last_data = json.load(f)

    # ブラウザからのアクセスを装うヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://marche-yell.com",
        "Referer": f"https://marche-yell.com/{CREATOR_ID}/"
    }

    try:
        # 商品一覧の取得
        res = requests.get(LIST_API, headers=headers, timeout=10)
        res.raise_for_status()
        
        data = res.json()
        products = data.get('data', [])

        print(f"取得した商品数: {len(products)}")

        current_data = {}

        for p in products:
            p_id = str(p.get('id'))
            title = p.get('title', '不明')
            
            # 個別詳細（正確な在庫）を取得
            detail = get_detail(p_id, headers)
            if not detail:
                continue

            # 在庫計算: 販売上限 - 販売済数
            limit = detail.get('limit_quantity', 0)
            sold = detail.get('sold_quantity', 0)
            stock = limit - sold
            
            current_data[p_id] = {"title": title, "stock": stock}

            # 【テスト用】実行するたびに必ず通知が飛ぶように設定
            msg = f"\n✅【接続テスト】一宮ゆい\n{title}\n在庫: 残り {stock} / 全 {limit}個\nhttps://marche-yell.com/{CREATOR_ID}/products/{p_id}"
            
            print(f"テスト通知送信中: {title} (ID:{p_id})")
            send_line(msg)

        # 状態を保存
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"解析エラー: {e}")

if __name__ == "__main__":
    main()
