import time
import json
import sys
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding="utf-8")


# ====== SETUP CHROME OPTIONS ======
def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def login_with_cookies(driver, cookie_file):
    print(f"[INFO] Đang đăng nhập với cookie: {cookie_file}")
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        driver.get("https://www.facebook.com")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        for cookie in cookies:
            cookie.pop("storeId", None)
            cookie.pop("id", None)
            if "sameSite" in cookie and cookie["sameSite"].lower() in [
                "no_restriction",
                "unspecified",
            ]:
                cookie["sameSite"] = "None"
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"[WARNING] Cookie lỗi: {cookie.get('name')}, {e}")
        driver.refresh()
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        if "login" in driver.current_url:
            print("[ERROR] Cookie sai hoặc hết hạn!")
            return False
        return driver

    except Exception as e:
        print(f"[ERROR] Đăng nhập thất bại: {e}")
        return False


def runLogin(pathAccCookie):
    print("[INFO] Bắt đầu đăng nhập vào Facebook")
    driver = get_driver()
    driver = login_with_cookies(driver, pathAccCookie)
    time.sleep(3)
    return driver
