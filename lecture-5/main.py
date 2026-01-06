import flet as ft
import requests
import datetime
import traceback
import os

def main(page: ft.Page):
    # --- アプリの基本設定 ---
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#E0E5EC"
    page.window_width = 1200 

    # ==========================================
    # 0. 地図の位置設定 (全国完全対応版)
    # ==========================================
    MAP_POSITIONS = {
        # --- 北海道 ---
        "011000": {"top": 91,  "left": 184, "name": "宗谷"},
        "012000": {"top": 105, "left": 183, "name": "上川・留萌"},
        "013000": {"top": 106, "left": 196, "name": "網走・北見・紋別"},
        "014030": {"top": 121, "left": 196, "name": "十勝"},
        "014100": {"top": 120, "left": 212, "name": "釧路・根室"},
        "015000": {"top": 133, "left": 185, "name": "胆振・日高"},
        "016000": {"top": 119, "left": 178, "name": "石狩・空知・後志"},
        "017000": {"top": 142, "left": 165, "name": "渡島・檜山"},

        # --- 東北 ---
        "020000": {"top": 161, "left": 169, "name": "青森"},
        "030000": {"top": 175, "left": 177, "name": "岩手"},
        "040000": {"top": 193, "left": 172, "name": "宮城"},
        "050000": {"top": 171, "left": 161, "name": "秋田"},
        "060000": {"top": 187, "left": 161, "name": "山形"},
        "070000": {"top": 207, "left": 163, "name": "福島"},

        # --- 関東甲信 ---
        "080000": {"top": 222, "left": 165, "name": "茨城"},
        "090000": {"top": 218, "left": 157, "name": "栃木"},
        "100000": {"top": 219, "left": 149, "name": "群馬"},
        "110000": {"top": 228, "left": 153, "name": "埼玉"},
        "120000": {"top": 232, "left": 163, "name": "千葉"},
        "130000": {"top": 233, "left": 154, "name": "東京"},
        "140000": {"top": 235, "left": 151, "name": "神奈川"},
        "190000": {"top": 231, "left": 144, "name": "山梨"},
        "200000": {"top": 224, "left": 138, "name": "長野"},

        # --- 北陸・東海 ---
        "150000": {"top": 207, "left": 149, "name": "新潟"},
        "160000": {"top": 217, "left": 129, "name": "富山"},
        "170000": {"top": 218, "left": 122, "name": "石川"},
        "180000": {"top": 229, "left": 119, "name": "福井"},
        "210000": {"top": 230, "left": 125, "name": "岐阜"},
        "220000": {"top": 240, "left": 140, "name": "静岡"},
        "230000": {"top": 240, "left": 127, "name": "愛知"},
        "240000": {"top": 249, "left": 121, "name": "三重"},

        # --- 近畿 ---
        "250000": {"top": 239, "left": 117, "name": "滋賀"},
        "260000": {"top": 237, "left": 110, "name": "京都"},
        "270000": {"top": 247, "left": 111, "name": "大阪"},
        "280000": {"top": 239, "left": 101, "name": "兵庫"},
        "290000": {"top": 248, "left": 115, "name": "奈良"},
        "300000": {"top": 256, "left": 109, "name": "和歌山"},

        # --- 中国 ---
        "310000": {"top": 236, "left": 93,  "name": "鳥取"},
        "320000": {"top": 238, "left": 76,  "name": "島根"},
        "330000": {"top": 245, "left": 91,  "name": "岡山"},
        "340000": {"top": 246, "left": 80,  "name": "広島"},
        "350000": {"top": 250, "left": 63,  "name": "山口"},

        # --- 四国 ---
        "360000": {"top": 255, "left": 95,  "name": "徳島"},
        "370000": {"top": 250, "left": 88,  "name": "香川"},
        "380000": {"top": 259, "left": 76,  "name": "愛媛"},
        "390000": {"top": 263, "left": 84,  "name": "高知"},

        # --- 九州 ---
        "400000": {"top": 258, "left": 55,  "name": "福岡"},
        "410000": {"top": 266, "left": 44,  "name": "佐賀"},
        "420000": {"top": 269, "left": 49,  "name": "長崎"},
        "430000": {"top": 270, "left": 56,  "name": "熊本"},
        "440000": {"top": 265, "left": 64,  "name": "大分"},
        "450000": {"top": 273, "left": 65,  "name": "宮崎"},
        "460100": {"top": 288, "left": 60,  "name": "鹿児島"},
        
        # --- 離島 ---
        "460040": {"top": 243, "left": 228, "name": "奄美"},
        "471000": {"top": 267, "left": 214, "name": "沖縄本島"},
        "472000": {"top": 270, "left": 240, "name": "大東島"},
        "473000": {"top": 279, "left": 229, "name": "宮古島"},
        "474000": {"top": 286, "left": 221, "name": "八重山"},
        
        # 予備の地方全体コード（県データがない場合の保険）
        "010100": {"top": 56,  "left": 245, "name": "北海道"},
        "010200": {"top": 120, "left": 215, "name": "東北"},
        "010300": {"top": 200, "left": 200, "name": "関東甲信"},
        "010400": {"top": 210, "left": 165, "name": "東海"},
        "010500": {"top": 170, "left": 160, "name": "北陸"},
        "010600": {"top": 220, "left": 135, "name": "近畿"},
        "010700": {"top": 210, "left": 80,  "name": "中国"},
        "010800": {"top": 250, "left": 90,  "name": "四国"},
        "010900": {"top": 230, "left": 40,  "name": "九州北部"},
        "011000": {"top": 280, "left": 40,  "name": "九州南部"},
        "011100": {"top": 330, "left": 10,  "name": "沖縄"},
    }

    # ==========================================
    # 設定データ
    # ==========================================
    REDIRECT_MAP = {"014030": "014100", "460040": "460100"}
    SEARCH_TARGETS = ["016000", "014100", "012000", "017000", "460100", "471000", "010000"]
    office_to_center = {}

    # ==========================================
    # 1. ロジック
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
            res = requests.get(url, timeout=3)
            if res.status_code == 200: return res.json()
        except: pass
        return None

    def get_forecast_data(target_code, target_name):
        url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{target_code}.json"
        data = fetch_json(url)
        found_mode = False

        if data is None:
            # 404の場合の捜索ロジック
            search_key = target_name.replace("地方", "").replace("県", "").replace("府", "").replace("都", "")
            
            # 1. 救済マップで探す
            if target_code in REDIRECT_MAP:
                alt_code = REDIRECT_MAP[target_code]
                data = fetch_json(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{alt_code}.json")
                if data: found_mode = True

            # 2. 広域エリアから探す
            if data is None:
                for code in SEARCH_TARGETS:
                    if code == target_code: continue
                    temp_data = fetch_json(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json")
                    if temp_data:
                        try:
                            if search_key in str(temp_data):
                                data = temp_data
                                found_mode = True
                                break
                        except: pass

        if data is None: return "取得失敗", []

        try:
            report = data[0]
            ts_weather = None
            for ts in report["timeSeries"]:
                if "areas" in ts and ts["areas"] and "weathers" in ts["areas"][0]:
                    ts_weather = ts
                    break
            
            if not ts_weather: return "データなし", []

            dates = ts_weather["timeDefines"]
            weather_areas = ts_weather["areas"]
            display_list = []
            search_key = target_name.replace("地方", "").replace("県", "").replace("府", "").replace("都", "")

            for w_area in weather_areas:
                area_n = w_area["area"]["name"]
                if found_mode:
                    if search_key not in area_n: continue

                weathers = w_area["weathers"]
                for i in range(len(weathers)):
                    if i >= len(dates): break
                    try:
                        dt = datetime.datetime.fromisoformat(dates[i].replace("Z", "+00:00"))
                        date_str = dt.strftime("%m/%d")
                        w_day = ["月","火","水","木","金","土","日"][dt.weekday()]
                        date_disp = f"{date_str} ({w_day})"
                    except: date_disp = "日付不明"

                    display_list.append({
                        "sub_area": area_n,
                        "date": date_disp,
                        "weather": weathers[i].replace("　", " ")
                    })

            if not display_list: return "データなし", []
            return target_name, display_list

        except:
            return "エラー", []

    # ==========================================
    # 2. UI
    # ==========================================
    def create_card(info):
        icon, color = get_weather_icon(info['weather'])
        return ft.Container(
            width=180, height=220, bgcolor="white", border_radius=15, padding=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black26"),
            content=ft.Column(
                controls=[
                    ft.Text(info['sub_area'], size=13, weight="bold", color="blueGrey700"),
                    ft.Text(info['date'], size=12, color="grey"),
                    ft.Divider(height=1, color="grey200"),
                    ft.Container(
                        content=ft.Icon(icon, size=48, color=color),
                        alignment=ft.Alignment(0, 0),
                        padding=10
                    ),
                    ft.Text(info['weather'], size=12, text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    grid_view = ft.Row(wrap=True, spacing=15, run_spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    main_title = ft.Text("地域を選択してください", size=24, weight="bold", color="white")
    
    # 地図設定
    MAP_WIDTH = 300
    MAP_HEIGHT = 380
    map_stack = ft.Stack(width=MAP_WIDTH, height=MAP_HEIGHT)

    def init_map():
        img_filename = "日本地図.jpg"
        if not os.path.exists(img_filename):
            img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Japan_regions_map.svg/462px-Japan_regions_map.svg.png"
        else:
            img_src = img_filename

        map_image = ft.Image(
            src=img_src,
            width=MAP_WIDTH, height=MAP_HEIGHT, 
            fit="contain", opacity=0.9
        )
        
        # クリック機能は削除し、純粋な画像表示のみに
        map_stack.controls.append(map_image)

        for code, pos in MAP_POSITIONS.items():
            dot = ft.Container(
                width=15, height=15, bgcolor="red", border_radius=10,
                left=pos["left"], top=pos["top"],
                visible=False, shadow=ft.BoxShadow(blur_radius=5, color="red"),
                data=code
            )
            map_stack.controls.append(dot)

    def update_map(selected_code):
        target_code = None
        # 1. ピンポイントのデータがあるか？
        if selected_code in MAP_POSITIONS:
            target_code = selected_code
        else:
            # 2. なければ親のデータ（地方）があるか？
            parent_code = office_to_center.get(selected_code)
            if parent_code in MAP_POSITIONS:
                target_code = parent_code

        # マーカー更新
        for control in map_stack.controls[1:]:
            if control.data == target_code:
                control.visible = True
                control.scale = 1.5
            else:
                control.visible = False
                control.scale = 1.0
        map_stack.update()

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
        
        update_map(code) # 地図の赤ポチを更新
        forecasts = get_forecast_data(code, name) # 天気データを取得
        update_view(name, forecasts) # 画面を更新

    # ==========================================
    # 3. 初期化
    # ==========================================
    init_map()
    sidebar_content = ft.Column(scroll=ft.ScrollMode.AUTO)
    sidebar_content.controls.append(ft.Container(padding=20, content=ft.Text("地域リスト", color="white", size=20, weight="bold")))

    try:
        area_url = "https://www.jma.go.jp/bosai/common/const/area.json"
        area_res = requests.get(area_url, timeout=5).json()
        centers = area_res['centers']
        offices = area_res['offices']
        for off_code, off_info in offices.items():
            if "parent" in off_info: office_to_center[off_code] = off_info["parent"]

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
    
    header = ft.Container(
        height=60, bgcolor="#303F9F", 
        padding=ft.Padding(left=20, top=0, right=0, bottom=0),
        content=ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color="white"), ft.Text("日本気象庁 天気予報", color="white", size=20, weight="bold")])
    )
    
    content_area = ft.Row([
        ft.Container(content=ft.Column([main_title, ft.Divider(color="white54"), grid_view], expand=True), expand=True, padding=30),
        
        # 地図エリア
        ft.Container(
            width=340, padding=20, bgcolor="#455A64", 
            border=ft.Border(left=ft.BorderSide(1, "white24")),
            content=ft.Column([
                ft.Text("現在地", color="white", weight="bold"), 
                map_stack
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    ], expand=True, spacing=0)
    
    main_area = ft.Container(expand=True, bgcolor="#546E7A", content=content_area)
    page.add(header, ft.Row([sidebar, main_area], expand=True, spacing=0))

ft.app(target=main, assets_dir=".")