from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time
import csv
import re
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pandas as pd

XPATH_RESULTS = "/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div/div[1]/div[1]/div/div/a"

def open_tiktok():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get("https://www.tiktok.com/en/")
    return driver

def findSearch(driver, keyword: str):
    wait = WebDriverWait(driver, 20)

    time.sleep(5)

    actions = ActionChains(driver)

    found = False
    for i in range(200):
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.5)
        try:
            el = driver.switch_to.active_element
            if el and "search" in el.get_attribute("outerHTML").lower():
                print("Đã focus tới ô/nút Search sau", i+1, "lần Tab")
                found = True
                break
        except Exception:
            continue

    if found:
        try:
            actions.send_keys(keyword).perform()
            time.sleep(1)
            actions.send_keys(Keys.ENTER).perform()
            print("Đã nhập từ khóa và nhấn Enter")
            time.sleep(5)
        except Exception as e:
            print("Lỗi khi nhập từ khóa hoặc nhấn Enter:", str(e))

    else:
        print("Không tìm thấy ô/nút Search bằng Tab")

def extract_username_from_href(href: str) -> str:
    try:
        path = urlparse(href).path or ""
    except Exception:
        path = href
    m = re.search(r"/@([A-Za-z0-9._]+)/video/", path)
    if m:
        return m.group(1)
    m = re.search(r"/@([A-Za-z0-9._]+)(?:/|$|\?)", path)
    if m:
        return m.group(1)
    return ""

def canonicalize_link(href: str) -> str:
    try:
        parsed = urlparse(href)
        path = parsed.path or ""
    except Exception:
        return href

    m = re.search(r"^(/@([A-Za-z0-9._]+))(?:/video/.*)?", path)
    if m:
        base_path = m.group(1)
        return f"{parsed.scheme}://{parsed.netloc}{base_path}"

    return href

def crawl(driver, scroll_times: int = 3, pause_seconds: float = 2.0, csv_path: str = "tiktok_links.csv"):
    """
    - Cuộn xuống cuối trang `scroll_times` lần.
    - BeautifulSoup lấy tất cả <a>.
    - Trích username + link chuẩn hóa (trước /video).
    - Ghi CSV: nếu file tồn tại -> append, ngược lại -> tạo mới.
    """
    # 1) Cuộn xuống N lần
    for i in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_seconds)

    # 2) Parse HTML
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    print(f"Tìm thấy {len(anchors)} thẻ <a> (trước khi lọc).")

    base_url = driver.current_url
    seen_links = set()
    new_rows = []

    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        abs_link = urljoin(base_url, href)

        # chỉ giữ domain TikTok
        netloc = urlparse(abs_link).netloc.lower()
        if "tiktok.com" not in netloc:
            continue

        username = extract_username_from_href(abs_link)
        if not username:
            continue

        canon = canonicalize_link(abs_link)
        key = (username, canon)
        if key in seen_links:
            continue
        seen_links.add(key)
        new_rows.append({"username": username, "link": canon})

    if not new_rows:
        print("Không có dữ liệu mới để ghi.")
        return

    # 3) Ghi CSV: append nếu file đã tồn tại, ngược lại tạo mới với header
    file_exists = os.path.isfile(csv_path)
    mode = "a" if file_exists else "w"
    with open(csv_path, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "link"])
        if not file_exists:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)

    print(f"Đã ghi {len(new_rows)} dòng vào: {csv_path} ({'append' if file_exists else 'create'})")

def dedupe_csv(csv_path: str = "tiktok_links.csv"):
    """
    Dùng pandas để xoá trùng theo 'username'.
    - Giữ dòng xuất hiện đầu tiên (first).
    - Ghi đè lại file CSV (UTF-8 BOM).
    """
    if not os.path.isfile(csv_path):
        print(f"Không tìm thấy file: {csv_path}")
        return

    try:
        df = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig")
    except UnicodeError:
        # fallback nếu file không có BOM
        df = pd.read_csv(csv_path, dtype=str, encoding="utf-8")

    if "username" not in df.columns or "link" not in df.columns:
        print("File CSV không đúng định dạng (thiếu cột 'username' hoặc 'link').")
        return

    before = len(df)
    # Chuẩn hóa thêm: đảm bảo link được cắt trước /video nếu còn sót
    df["link"] = df["link"].astype(str).apply(canonicalize_link)

    df = df.drop_duplicates(subset=["username"], keep="first").reset_index(drop=True)
    after = len(df)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Đã xoá {before - after} dòng trùng username. Còn lại {after} dòng trong {csv_path}.")

if __name__ == "__main__":
    # keywords = ["Bất động sản", "nhà trọ hồ chí minh", "nhà trọ rẻ", "cho thuê nhà trọ", "phòng trọ giá rẻ", "phòng trọ sinh viên", "nhà trọ sinh viên"] 
    # keywords = ["căn hộ", "chung cư", "nhà đất", "bất động sản", "mua bán nhà đất", "nhà đất hà nội", "nhà đất hồ chí minh"]
    # keywords = [
    #     # Hashtag tiếng Việt
    #     "#batdongsan", "#nhadat", "#bds", "#muabannhadat",
    #     "#chungcu", "#nhadep", "#sannha", "#MuaNha", "#DauTuBatDongSan",

    #     # Địa phương
    #     "#hochiminh", "#saigon", "#hcmc", "#hanoi",

    #     # Cụm từ tìm kiếm TP.HCM
    #     "nhà đất TP.HCM", "bán căn hộ TP.HCM", "dự án chung cư HCM",
    #     "thị trường bất động sản TP.HCM", "pháp lý nhà đất TP.HCM",

    #     # Cụm từ tìm kiếm Hà Nội
    #     "nhà đất Hà Nội", "bán nhà phố Hà Nội", "chung cư Hà Nội",
    #     "đầu tư bất động sản Hà Nội", "mẹo mua nhà Hà Nội",

    #     # Cụm từ tìm kiếm chung
    #     "đầu tư bất động sản", "pháp lý nhà đất", "mẹo mua bán nhà",
    #     "tư vấn bất động sản", "marketing BĐS", "xu hướng bất động sản 2025"
    # ]
    keywords = ["KOL bất động sản",
    "influencer bất động sản",
    "chuyên gia bất động sản",
    "chuyên gia đầu tư BĐS",
    "cố vấn BĐS nổi tiếng",
    "chuyên gia review dự án bất động sản",
    "KOL thị trường đất nền",
    "KOL review nhà mẫu",
    "KOL bất động sản cao cấp",
    "influencer đầu tư bất động sản",
    "KOL đầu tư nhà đất",
    "KOL bất động sản Hà Nội",
    "KOL bất động sản TP.HCM",
    "KOL bất động sản Đà Nẵng",]
    for keyword in keywords:
        driver = open_tiktok()
        findSearch(driver, keyword)

        SCROLL_TIMES = 5
        SCROLL_PAUSE = 2.0
        CSV_PATH = "tiktok_links.csv"

        crawl(driver, scroll_times=SCROLL_TIMES, pause_seconds=SCROLL_PAUSE, csv_path=CSV_PATH)
        dedupe_csv(CSV_PATH)
        driver.quit()