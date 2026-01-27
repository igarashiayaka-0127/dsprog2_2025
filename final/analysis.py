import psycopg2
import pandas as pd

class StationAnalyzer:
    def __init__(self, db_params):
        self.db_params = db_params
        self.df = self._load_data()

    def _load_data(self):
        """DBからデータを取得し、クレンジングする内部関数"""
        conn = psycopg2.connect(**self.db_params)
        df = pd.read_sql("SELECT station_name, line_name, location FROM stations", conn)
        conn.close()
        # クレンジング処理
        exclude = ["信号場", "貨物", "廃止", "国鉄", "下河原", "須賀"]
        df = df[~df['station_name'].str.contains('|'.join(exclude))]
        return df

    def analyze_area(self, area_name):
        """【重要】入力に応じて出力が動的に変化する関数"""
        area_df = self.df[self.df['location'] == area_name]
        
        if area_df.empty:
            return f"❌ {area_name} のデータは見つかりませんでした。"
        
        # その区のハブ駅（2路線以上）を抽出
        hub_stations = area_df.groupby('station_name')['line_name'].count()
        hub_stations = hub_stations[hub_stations >= 2].sort_values(ascending=False)
        
        print(f"--- {area_name} の分析結果 ---")
        print(f"総駅数: {area_df['station_name'].nunique()}")
        print(f"主要なハブ駅:\n{hub_stations if not hub_stations.empty else 'なし'}")
        return hub_stations

# --- 実行部分 ---
if __name__ == "__main__":
    params = {"host": "localhost", "database": "dsprog2db", "user": "igarashiayaka", "password": ""}
    analyzer = StationAnalyzer(params)
    
    # ここで「入力」を変えることで「出力」が動的に変わる
    target_area = input("分析したい区を入力してください（例：大田区）: ")
    analyzer.analyze_area(target_area)