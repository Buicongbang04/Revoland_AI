import time
import json
import sys
import random
import csv
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')

class FacebookAccountManager:
    def __init__(self, csv_path="data/account/account.csv"):
        self.csv_path = csv_path
        self.accounts = self.load_accounts()
    
    def load_accounts(self):
        """Load accounts from CSV file"""
        try:
            # Check if file exists
            if not os.path.exists(self.csv_path):
                print(f"[ERROR] File CSV không tồn tại: {self.csv_path}")
                return []
            
            # Read CSV with proper handling
            df = pd.read_csv(self.csv_path, header=0)
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            # Check if required columns exist
            required_columns = ['username', 'password', 'name', 'id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"[ERROR] Thiếu các cột bắt buộc: {missing_columns}")
                print(f"[INFO] Các cột có sẵn: {list(df.columns)}")
                return []
            
            accounts = []
            for _, row in df.iterrows():
                account = {
                    'username': str(row['username']).strip(),
                    'password': str(row['password']).strip(),
                    'name': str(row['name']).strip(),
                    'id': str(row['id']).strip()
                }
                accounts.append(account)
            
            print(f"[INFO] Đã tải {len(accounts)} tài khoản từ {self.csv_path}")
            return accounts
        except Exception as e:
            print(f"[ERROR] Không thể tải file CSV: {e}")
            return []
    
    def get_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def close_popup(self, driver):
        """Close Facebook popups"""
        try:
            # Tìm và click nút "Continue" trong màn hình chọn profile
            continue_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//span[text()='Continue' or text()='Tiếp tục']/ancestor::div[@role='button']"
                ))
            )
            continue_btn.click()
            print("[INFO] Đã click Continue trong màn hình chọn profile")
            time.sleep(3)
        except:
            try:
                # Tìm và click nút "Save" trong popup "Save your login info"
                save_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//span[text()='Save' or text()='Lưu']/ancestor::div[@role='button']"
                    ))
                )
                save_btn.click()
                print("[INFO] Đã click Save trong popup lưu thông tin đăng nhập")
                time.sleep(2)
            except:
                try:
                    # Tìm và đóng popup "Lúc khác"
                    later = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            "//span[text()='Lúc khác' or text()='Not now']/ancestor::div[@role='button']"
                        ))
                    )
                    later.click()
                    print("[INFO] Đã tắt popup (Lúc khác)")
                except:
                    try:
                        # Tìm và đóng popup "X"
                        close_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((
                                By.XPATH,
                                "//div[@aria-label='Đóng' or @aria-label='Close']"
                            ))
                        )
                        time.sleep(random.uniform(2, 3))
                        close_btn.click()
                        print("[INFO] Đã tắt popup (X)")
                    except:
                        pass
        
        # Xử lý popup Chrome "Save password?"
        try:
            save_password_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Save') and contains(@class, 'save-password')] | //button[text()='Save']"
                ))
            )
            save_password_btn.click()
            print("[INFO] Đã click Save trong popup Chrome Save password")
            time.sleep(1)
        except:
            pass
        
        # Xử lý popup Facebook "Show notifications" - chọn Block
        try:
            block_notification_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[text()='Block' or text()='Chặn']"
                ))
            )
            block_notification_btn.click()
            print("[INFO] Đã click Block trong popup thông báo Facebook")
            time.sleep(1)
        except:
            pass 
    
    def login_with_credentials(self, driver, username, password):
        """Login with username and password"""
        try:
            print(f"[INFO] Đang đăng nhập với tài khoản: {username}")
            
            # Navigate to Facebook login page
            driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Find and fill username field
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(random.uniform(1, 2))
            
            # Find and fill password field
            password_field = driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(random.uniform(5, 10))
            
            # Click login button
            login_button = driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for page to load
            time.sleep(10)
            
            # Check if login was successful
            if "login" in driver.current_url or "checkpoint" in driver.current_url:
                print(f"[ERROR] Đăng nhập thất bại cho tài khoản: {username}")
                return False
            
            print(f"[INFO] Đăng nhập thành công cho tài khoản: {username}")
            self.close_popup(driver)
            return True
            
        except Exception as e:
            print(f"[ERROR] Lỗi đăng nhập: {e}")
            return False
    
    def save_cookies(self, driver, account_id):
        """Save cookies for future use"""
        try:
            cookies = driver.get_cookies()
            cookie_file = f"data/account/{account_id}.json"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cookie_file), exist_ok=True)
            
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"[INFO] Đã lưu cookies cho tài khoản {account_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Không thể lưu cookies: {e}")
            return False
    
    def login_with_cookies(self, driver, account_id):
        """Login using saved cookies"""
        try:
            cookie_file = f"data/account/{account_id}.json"
            
            if not os.path.exists(cookie_file):
                print(f"[WARNING] Không tìm thấy file cookie: {cookie_file}")
                return False
            
            print(f"[INFO] Đang đăng nhập với cookie: {cookie_file}")
            
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            driver.get("https://www.facebook.com")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            for cookie in cookies:
                cookie.pop("storeId", None)
                cookie.pop("id", None)
                if "sameSite" in cookie and cookie["sameSite"].lower() in ["no_restriction", "unspecified"]:
                    cookie["sameSite"] = "None"
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"[WARNING] Cookie lỗi: {cookie.get('name')}, {e}")

            # Refresh page to apply cookies
            driver.refresh()
            time.sleep(3)

            if "login" in driver.current_url:
                print("[ERROR] Cookie sai hoặc hết hạn!")
                return False

            print("[INFO] Đăng nhập thành công với cookie")
            self.close_popup(driver)
            return True

        except Exception as e:
            print(f"[ERROR] Đăng nhập thất bại: {e}")
            return False
    
    def get_account_by_id(self, account_id):
        """Get account information by ID"""
        for account in self.accounts:
            if str(account['id']) == str(account_id):
                return account
        return None
    
    def get_account_by_username(self, username):
        """Get account information by username"""
        for account in self.accounts:
            if account['username'] == username:
                return account
        return None
    
    def list_accounts(self):
        """List all available accounts"""
        print("\n=== DANH SÁCH TÀI KHOẢN ===")
        for i, account in enumerate(self.accounts, 1):
            print(f"{i}. {account['name']} ({account['username']}) - ID: {account['id']}")
        print("=" * 30)
    
    def run_login(self, account_id=None, username=None, use_cookies=True):
        """Main login function"""
        print("[INFO] Bắt đầu đăng nhập vào Facebook")
        
        # Get account information
        if account_id:
            account = self.get_account_by_id(account_id)
        elif username:
            account = self.get_account_by_username(username)
        else:
            print("[ERROR] Vui lòng cung cấp account_id hoặc username")
            return None
        
        if not account:
            print("[ERROR] Không tìm thấy tài khoản")
            return None
        
        driver = self.get_driver()
        
        # Try cookie login first if enabled
        if use_cookies:
            if self.login_with_cookies(driver, account['id']):
                return driver
            else:
                print("[INFO] Cookie login thất bại, thử đăng nhập bằng username/password")
        
        # Fallback to credential login
        if self.login_with_credentials(driver, account['username'], account['password']):
            # Save cookies for future use
            self.save_cookies(driver, account['id'])
            return driver
        else:
            driver.quit()
            return None

# Convenience functions for backward compatibility
def runLogin(account_id=None, username=None, use_cookies=True):
    """Run login with specified account"""
    manager = FacebookAccountManager()
    return manager.run_login(account_id, username, use_cookies)

def getAccountManager():
    """Get FacebookAccountManager instance"""
    return FacebookAccountManager()

# # Example usage
# if __name__ == "__main__":
#     manager = FacebookAccountManager(csv_path="../data/account/account.csv")
#     manager.list_accounts()
    
#     # Example: Login with first account
#     if manager.accounts:
#         first_account = manager.accounts[0]
#         driver = manager.run_login(account_id=first_account['id'])
        
#         if driver:
#             print("Đăng nhập thành công!")
#             time.sleep(5)
#             driver.quit()
#         else:
#             print("Đăng nhập thất bại!")
