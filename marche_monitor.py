import requests
import json
import os

# --- 設定 ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

# 【ここに追加！】監視したいクリエイターのIDをリストに入れる
TARGET_CREATORS = [
    "2c_ichimiyayui",  # 一宮ゆい
    "2c_yagiharuka"  # 八木遥叶
    "2c_matobakarin"  # 的場華鈴
    "2c_hirutaairi"  # 蛭田愛梨
    "2c_kawabatayu"  # 川端優
    "2c_itomai"  # 伊藤舞依
    "2c_kuriharamay"  # 栗原舞優
    "2c_maejimaano"  # 前嶋杏乃
    "2c_yamatoao"  # 大和明桜
    "2c_ishihamamei"  # 石浜芽衣
    "2c_obayashiyuik"  # 尾林結花
    "2c_kumamotomari"  # 隈本茉莉奈
    "2c_aoyamauta"  # 青山詩
]

DB_FILE = "last_inventory.json"

def send_line(message):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    # 前回の在庫データを読み込み
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            last_data = json.load(f)

    new_inventory_data = last_data.copy()

    for creator_id in TARGET_CREATORS:
        print(f"--- 監視中: {creator_id} ---")
        list_api = f"https://api.marche-yell.com/api/public/products?creator_marche_id={creator_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://marche-yell.com",
            "Referer": f"https://marche-yell.com/{creator_id}/"
        }

        try:
            res = requests.get(list_api, headers=headers, timeout=15)
            res.raise_for_status()
            products = res.json().get('products', [])
            
            for p in products:
                p_id = str(p.get('id'))
                title = p.get('title', '不明')
                
                # 在庫計算
                limit = p.get('limit_quantity', 0)
                sold = p.get('sold_quantity', 0)
                stock = limit - sold
                
                # 通知判定用キー（クリエイターIDと商品IDを組み合わせる）
                db_key = f"{creator_id}_{p_id}"
                
                msg = ""
                if db_key not in last_data:
                    msg = f"\n✨【新着】{creator_id}\n{title}\n在庫: {stock}個\nhttps://marche-yell.com/{creator_id}/products/{p_id}"
                elif stock > 0 and last_data[db_key]['stock'] == 0:
                    msg = f"\n🔄【復活】{creator_id}\n{title}\n残り {stock}個！\nhttps://marche-yell.com/{creator_id}/products/{p_id}"
                
                if msg:
                    send_line(msg)
                    print(f"通知送信: {title}")

                # 最新の状態を保存用変数に格納
                new_inventory_data[db_key] = {"title": title, "stock": stock}

        except Exception as e:
            print(f"エラー ({creator_id}): {e}")

    # すべてのメンバーのスキャンが終わったらデータを保存
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(new_inventory_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
