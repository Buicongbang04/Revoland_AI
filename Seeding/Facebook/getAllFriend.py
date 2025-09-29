import time
import random
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import StaleElementReferenceException 
from typing import List, Dict, Set
from util import loginFacebookWithCookies

def scroll_and_get_link_acc(driver: webdriver.Chrome, max_scroll: int = 50) -> List[Dict[str, str]]:
    """
    Cuộn trang và thu thập các liên kết (link) cùng với tên người dùng (name)
    của các tài khoản Facebook.

    Args:
        driver: Đối tượng WebDriver đã đăng nhập.
        max_scroll: Số lần cuộn tối đa.

    Returns:
        List[Dict[str, str]]: Danh sách các dictionary {'name': 'Tên người dùng', 'link': 'URL profile'}.
    """
    
    # Sử dụng Set để lưu trữ các liên kết DUY NHẤT
    unique_links: Set[str] = set()
    
    # Sử dụng List để lưu trữ kết quả cuối cùng (name và link)
    found_accounts: List[Dict[str, str]] = []
    
    # Theo dõi chiều cao cũ để biết đã cuộn đến cuối trang hay chưa
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(1, max_scroll + 1):
        print(f"[SCROLL] Lần cuộn {i}/{max_scroll}.")

        # Cuộn xuống cuối trang
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(random.uniform(1, 2)) # Tăng thời gian chờ để nội dung tải
        
            # --- Kiểm tra điều kiện thoát ---
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Nếu chiều cao trang không đổi VÀ không tìm thấy bất kỳ link mới nào trong lần cuộn này
        if new_height == last_height:
            print("[INFO] Đã cuộn đến cuối trang hoặc không có thêm tài khoản để tải.")
            break
            
        last_height = new_height

    try:
        # XPath: Chọn tất cả thẻ <a> có role='link' và KHÔNG chứa '/group/' trong href
        a_tags = driver.find_elements(
            By.XPATH, "//a[@role='link' and not(contains(@href, '/groups/')) and not(contains(@href, '/friends_mutual')) and not(contains(@href, '/videos/')) and not(contains(@href, '/pages/'))]"
        )
        
        for a in a_tags:
            try:
                href = a.get_attribute("href")
                name = a.text.strip()
                
                # 1. Loại bỏ tham số tracking của Facebook (eav, ifg, etc.)
                clean_href = href.split('?')[0]
                
                # 2. Đảm bảo tên và link hợp lệ, và link chưa được thêm vào
                # Thẻ <a> trong Facebook đôi khi có text rỗng hoặc link chung chung
                if name and len(name) > 1 and clean_href not in unique_links:
                    # Thêm vào Set để kiểm soát trùng lặp
                    unique_links.add(clean_href)
                    
                    # Thêm vào danh sách kết quả
                    found_accounts.append({
                        'name': name,
                        'link': clean_href
                    })
                    
            except StaleElementReferenceException:
                # Bỏ qua nếu phần tử biến mất trong quá trình cuộn
                continue 
            except Exception as e:
                # Bỏ qua các lỗi khác (ví dụ: thẻ a không có href)
                # print(f"[WARNING] Lỗi xử lý thẻ a: {e}")
                continue

    except Exception as e:
        print(f"[WARNING] Lỗi khi tìm thẻ <a>: {e}")
        
    print(f"[RESULT] Đã thu thập {len(found_accounts) - 3} tài khoản (tên và link).")
    return found_accounts[3:]

def save_friends_to_csv(friends_data, account_id):
    """Lưu danh sách bạn bè vào file CSV."""
    
    if not friends_data:
        print("[WARNING] Không có dữ liệu bạn bè để lưu.")
        return

    # 1. Tạo thư mục lưu trữ nếu chưa có
    save_dir = "data/account/friends"
    os.makedirs(save_dir, exist_ok=True)
    
    # 2. Định nghĩa tên file (sử dụng ID tài khoản để tránh trùng lặp)
    file_path = os.path.join(save_dir, f"friends_{account_id}.csv")
    
    # 3. Chuyển đổi danh sách dictionary sang DataFrame
    df = pd.DataFrame(friends_data)
    
    # 4. Lưu DataFrame vào CSV
    try:
        # index=False để không lưu chỉ mục DataFrame vào file
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"[SUCCESS] Đã lưu {len(friends_data)} người bạn vào: {file_path}")
    except Exception as e:
        print(f"[ERROR] Không thể lưu file CSV: {e}")
        
def getAllFriends(driver, acc_id): 
    print(f"[INFO] Truy cập vào trang danh sách bạn bè...")
    driver.get("https://www.facebook.com/me/friends")      
    time.sleep(3)
    # Nhấn Escapse để tắt popup (nếu có)
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(2)
    friends_links = scroll_and_get_link_acc(driver, max_scroll=1000)
    save_friends_to_csv(friends_links, acc_id)

def main():
    cookies = os.listdir("data/account/cookie")[2:3]
    for cookie in cookies:
        acc_id = cookie.split(".")[0]
        print(f"[INFO] Đang xử lý tài khoản với ID: {acc_id}")
        driver = loginFacebookWithCookies.runLogin(f"data/account/cookie/{cookie}")
        if driver:
            getAllFriends(driver, acc_id)
            driver.quit()
        else:
            print(f"[ERROR] Không thể đăng nhập tài khoản với ID: {acc_id}")

if __name__ == "__main__":
    main()