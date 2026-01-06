import flet as ft
import requests
import datetime
import traceback

def main(page: ft.Page):
    # --- アプリの基本設定 ---
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#E0E5EC"

    # ==========================================
    # 0. 捜索用：広域エリアのコードリスト
    # ==========================================
    # 特定の地域のファイルがない(404)場合、これらの「親分ファイル」を一斉捜索します
    # (北海道全体, 東北, 関東, ..., 九州, 鹿児島, 沖縄)
    # これで「奄美」や「十勝」など、間借りしている地域も拾い上げます
    SEARCH_TARGETS = [
        "016000", # 北海道（札幌）
        "014100", # 北海道（釧路・十勝対策）
        "012000", # 北海道（旭川）
        "017000", # 北海道（函館）
        "460100", # 鹿児島（奄美対策）
        "471000", # 沖縄
        "010000", # 全国（念のため）
    ]

    # ==========================================
    # 1. データ取得・解析ロジック
    # ==========================================
    
    def get_weather_icon(weather_text):
        text = weather_text.lower()
        if "晴" in text: return ft.Icons.WB_SUNNY, "orange"
        elif "雨" in text: return ft.Icons.UMBRELLA, "blue"
        elif "雪" in text: return ft.Icons.AC_UNIT, "cyan"
        elif "くもり" in text or "曇" in text: return ft.Icons.CLOUD, "grey"
        else: return ft.Icons.WB_CLOUDY_OUTLINED, "blueGrey"

    def fetch_json(url):
        try:
            res = requests.get(url, timeout=3) # 捜索用にタイムアウトを短めに
            if res.status_code == 200:
                return res.json()
        except:
            pass
        return None

    def get_forecast_data(target_code, target_name):
        print(f"--- 取得開始: {target_name} ({target_code}) ---")
        
        # 1. まずは「その地域のコード」で素直にアクセス（基本ルート）
        url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{target_code}.json"
        data = fetch_json(url)
        
        found_mode = False # 捜索モードで見つけたかどうかのフラグ

        # 2. もしダメ(404)なら、親分リストから一斉捜索（救済ルート）
        if data is None:
            print(f"⚠️ {target_code} が見つかりません。他のファイルを捜索します...")
            
            # 検索キーワード作成（「奄美地方」→「奄美」など）
            search_key = target_name.replace("地方", "").replace("県", "").replace("府", "").replace("都", "")
            
            for code in SEARCH_TARGETS:
                # 自分自身はさっき試したのでスキップ
                if code == target_code: continue
                
                check_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
                temp_data = fetch_json(check_url)
                
                if temp_data:
                    # このファイルの中に、探している地名があるか確認
                    try:
                        report = temp_data[0]
                        for ts in report["timeSeries"]:
                            if "areas" in ts:
                                for area in ts["areas"]:
                                    if search_key in area["area"]["name"]:
                                        # 見つけた！！
                                        print(f"✅ {code} のファイル内で {target_name} を発見！")
                                        data = temp_data
                                        found_mode = True
                                        break
                            if found_mode: break
                    except:
                        pass
                
                if found_mode: break

        if data is None:
            return "取得失敗", []

        # --- JSON解析 ---
        try:
            report = data[0]
            
            # 天気情報(weathers)が入っている場所を探す
            ts_weather = None
            for ts in report["timeSeries"]:
                if "areas" in ts and ts["areas"] and "weathers" in ts["areas"][0]:
                    ts_weather = ts
                    break
            
            if not ts_weather:
                return "データなし", []

            dates = ts_weather["timeDefines"]
            weather_areas = ts_weather["areas"]
            display_list = []

            # 検索用キーワード再確認
            search_key = target_name.replace("地方", "").replace("県", "").replace("府", "").replace("都", "")

            for w_area in weather_areas:
                area_n = w_area["area"]["name"]
                
                # 【ここが重要】
                # 捜索モード(found_mode=True)で見つけた時は、名前が合うデータだけを拾う
                # 普通に取得できた時は、全部表示する（ただし、明らかに違う地域のデータが混ざらないように、念のため名前チェックを入れても良い）
                if found_mode:
                    if search_key not in area_n:
                        continue # 名前が一致しないエリアは飛ばす（例：鹿児島ファイルの中の鹿児島エリアなど）

                weathers = w_area["weathers"]
                for i in range(len(weathers)):
                    if i >= len(dates): break
                    try:
                        dt = datetime.datetime.fromisoformat(dates[i].replace("Z", "+00:00"))
                        date_str = dt.strftime("%m/%d")
                        w_day = ["月","火","水","木","金","土","日"][dt.weekday()]
                        date_disp = f"{date_str} ({w_day})"
                    except:
                        date_disp = "日付不明"

                    display_list.append({
                        "sub_area": area_n,
                        "date": date_disp,
                        "weather": weathers[i].replace("　", " ")
                    })

            # リストが空なら
            if not display_list:
                return "データなし", []

            return target_name, display_list

        except Exception as e:
            print(f"解析エラー: {e}")
            traceback.print_exc()
            return "エラー", []

    # ==========================================
    # 2. UIコンポーネント
    # ==========================================

    def create_card(info):
        icon, color = get_weather_icon(info['weather'])
        return ft.Container(
            width=200, height=220, bgcolor="white", border_radius=15, padding=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black26"),
            content=ft.Column(
                controls=[
                    ft.Text(info['sub_area'], size=14, weight="bold", color="blueGrey700"),
                    ft.Text(info['date'], size=12, color="grey"),
                    ft.Divider(height=1, color="grey200"),
                    ft.Container(content=ft.Icon(icon, size=48, color=color), alignment=ft.alignment.center, padding=10),
                    ft.Text(info['weather'], size=13, text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    grid_view = ft.Row(wrap=True, spacing=20, run_spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
    main_title = ft.Text("地域を選択してください", size=24, weight="bold", color="white")

    def update_view(area_name, forecasts):
        if isinstance(forecasts, tuple): _, data_list = forecasts
        else: data_list = forecasts

        main_title.value = f"{area_name} の天気"
        grid_view.controls.clear()
        
        if not data_list:
            grid_view.controls.append(ft.Text("データを取得できませんでした。", color="white"))
        else:
            for info in data_list:
                grid_view.controls.append(create_card(info))
        page.update()

    def on_sidebar_click(e):
        code = e.control.data["code"]
        name = e.control.data["name"]
        main_title.value = f"{name} を読込中..."
        page.update()
        
        forecasts = get_forecast_data(code, name)
        update_view(name, forecasts)

    # ==========================================
    # 3. サイドバー構築
    # ==========================================
    sidebar_content = ft.Column(scroll=ft.ScrollMode.AUTO)
    sidebar_content.controls.append(ft.Container(padding=20, content=ft.Text("地域リスト", color="white", size=20, weight="bold")))

    try:
        area_url = "https://www.jma.go.jp/bosai/common/const/area.json"
        area_res = requests.get(area_url, timeout=5).json()
        centers = area_res['centers']
        offices = area_res['offices']
        
        for center_code, center_info in centers.items():
            office_buttons = []
            for child_code in center_info['children']:
                if child_code in offices:
                    office_name = offices[child_code]['name']
                    office_buttons.append(
                        ft.ListTile(
                            title=ft.Text(office_name, color="white70"),
                            leading=ft.Icon(ft.Icons.LOCATION_ON, color="white70", size=16),
                            data={"code": child_code, "name": office_name},
                            on_click=on_sidebar_click,
                            hover_color="white10",
                        )
                    )
            if office_buttons:
                sidebar_content.controls.append(
                    ft.ExpansionTile(
                        title=ft.Text(center_info['name'], color="white", weight="bold"),
                        controls=office_buttons,
                        icon_color="white", collapsed_icon_color="white", bgcolor="transparent",
                    )
                )
    except:
        sidebar_content.controls.append(ft.Text("リスト取得エラー", color="red"))

    sidebar = ft.Container(width=260, bgcolor="#263238", content=sidebar_content)
    header = ft.Container(height=60, bgcolor="#303F9F", padding=ft.padding.only(left=20),
                          content=ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color="white"), ft.Text("日本気象庁 天気予報", color="white", size=20, weight="bold")]))
    main_area = ft.Container(expand=True, padding=30, bgcolor="#546E7A",
                             content=ft.Column([main_title, ft.Divider(color="white54"), grid_view]))

    page.add(header, ft.Row([sidebar, main_area], expand=True, spacing=0))

ft.app(target=main)