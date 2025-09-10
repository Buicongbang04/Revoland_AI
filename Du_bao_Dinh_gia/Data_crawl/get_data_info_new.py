import pandas as pd
import numpy as np
import os
import requests
import time
import random
from bs4 import BeautifulSoup

# --- INPUT: DANH SÁCH QUẬN ---
quan_input = input("Enter the list of districts (space-separated): ")
quan = quan_input.strip().split()

# --- SET HEADER GIẢ LẬP TRÌNH DUYỆT ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# --- BẮT ĐẦU SCRAPING ---
for q in quan:
    print(f"🟢 Processing district: {q}")
    print("=" * 60)
    for loai in [
        "mua-nha-mat-tien-pho",
        "mua-nha-biet-thu-lien-ke",
        "mua-duong-noi-bo",
        "mua-nha-hem-ngo",
    ]:
        csv_path = f"data/{q}/link_csv/{loai}.csv"
        if not os.path.exists(csv_path):
            print(f"⚠️  File {csv_path} not found. Skipping...")
            continue

        df = pd.read_csv(csv_path)
        n = len(df)
        data_list = []

        for i in range(n):
            url = df.loc[i, "link"]
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code != 200:
                    print(f"❌ Failed ({response.status_code}): {url}")
                    continue

                soup = BeautifulSoup(response.content, "html.parser")

                title = soup.find("div", class_="title")
                price = soup.find("div", class_="price")
                address = soup.find("div", class_="address")
                attrs = soup.find("div", class_="info-attrs clearfix")
                description = soup.find("div", class_="info-content-body")

                if not (title and price and address and attrs and description):
                    print(f"⚠️  Missing fields: {url}")
                    continue

                attributes = attrs.find_all("div")
                data = {
                    attr.find_all("span")[0]
                    .text.strip(): attr.find_all("span")[1]
                    .text.strip()
                    for attr in attributes
                    if len(attr.find_all("span")) >= 2
                }

                data_list.append(
                    {
                        "Ma_BDS": data.get("Mã BĐS"),
                        "Ngay_dang": data.get("Ngày đăng"),
                        "Dia_chi": address.text.strip(),
                        "Dien_tich_su_dung": data.get("Diện tích sử dụng"),
                        "Dien_tich_dat": data.get("Diện tích đất"),
                        "So_phong_ngu": data.get("Phòng ngủ"),
                        "So_nha_tam": data.get("Nhà tắm"),
                        "Phap_ly": data.get("Pháp lý"),
                        "Gioi_thieu": description.text.strip(),
                        "Gia_dat": price.text.strip(),
                    }
                )

                print(f"✅ [{i+1}/{n}] {url}")

                # Tránh bị limit request
                time.sleep(random.uniform(2, 5))

            except Exception as e:
                print(f"❗ Error on {url}: {e}")
                continue

        # Lưu kết quả
        out_dir = f"data/{q}/data_info"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{loai}.csv")
        pd.DataFrame(data_list).to_csv(out_path, index=False)

        print(f"✅ Done: {out_path}")
        print("=" * 60)
