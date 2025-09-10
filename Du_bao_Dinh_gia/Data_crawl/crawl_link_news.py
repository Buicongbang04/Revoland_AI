import requests
import pandas as pd
from bs4 import BeautifulSoup
import os 

# quan = ["quan-1", "quan-2", "quan-3", "quan-4", "quan-5", "quan-6", "quan-7", "quan-8", "quan-9", "quan-10", "quan-11", "quan-12", "quan-binh-tan", "quan-binh-thanh", "quan-go-vap", "quan-phu-nhuan","quan-tan-binh", "quan-tan-phu", "quan-thu-duc", "huyen-binh-chanh", "huyen-can-gio", "huyen-cu-chi", "huyen-hoc-mon", "huyen-nha-be"]

quan = ["quan-binh-tan", "quan-binh-thanh", "quan-go-vap", "quan-phu-nhuan","quan-tan-binh", "quan-tan-phu", "quan-thu-duc", "huyen-binh-chanh", "huyen-can-gio", "huyen-cu-chi", "huyen-hoc-mon", "huyen-nha-be"]

loai_bds = {
    "Nhà": {
        "mua-nha-mat-tien-pho": 0, 
        "mua-nha-biet-thu-lien-ke": 0, 
        "mua-duong-noi-bo": 0, 
        "mua-nha-hem-ngo": 0,
    },
}

info_quan = {q: {loai: 0 for loai in loai_bds["Nhà"].keys()} for q in quan}

for q in quan: 
    for loai, _ in loai_bds["Nhà"].items():
        url = f'https://mogi.vn/ho-chi-minh/{q}/{loai}'
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f'Truy cập {loai} tại {q} thành công')
            soup = BeautifulSoup(response.text, 'html.parser')
            total_items = soup.find('div', class_='property-list-result').text.strip()
            info_quan[q][loai] = int(total_items.split()[4].replace('.', '')) if total_items else 0
        else:
            print(f'Không thể truy cập {loai} tại {q}, mã trạng thái: {response.status_code}')

print("="*50)
for q in quan:
    print("="*50)
    print(f"Quận {q}:")
    print("="*50)

    for loai, count in info_quan[q].items():
        print("="*50)
        print(f"{loai}")
        print("="*50)
        data = []
        for page in range(1, count//15+2):
            url = f'https://mogi.vn/ho-chi-minh/{q}/{loai}?cp={page}'
            response = requests.get(url)
            
            if response.status_code == 200:
                print(f'Truy cập trang thứ {page}/{count//15+1} thành công')
                soup = BeautifulSoup(response.text, 'html.parser')
                houses = soup.find_all('div', class_='prop-info')
                dates = soup.find_all('div', class_='prop-extra')

                for house in houses:
                    link = house.find('a', class_="link-overlay")['href'] 
                    data.append(link)

        df = pd.DataFrame(data, columns=['link'])
        os.makedirs(f'data/{q}/link_csv', exist_ok=True)
        df.to_csv(f'data/{q}/link_csv/{loai}.csv', index=False)
