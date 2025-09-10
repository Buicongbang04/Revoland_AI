import pandas as pd 
import numpy as np 
import os 
import requests
from bs4 import BeautifulSoup

# quan = ["quan-2", "quan-3", "quan-4", "quan-5", "quan-6", "quan-7", "quan-8", "quan-9", "quan-10", "quan-11", "quan-12", "quan-binh-tan", "quan-binh-thanh", "quan-go-vap", "quan-phu-nhuan","quan-tan-binh", "quan-tan-phu", "quan-thu-duc", "huyen-binh-chanh", "huyen-can-gio", "huyen-cu-chi", "huyen-hoc-mon", "huyen-nha-be"]
quan = input("Enter the list of districts (comma-separated): ").split(' ')

for q in quan:
    print(f"Processing data for {q}...")
    print("="*50)
    for loai in ["mua-nha-mat-tien-pho", "mua-nha-biet-thu-lien-ke", "mua-duong-noi-bo", "mua-nha-hem-ngo"]:
        df = pd.read_csv(f'data/{q}/link_csv/{loai}.csv')
        # TRUY CẬP TẤT CẢ CÁC LINK
        n = len(df) 
        data_list = []
        for i in range(n):
            url = df['link'][i] 
            response = requests.get(url) 
            if response.status_code == 200:
                print(f"Processing {i+1}/{n}: {url}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                title = soup.find('div', class_='title').text.strip()
                price = soup.find('div', class_="price").text.strip()
                address = soup.find('div', class_="address").text.strip()
                atrributes = soup.find('div', class_='info-attrs clearfix').find_all('div')
                data = {atrr.find_all('span')[0].text.strip(): atrr.find_all('span')[1].text.strip() for atrr in atrributes}
                decription = soup.find('div', class_='info-content-body').text.strip()
                
                data_list.append({
                    'Ma_BDS': data.get('Mã BĐS', None),
                    'Ngay_dang': data.get('Ngày đăng', None),
                    'Dia_chi': address,
                    'Dien_tich_su_dung': data.get('Diện tích sử dụng', None),
                    'Dien_tich_dat': data.get('Diện tích đất', None),
                    'So_phong_ngu': data.get('Phòng ngủ', None),
                    'So_nha_tam': data.get('Nhà tắm', None),
                    'Phap_ly': data.get('Pháp lý', None),
                    'Gioi_thieu': decription,
                    'Gia_dat': price,
                })
                
        df_data = pd.DataFrame(data_list)
        os.makedirs(f'data/{q}/data_info', exist_ok=True)
        df_data.to_csv(f'data/{q}/data_info/{loai}.csv', index=False)
        print(f"Done for {q}/{loai}.csv")
        print("="*50)

