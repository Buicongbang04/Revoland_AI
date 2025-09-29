import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def runAcceptFriend(driver, max_accept=5):
    print(f"[INFO] Truy cập vào trang chấp nhận kết bạn...")
    driver.get("https://m.facebook.com/friends/requests")

    try:
        # đợi các nút xuất hiện (nếu không có thì thoát luôn)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//span[contains(text(),'Chấp nhận') or contains(text(),'Confirm') or contains(text(),'Xác nhận') or contains(text(),'Accept')]")
            )
        )
    except:
        print("✅ Hết lời mời kết bạn")
        return {
            "successful_accepts": 0,
            "total_found": 0
        }

    buttons = driver.find_elements(
        By.XPATH, "//span[contains(text(),'Chấp nhận') or contains(text(),'Confirm') or contains(text(),'Xác nhận') or contains(text(),'Accept')]"
    )
    total_found = len(buttons)
    print(f"[INFO] Tìm thấy {total_found} nút chấp nhận")

    accepted = 0
    for btn in buttons:
        if accepted >= max_accept:
            break
        try:
            driver.execute_script("arguments[0].click();", btn)
            accepted += 1
            print(f"[SUCCESS] Đã chấp nhận {accepted}/{max_accept}")
            time.sleep(random.uniform(3, 6))  # nghỉ tránh bị block
        except Exception as e:
            print(f"[ERROR] Không click được nút: {e}")

    print(f"[DONE] Tổng cộng đã chấp nhận {accepted} lời mời.")

    return {
        "successful_accepts": accepted,
        "total_found": total_found
    }
