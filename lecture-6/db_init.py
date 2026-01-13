import sqlite3
import requests
import datetime
import os
import time

# ---------------------------------------------------------
# 1. データベース設定 & テーブル作成
# ---------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
dbname = os.path.join(script_dir, "weather.db")
conn = sqlite3.connect(dbname)
cur = conn.cursor()

# areas テーブル（地域マスタ）
cur.execute("""
CREATE TABLE IF NOT EXISTS areas (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    map_top INTEGER,
    map_left INTEGER
)
""")

# forecasts テーブル（天気予報データ）
cur.execute("""
CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_code TEXT,
    forecast_date TEXT,
    weather TEXT,
    FOREIGN KEY (area_code) REFERENCES areas(code)
)
""")

# ---------------------------------------------------------
# 2. 地域データの登録 (MAP_POSITIONS)
# ---------------------------------------------------------
MAP_POSITIONS = {
    "011000": {"top": 92,  "left": 185, "name": "宗谷"},
    "012000": {"top": 105, "left": 183, "name": "上川・留萌"},
    "013000": {"top": 106, "left": 196, "name": "網走・北見・紋別"},
    "014030": {"top": 121, "left": 196, "name": "十勝"},
    "014100": {"top": 120, "left": 212, "name": "釧路・根室"},
    "015000": {"top": 133, "left": 185, "name": "胆振・日高"},
    "016000": {"top": 119, "left": 178, "name": "石狩・空知・後志"},
    "017000": {"top": 142, "left": 165, "name": "渡島・檜山"},
    "020000": {"top": 161, "left": 169, "name": "青森"},
    "030000": {"top": 175, "left": 177, "name": "岩手"},
    "040000": {"top": 193, "left": 172, "name": "宮城"},
    "050000": {"top": 171, "left": 161, "name": "秋田"},
    "060000": {"top": 187, "left": 161, "name": "山形"},
    "070000": {"top": 207, "left": 163, "name": "福島"},
    "080000": {"top": 222, "left": 165, "name": "茨城"},
    "090000": {"top": 218, "left": 157, "name": "栃木"},
    "100000": {"top": 219, "left": 149, "name": "群馬"},
    "110000": {"top": 228, "left": 153, "name": "埼玉"},
    "120000": {"top": 232, "left": 163, "name": "千葉"},
    "130000": {"top": 233, "left": 154, "name": "東京"},
    "140000": {"top": 235, "left": 151, "name": "神奈川"},
    "150000": {"top": 207, "left": 149, "name": "新潟"},
    "160000": {"top": 217, "left": 129, "name": "富山"},
    "170000": {"top": 218, "left": 122, "name": "石川"},
    "180000": {"top": 229, "left": 119, "name": "福井"},
    "190000": {"top": 231, "left": 144, "name": "山梨"},
    "200000": {"top": 224, "left": 138, "name": "長野"},
    "210000": {"top": 230, "left": 125, "name": "岐阜"},
    "220000": {"top": 240, "left": 140, "name": "静岡"},
    "230000": {"top": 240, "left": 127, "name": "愛知"},
    "240000": {"top": 249, "left": 121, "name": "三重"},
    "250000": {"top": 239, "left": 117, "name": "滋賀"},
    "260000": {"top": 237, "left": 110, "name": "京都"},
    "270000": {"top": 247, "left": 111, "name": "大阪"},
    "280000": {"top": 239, "left": 101, "name": "兵庫"},
    "290000": {"top": 248, "left": 115, "name": "奈良"},
    "300000": {"top": 256, "left": 109, "name": "和歌山"},
    "310000": {"top": 236, "left": 93,  "name": "鳥取"},
    "320000": {"top": 238, "left": 76,  "name": "島根"},
    "330000": {"top": 245, "left": 91,  "name": "岡山"},
    "340000": {"top": 246, "left": 80,  "name": "広島"},
    "350000": {"top": 250, "left": 63,  "name": "山口"},
    "360000": {"top": 255, "left": 95,  "name": "徳島"}, 
    "370000": {"top": 250, "left": 88,  "name": "香川"}, 
    "380000": {"top": 259, "left": 76,  "name": "愛媛"},
    "390000": {"top": 263, "left": 84,  "name": "高知"},
    "400000": {"top": 258, "left": 55,  "name": "福岡"},
    "410000": {"top": 266, "left": 44,  "name": "佐賀"},
    "420000": {"top": 269, "left": 49,  "name": "長崎"},
    "430000": {"top": 270, "left": 56,  "name": "熊本"},
    "440000": {"top": 265, "left": 64,  "name": "大分"},
    "450000": {"top": 273, "left": 65,  "name": "宮崎"},
    "460100": {"top": 288, "left": 60,  "name": "鹿児島"},
    "460040": {"top": 243, "left": 228, "name": "奄美"},
    "471000": {"top": 267, "left": 214, "name": "沖縄本島"},
    "472000": {"top": 270, "left": 240, "name": "大東島"},
    "473000": {"top": 279, "left": 229, "name": "宮古島"},
    "474000": {"top": 286, "left": 221, "name": "八重山"},
}

try:
    # 地域データを登録 (INSERT OR REPLACE)
    data_to_insert = []
    for code, info in MAP_POSITIONS.items():
        data_to_insert.append((code, info["name"], info["top"], info["left"]))

    cur.executemany("""
        INSERT OR REPLACE INTO areas (code, name, map_top, map_left)
        VALUES (?, ?, ?, ?)
    """, data_to_insert)
    conn.commit()
    print("✅ areasテーブルの準備完了！")

except Exception as e:
    print(f"エリア登録エラー: {e}")


# ---------------------------------------------------------
# 3. APIから天気データを取得して保存する (ここから追加部分！)
# ---------------------------------------------------------

# 古い予報データは一旦削除（リセット）
cur.execute("DELETE FROM forecasts")
conn.commit()

# 一部の地域コードはAPIのエンドポイントが違うのでリダイレクト設定
REDIRECT_MAP = {"014030": "014100", "460040": "460100"}

def get_forecast_from_jma(area_code):
    """気象庁APIからデータを取得して整形する関数"""
    
    # リダイレクトが必要ならコードを書き換える
    target_code = REDIRECT_MAP.get(area_code, area_code)
    
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{target_code}.json"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code != 200: return None
        data = res.json()
    except:
        return None

    try:
        report = data[0]
        # 天気予報(weathers)が含まれているエリアを探す
        ts_weather = None
        for ts in report["timeSeries"]:
            # 'weathers'キーがあるデータセットを探す
            if "areas" in ts and ts["areas"] and "weathers" in ts["areas"][0]:
                ts_weather = ts
                break
        
        if not ts_weather: return None

        dates = ts_weather["timeDefines"]
        weather_area = ts_weather["areas"][0] # 簡易的にリストの先頭の地域を使う
        weathers = weather_area["weathers"]
        
        # (日付, 天気) のリストを作成
        results = []
        for i in range(len(weathers)):
            if i >= len(dates): break
            
            # 日付の変換 (ISO形式 -> YYYY-MM-DD)
            dt = datetime.datetime.fromisoformat(dates[i].replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
            
            # 天気の全角スペースを半角に
            weather_text = weathers[i].replace("　", " ")
            
            results.append((date_str, weather_text))
            
        return results

    except Exception as e:
        print(f"解析エラー({area_code}): {e}")
        return None

print("🚀 天気データの取得を開始します...")

# DBに登録した全エリアに対してAPIを実行
cur.execute("SELECT code, name FROM areas")
all_areas = cur.fetchall()

for code, name in all_areas:
    
    
    forecasts = get_forecast_from_jma(code)
    
    if forecasts:
        # 取得できたデータをforecastsテーブルに保存
        for f_date, f_weather in forecasts:
            cur.execute("""
                INSERT INTO forecasts (area_code, forecast_date, weather)
                VALUES (?, ?, ?)
            """, (code, f_date, f_weather))
        print(" OK!")
    else:
        print(" 失敗 (データなし)")
    
    # サーバー負荷軽減のため少し待つ
    time.sleep(0.5)

# 最後に変更を確定して閉じる
conn.commit()
conn.close()

print("\n🎉 全て完了しました！ weather.db にデータが入りました。")