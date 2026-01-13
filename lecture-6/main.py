import flet as ft
import sqlite3
import datetime
import os

def main(page: ft.Page):
    # --- アプリ設定 ---
    page.title = "天気予報"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#E0E5EC"
    page.window_width = 1200 


    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "weather.db")

    if not os.path.exists(db_path):
        # DBがない場合のエラー表示
        page.add(ft.Text("エラー: weather.db が見つかりません！\n先に db_import.py を実行してデータを作成してください。", color="red", size=30))
        return

    MAP_POSITIONS = {}
    
    # メニューのグループ分け用に、地域コード順で取得します
    SORTED_AREAS = [] 

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 地域コード順(ORDER BY code)で取得
        cur.execute("SELECT code, name, map_top, map_left FROM areas ORDER BY code")
        rows = cur.fetchall()
        
        for r in rows:
            code, name, top, left = r
            # 地図表示用
            MAP_POSITIONS[code] = {
                "name": name,
                "top": top,
                "left": left
            }
            # メニュー表示用リストにも追加
            SORTED_AREAS.append({"code": code, "name": name})
            
        conn.close()

        
    except Exception as e:
        print(f"DB読み込みエラー: {e}")

    
    def get_weather_icon(weather_text):
        text = weather_text.lower()
        if "晴" in text: return ft.Icons.WB_SUNNY, "orange"
        elif "雨" in text: return ft.Icons.UMBRELLA, "blue"
        elif "雪" in text: return ft.Icons.AC_UNIT, "cyan"
        elif "くもり" in text or "曇" in text: return ft.Icons.CLOUD, "grey"
        else: return ft.Icons.WB_CLOUDY_OUTLINED, "blueGrey"

    def get_forecast_data(target_code, target_name):
        
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            # forecastsテーブルから検索
            cur.execute("""
                SELECT forecast_date, weather 
                FROM forecasts 
                WHERE area_code = ?
                ORDER BY forecast_date
            """, (target_code,))
            
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                return "データなし", []

            display_list = []
            
            for r in rows:
                db_date, weather_text = r
                
                # 日付整形
                try:
                    dt = datetime.datetime.strptime(db_date, "%Y-%m-%d")
                    date_str = dt.strftime("%m/%d")
                    w_day = ["月","火","水","木","金","土","日"][dt.weekday()]
                    date_disp = f"{date_str} ({w_day})"
                except:
                    date_disp = db_date

                display_list.append({
                    "sub_area": target_name,
                    "date": date_disp,
                    "weather": weather_text
                })
            
            return target_name, display_list

        except Exception as e:
            print(f"検索エラー: {e}")
            return "エラー", []


    
    sidebar_content = ft.Column(scroll=ft.ScrollMode.AUTO)
    sidebar_content.controls.append(ft.Container(padding=20, content=ft.Text("地域リスト", color="white", size=20, weight="bold")))

    # --- 地域コードの先頭2桁で地方を判定する関数 ---
    def get_region_group(code):
        prefix = int(code[:2])
        if prefix == 1: return "北海道地方"
        if 2 <= prefix <= 7: return "東北地方"
        if 8 <= prefix <= 14 or prefix in [19, 20]: return "関東甲信地方"
        if 15 <= prefix <= 24: return "北陸・東海地方"
        if 25 <= prefix <= 30: return "近畿地方"
        if 31 <= prefix <= 35: return "中国地方"
        if 36 <= prefix <= 39: return "四国地方"
        if 40 <= prefix <= 49: return "九州・沖縄地方"
        return "その他"

    # --- DBのデータを使ってメニューを作成 ---
    # 1. まずグループごとにリストに分ける
    grouped_areas = {}
    # グループの表示順序を定義
    group_order = ["北海道地方", "東北地方", "関東甲信地方", "北陸・東海地方", "近畿地方", "中国地方", "四国地方", "九州・沖縄地方", "その他"]
    
    for area in SORTED_AREAS:
        group = get_region_group(area["code"])
        if group not in grouped_areas:
            grouped_areas[group] = []
        grouped_areas[group].append(area)

    # 2. グループごとにExpansionTileを作って追加
    for group_name in group_order:
        if group_name in grouped_areas:
            office_buttons = []
            for area in grouped_areas[group_name]:
                office_buttons.append(
                    ft.ListTile(
                        title=ft.Text(area["name"], color="white70"),
                        leading=ft.Icon(ft.Icons.LOCATION_ON, color="white70", size=16),
                        data={"code": area["code"], "name": area["name"]},
                        on_click=lambda e: on_sidebar_click(e),
                        hover_color="white10",
                    )
                )
            
            sidebar_content.controls.append(
                ft.ExpansionTile(
                    title=ft.Text(group_name, color="white", weight="bold"),
                    controls=office_buttons,
                    icon_color="white", collapsed_icon_color="white", bgcolor="transparent",
                )
            )

    # --- その他のUIパーツ ---
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
    
    MAP_WIDTH = 300
    MAP_HEIGHT = 380
    map_stack = ft.Stack(width=MAP_WIDTH, height=MAP_HEIGHT)

    def init_map_ui():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_filename = "日本地図.jpg"
        img_full_path = os.path.join(script_dir, img_filename)

        if os.path.exists(img_full_path):
            img_src = img_filename
        else:
            img_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Japan_regions_map.svg/462px-Japan_regions_map.svg.png"

        map_image = ft.Image(src=img_src, width=MAP_WIDTH, height=MAP_HEIGHT, fit="contain", opacity=0.9)
        map_stack.controls.append(map_image)

        for code, info in MAP_POSITIONS.items():
            dot = ft.Container(
                width=8, height=8, bgcolor="red", border_radius=4,
                left=info["left"], top=info["top"],
                visible=False, shadow=ft.BoxShadow(blur_radius=3, color="red"),
                data=code
            )
            map_stack.controls.append(dot)

    def update_map(selected_code):
        target_code = None
        if selected_code in MAP_POSITIONS:
            target_code = selected_code
        
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
            grid_view.controls.append(ft.Text("データなし (DBを確認してください)", color="white"))
        else:
            for info in data_list:
                grid_view.controls.append(create_card(info))
        page.update()

    def on_sidebar_click(e):
        code = e.control.data["code"]
        name = e.control.data["name"]
        main_title.value = f"{name} を読込中..."
        page.update()
        update_map(code)
        forecasts = get_forecast_data(code, name)
        update_view(name, forecasts)

    # --- 画面構成 ---
    init_map_ui()
    
    sidebar = ft.Container(width=260, bgcolor="#263238", content=sidebar_content)
    header = ft.Container(
        height=60, bgcolor="#303F9F", 
        padding=ft.Padding(left=20, top=0, right=0, bottom=0),
        content=ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color="white"), ft.Text("日本気象庁 天気予報", color="white", size=20, weight="bold")])
    )
    content_area = ft.Row([
        ft.Container(content=ft.Column([main_title, ft.Divider(color="white54"), grid_view], expand=True), expand=True, padding=30),
        ft.Container(width=340, padding=20, bgcolor="#455A64", border=ft.Border(left=ft.BorderSide(1, "white24")),
                     content=ft.Column([ft.Text("現在地", color="white", weight="bold"), map_stack], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    ], expand=True, spacing=0)
    
    main_area = ft.Container(expand=True, bgcolor="#546E7A", content=content_area)
    page.add(header, ft.Row([sidebar, main_area], expand=True, spacing=0))

script_dir = os.path.dirname(os.path.abspath(__file__))
ft.app(target=main, assets_dir=script_dir)