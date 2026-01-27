import requests
from bs4 import BeautifulSoup
import time
import psycopg2

class WikiScraperPostgres:
    def __init__(self):
        self.base_url = "https://ja.wikipedia.org"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.db_params = {
            "host": "localhost",
            "database": "dsprog2db",
            "user": "igarashiayaka",
            "password": ""
        }
        self.processed_urls = set()

    def fetch_all(self):
        # 探索開始カテゴリ
        start_categories = [
            "/wiki/Category:%E6%9D%B1%E4%BA%AC%E9%83%BD%E3%81%AE%E9%89%84%E9%81%93%E9%A7%85",
            "/wiki/Category:%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8C%BA%E9%83%A8%E3%81%AE%E9%89%84%E9%81%93%E9%A7%85"
        ]
        for cat in start_categories:
            self.crawl_category(self.base_url + cat)

    def crawl_category(self, url):
        # 重複・空URLチェック（ここでエラーを回避）
        if not url or url in self.processed_urls: return
        self.processed_urls.add(url)
        
        
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            # 1. 駅ページを解析
            links = soup.select("#mw-pages .mw-category-group a")
            for link in links:
                href = link.get('href')
                if href and "駅" in link.text and "Category" not in href:
                    self.scrape_detail(self.base_url + href)
                    time.sleep(0.2)

            # 2. サブカテゴリ（足立区の鉄道など）を探索
            sub_cats = soup.select("#mw-subcategories .mw-category-group a")
            for sub_cat in sub_cats:
                sub_href = sub_cat.get('href')
                if sub_href: # ここで None をチェック！
                    self.crawl_category(self.base_url + sub_href)

            # 3. 「次の200件」を追跡
            next_link = soup.find("a", string="次の200件")
            if next_link and next_link.get('href'):
                self.crawl_category(self.base_url + next_link.get('href'))
        except Exception as e:
            print(f"      [!] カテゴリ取得失敗: {e}")

    def scrape_detail(self, url):
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            st_name = soup.find("h1", id="firstHeading").text.replace("駅", "")
            
            content = soup.find("div", class_="mw-parser-output")
            paragraphs = content.find_all("p")
            
            lines, comp, loc = [], "不明", "不明"
            for p in paragraphs:
                text = p.get_text()
                if "駅" in text and ("は" in text or "にある" in text):
                    lines = [l.text for l in p.find_all("a", title=lambda x: x and "線" in x)]
                    c_link = p.find("a", title=lambda x: x and ("鉄道" in x or "交通局" in x))
                    if c_link: comp = c_link.text
                    t_link = p.find("a", title="東京都")
                    if t_link:
                        loc_link = t_link.find_next_sibling("a")
                        if loc_link: loc = loc_link.text
                    break

            for ln in (lines if lines else ["不明"]):
                self.save_db(st_name, ln, comp, loc)
        except: pass

    def save_db(self, st, ln, cp, lc):
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    # 重複防止
                    cur.execute("""
                        INSERT INTO stations (station_name, line_name, company_name, location)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (station_name, line_name) DO NOTHING;
                    """, (st, ln, cp, lc))
                conn.commit()
            print(f"      [SUCCESS] {st} ({ln})")
        except: pass

if __name__ == "__main__":
    scraper = WikiScraperPostgres()
    scraper.fetch_all()