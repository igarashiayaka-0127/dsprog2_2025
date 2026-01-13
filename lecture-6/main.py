import flet as ft
import sqlite3
import datetime
import os

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#E0E5EC"
    page.window_width = 2000 

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "weather.db")

    if not os.path.exists(db_path):
        page.add(ft.Text("⚠️ エラー: weather.db がありません！db_import.pyを実行してください。", color="red", size=30))
        return

    current_selected_code = None 
    current_selected_name = None
    
    MAP_POSITIONS = {}
    SORTED_AREAS = [] 
    AVAILABLE_DATES = []

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT code, name, map_top, map_left FROM areas ORDER BY code")
        rows = cur.fetchall()
        for r in rows:
            code, name, top, left = r
            MAP_POSITIONS[code] = {"name": name, "top": top, "left": left}
            SORTED_AREAS.append({"code": code, "name": name})

        cur.execute("SELECT DISTINCT forecast_date FROM forecasts ORDER BY forecast_date")
        date_rows = cur.fetchall()
        AVAILABLE_DATES = [r[0] for r in date_rows]
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

    def get_forecast_data(target_code, target_name, filter_date):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            if filter_date == "すべて" or filter_date is None:
                sql = "SELECT forecast_date, weather FROM forecasts WHERE area_code = ? ORDER BY forecast_date"
                params = (target_code,)
            else:
                sql = "SELECT forecast_date, weather FROM forecasts WHERE area_code = ? AND forecast_date = ?"
                params = (target_code, filter_date)
            cur.execute(sql, params)
            rows = cur.fetchall()
            conn.close()
            
            if not rows: return "データなし", []
            display_list = []
            for r in rows:
                db_date, weather_text = r
                try:
                    dt = datetime.datetime.strptime(db_date, "%Y-%m-%d")
                    date_disp = f"{dt.strftime('%m/%d')} ({['月','火','水','木','金','土','日'][dt.weekday()]})"
                except: date_disp = db_date
                display_list.append({"sub_area": target_name, "date": date_disp, "weather": weather_text})
            return target_name, display_list
        except: return "エラー", []

    date_options = [ft.dropdown.Option("すべて")] + [ft.dropdown.Option(d) for d in AVAILABLE_DATES]
    date_dropdown = ft.Dropdown(
        width=200, options=date_options, value="すべて", label="日付で絞り込み",
        label_style=ft.TextStyle(color="white"), text_style=ft.TextStyle(color="white"),
        border_color="white", content_padding=10,
    )

    def on_date_change(e):
        selected_date = date_dropdown.value
        if current_selected_code: on_sidebar_click_logic(current_selected_code, current_selected_name)
        else: 
            page.snack_bar = ft.SnackBar(ft.Text(f"日付を「{selected_date}」にしました。"))
            page.snack_bar.open = True
            page.update()
    date_dropdown.on_change = on_date_change

    sidebar_content = ft.Column(scroll=ft.ScrollMode.AUTO)
    sidebar_content.controls.append(ft.Container(padding=20, content=ft.Text("地域リスト", color="white", size=20, weight="bold")))

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

    grouped_areas = {}
    for area in SORTED_AREAS:
        group = get_region_group(area["code"])
        if group not in grouped_areas: grouped_areas[group] = []
        grouped_areas[group].append(area)

    for group_name in ["北海道地方", "東北地方", "関東甲信地方", "北陸・東海地方", "近畿地方", "中国地方", "四国地方", "九州・沖縄地方", "その他"]:
        if group_name in grouped_areas:
            office_buttons = [
                ft.ListTile(title=ft.Text(a["name"], color="white70"), leading=ft.Icon(ft.Icons.LOCATION_ON, color="white70", size=16),
                            data=a, on_click=lambda e: on_sidebar_click_ui(e), hover_color="white10")
                for a in grouped_areas[group_name]
            ]
            sidebar_content.controls.append(ft.ExpansionTile(title=ft.Text(group_name, color="white", weight="bold"), controls=office_buttons, icon_color="white", collapsed_icon_color="white", bgcolor="transparent"))

    def create_card(info):
        icon, color = get_weather_icon(info['weather'])
        return ft.Container(
            width=180, height=220, bgcolor="white", border_radius=15, padding=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black26"),
            content=ft.Column([
                ft.Text(info['sub_area'], size=13, weight="bold", color="blueGrey700"),
                ft.Text(info['date'], size=12, color="grey"),
                ft.Divider(height=1, color="grey200"),
                ft.Container(content=ft.Icon(icon, size=48, color=color), alignment=ft.Alignment(0,0), padding=10),
                ft.Text(info['weather'], size=12, text_align=ft.TextAlign.CENTER, max_lines=2)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    grid_view = ft.Row(wrap=True, spacing=15, run_spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    main_title = ft.Text("地域を選択してください", size=24, weight="bold", color="white")
    
    MAP_WIDTH = 300
    MAP_HEIGHT = 380
    map_stack = ft.Stack(width=MAP_WIDTH, height=MAP_HEIGHT)

    def init_map_ui():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(script_dir, "日本地図.jpg")
        img_src = "日本地図.jpg" if os.path.exists(img_path) else "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Japan_regions_map.svg/462px-Japan_regions_map.svg.png"
        map_stack.controls.append(ft.Image(src=img_src, width=MAP_WIDTH, height=MAP_HEIGHT, fit="contain", opacity=0.9))
        for code, info in MAP_POSITIONS.items():
            map_stack.controls.append(ft.Container(width=8, height=8, bgcolor="red", border_radius=4, left=info["left"], top=info["top"], visible=False, shadow=ft.BoxShadow(blur_radius=3, color="red"), data=code))

    def update_map(target_code):
        for c in map_stack.controls[1:]:
            c.visible = (c.data == target_code)
            c.scale = 1.5 if c.visible else 1.0
        map_stack.update()

    def update_view(area_name, forecasts):
        if isinstance(forecasts, tuple): _, data_list = forecasts
        else: data_list = forecasts
        date_info = f" ({date_dropdown.value})" if date_dropdown.value != "すべて" else ""
        main_title.value = f"{area_name} の天気{date_info}"
        grid_view.controls.clear()
        if not data_list: grid_view.controls.append(ft.Text("データなし", color="white"))
        else: 
            for info in data_list: grid_view.controls.append(create_card(info))
        page.update()

    def on_sidebar_click_logic(code, name):
        nonlocal current_selected_code, current_selected_name
        current_selected_code, current_selected_name = code, name
        main_title.value = f"{name} を読込中..."
        page.update()
        update_map(code)
        update_view(name, get_forecast_data(code, name, date_dropdown.value))

    def on_sidebar_click_ui(e): on_sidebar_click_logic(e.control.data["code"], e.control.data["name"])

    init_map_ui()
    

    content_area = ft.Column([
       
        ft.Container(
            height=250, 
            width=float("inf"),
            bgcolor="#455A64",
            padding=ft.padding.only(top=0, left=20, right=20, bottom=5),
            alignment=ft.Alignment(0, -1.0), 
            border=ft.Border(bottom=ft.BorderSide(1, "white24")),
            
            content=ft.Column([
          
                ft.Container(
                    content=map_stack,
                    margin=ft.margin.only(top=-70)
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START, 
            spacing=0 
            )
        ),
    
        ft.Container(
            expand=True, padding=30,
            content=ft.Column([main_title, ft.Divider(color="white54"), grid_view], expand=True)
        )
    ], spacing=0, expand=True)
    
    page.add(
        ft.Container(height=70, bgcolor="#303F9F", padding=ft.Padding(left=20,right=20), 
                     content=ft.Row([ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color="white"), ft.Text("過去天気アーカイブ", color="white", size=20, weight="bold")]), date_dropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),
        ft.Row([ft.Container(width=210, bgcolor="#263238", content=sidebar_content), ft.Container(expand=True, bgcolor="#546E7A", content=content_area)], expand=True, spacing=0)
    )

script_dir = os.path.dirname(os.path.abspath(__file__))
ft.app(target=main, assets_dir=script_dir)