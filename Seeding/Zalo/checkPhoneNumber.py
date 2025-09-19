"""
zalo_login_selenium.py
Sử dụng Selenium để tự login vào https://id.zalo.me/account?... và lưu cookies.
Chú ý: nếu có 2FA/captcha, script sẽ tạm dừng để bạn nhập thủ công.
"""

import os
import json
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

ZALO_USER = os.getenv("ZALO_USER")
ZALO_PASS = os.getenv("ZALO_PASS")

LOGIN_URL = "https://id.zalo.me/account?continue=https%3A%2F%2Fchat.zalo.me%2F"
COOKIES_FILE = "zalo_cookies.json"

# Thử nhiều selector phổ biến; nếu site thay đổi, chỉnh ở đây
USERNAME_SELECTORS = [
    (By.NAME, "phone"),         # ví dụ
    (By.NAME, "username"),
    (By.NAME, "email"),
    (By.ID, "phone"),
    (By.ID, "username"),
    (By.CSS_SELECTOR, "input[type='text']"),
]
PASSWORD_SELECTORS = [
    (By.NAME, "password"),
    (By.ID, "password"),
    (By.CSS_SELECTOR, "input[type='password']"),
]
SUBMIT_SELECTORS = [
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.XPATH, "//button[contains(., 'Đăng nhập')]"),
    (By.XPATH, "//button[contains(., 'Đăng nhập bằng')]"),
]

def try_find(driver, selectors, timeout=8):
    """Try multiple selectors; return first found element or None."""
    wait = WebDriverWait(driver, timeout)
    for by, sel in selectors:
        try:
            el = wait.until(EC.presence_of_element_located((by, sel)))
            return el
        except Exception:
            continue
    return None

def save_cookies(driver, path=COOKIES_FILE):
    cookies = driver.get_cookies()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"[+] Cookies saved to {path}")

def load_cookies(driver, url, path=COOKIES_FILE):
    if not os.path.exists(path):
        print("[!] Cookies file not found.")
        return False
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    driver.get(url)  # phải vào domain trước khi add cookie
    for c in cookies:
        # Selenium expects expiry as int in some versions; handle None
        try:
            driver.add_cookie(c)
        except Exception:
            # sanitize cookie
            c.pop("sameSite", None)
            try:
                driver.add_cookie(c)
            except Exception as e:
                print("Warning add_cookie failed for", c.get("name"), "->", e)
    print("[+] Cookies loaded into browser")
    return True

def main():
    chrome_options = Options()
    # Không để headless mặc định — nhiều site detect headless và block.
    # Nếu bạn hiểu rủi ro có thể bật headless bằng: chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                              options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        # Nếu đã có cookie, thử load cookie trước để skip login
        if os.path.exists(COOKIES_FILE):
            print("[*] Cookies file found, attempting to reuse session...")
            load_cookies(driver, "https://id.zalo.me")
            # Sau khi load cookie, vào trang chat để kiểm tra login
            driver.get("https://chat.zalo.me/")
            time.sleep(3)
            if "id.zalo.me" not in driver.current_url and "login" not in driver.current_url:
                print("[+] Có vẻ đã đăng nhập bằng cookie. URL:", driver.current_url)
                return
            else:
                print("[*] Cookie không hợp lệ hoặc đã hết hạn. Tiếp tục flow đăng nhập.")

        # Bắt đầu flow đăng nhập
        driver.get(LOGIN_URL)

        # Tìm ô nhập user và pass
        user_el = try_find(driver, USERNAME_SELECTORS)
        pass_el = try_find(driver, PASSWORD_SELECTORS)

        if user_el is None or pass_el is None:
            print("[!] Không tìm thấy input username/password tự động. Vui lòng mở developer tools kiểm tra selector.")
            # Mở trang để user tự thao tác (không headless), chờ họ hoàn tất login thủ công:
            input("Nhấn Enter sau khi bạn đăng nhập thủ công trong cửa sổ trình duyệt...")
            # Sau user đăng nhập thủ công, lưu cookie nếu thành công
            save_cookies(driver)
            return

        # Gõ username/password
        user_el.clear()
        user_el.send_keys(ZALO_USER)
        pass_el.clear()
        pass_el.send_keys(ZALO_PASS)

        # Tìm nút submit
        submit_btn = try_find(driver, SUBMIT_SELECTORS)
        if submit_btn:
            submit_btn.click()
        else:
            # fallback: gửi Enter từ ô password
            pass_el.send_keys("\n")

        # Sau submit, có thể có nhiều bước: captcha, xác thực, redirect. Chờ redirect đến chat hoặc trang profile
        # Thử đợi URL chứa chat.zalo.me hoặc presence of element indicative of logged-in
        try:
            wait.until(EC.url_contains("chat.zalo.me"), timeout=10)
            print("[+] Đã redirect tới chat.zalo.me => login có vẻ thành công.")
            save_cookies(driver)
            return
        except Exception:
            print("[*] Không detect redirect tới chat.zalo.me trong 10s. Có thể cần 2FA/captcha hoặc trang load chậm.")
            # Kiểm tra presence of known element or ask user to complete manual step
            print("Mở cửa sổ trình duyệt để bạn hoàn tất 2FA/captcha nếu cần.")
            # Tạm dừng cho user hoàn tất (manual)
            input("Sau khi hoàn tất, nhấn Enter để tiếp tục và lưu cookie...")
            # Sau user hoàn tất, lưu cookie
            save_cookies(driver)
            return

    finally:
        driver.quit()

if __name__ == "__main__":
    if not ZALO_USER or not ZALO_PASS:
        print("[!] Hãy thiết lập ZALO_USER và ZALO_PASS trong .env trước khi chạy.")
    else:
        main()
