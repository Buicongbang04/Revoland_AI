import time
import json
import sys
import random
import csv
import pandas as pd
import os
from datetime import datetime
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

class FacebookFriendScraper:
    def __init__(self, output_csv_path="data/friends/friends.csv"):
        self.output_csv_path = output_csv_path
        self.friends_data = []
        self.driver = None
        
    def close_popup(self):
        """Đóng các popup Facebook"""
        try:
            # Tìm và click nút "Continue" trong màn hình chọn profile
            continue_btn = WebDriverWait(self.driver, 3).until(
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
                save_btn = WebDriverWait(self.driver, 3).until(
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
                    later = WebDriverWait(self.driver, 3).until(
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
                        close_btn = WebDriverWait(self.driver, 2).until(
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
    
    def navigate_to_friends_page(self):
        """Điều hướng đến trang danh sách bạn bè"""
        try:
            print("[INFO] Đang điều hướng đến trang bạn bè...")
            
            # Truy cập trực tiếp URL danh sách bạn bè
            self.driver.get("https://www.facebook.com/friends/list")
            time.sleep(random.uniform(3, 5))
            
            # Kiểm tra xem đã vào đúng trang chưa
            if "friends/list" in self.driver.current_url or "friends" in self.driver.current_url:
                print("[SUCCESS] Đã truy cập trang danh sách bạn bè")
                return True
            else:
                print("[WARNING] Không thể truy cập trang bạn bè, thử cách khác...")
                
                # Thử truy cập qua profile
                try:
                    self.driver.get("https://www.facebook.com/me")
                    time.sleep(3)
                    
                    # Tìm và click vào tab Friends
                    friends_links = [
                        "//a[contains(@href, '/friends')]",
                        "//span[text()='Friends' or text()='Bạn bè']/ancestor::a",
                        "//div[@aria-label='Friends' or @aria-label='Bạn bè']"
                    ]
                    
                    for link_xpath in friends_links:
                        try:
                            friends_link = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, link_xpath))
                            )
                            friends_link.click()
                            time.sleep(3)
                            print("[SUCCESS] Đã click vào tab Friends")
                            return True
                        except:
                            continue
                    
                    print("[ERROR] Không tìm thấy tab Friends")
                    return False
                    
                except Exception as e:
                    print(f"[ERROR] Lỗi khi truy cập qua profile: {e}")
                    return False
                
        except Exception as e:
            print(f"[ERROR] Lỗi khi điều hướng đến trang bạn bè: {e}")
            return False
    
    def get_total_friends_count(self):
        """Lấy tổng số bạn bè từ trang"""
        try:
            # Tìm text hiển thị số bạn bè (ví dụ: "134 friends")
            count_selectors = [
                "//span[contains(text(), 'friends')]",
                "//div[contains(text(), 'friends')]",
                "//span[contains(text(), 'người bạn')]",
                "//div[contains(text(), 'người bạn')]"
            ]
            
            for selector in count_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        # Tìm số trong text (ví dụ: "134 friends" -> 134)
                        import re
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            count = int(numbers[0])
                            print(f"[INFO] Tìm thấy tổng số bạn bè: {count}")
                            return count
                except:
                    continue
            
            print("[WARNING] Không tìm thấy số bạn bè, sử dụng scroll mặc định")
            return None
            
        except Exception as e:
            print(f"[ERROR] Lỗi khi lấy số bạn bè: {e}")
            return None
    
    def find_friends_container(self):
        """Tìm container chứa danh sách bạn bè"""
        try:
            # Tìm container có scrollbar riêng chứa danh sách bạn bè
            container_selectors = [
                # "//div[contains(@data-visualcompletion, 'ignore-dynamic')",
                # "//div[contains(@aria-label, 'All friends') and contains(@role, 'navigation')]",
                "//div[@aria-label='All friends' or @aria-label='Tất cả bạn bè']//div//div[2]"
            ]
            
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    for container in containers:
                        # Kiểm tra xem container có chứa danh sách bạn bè không
                        if container.find_elements(By.XPATH, ".//a[contains(@href, '/profile.php?id=')]"):
                            print(f"[INFO] Tìm thấy container bạn bè với selector: {selector}")
                            return container
                except:
                    continue
            
            print("[WARNING] Không tìm thấy container bạn bè, sử dụng scroll trang")
            return None
            
        except Exception as e:
            print(f"[ERROR] Lỗi khi tìm container bạn bè: {e}")
            return None
    
    def scroll_and_load_friends(self, max_scrolls=50):
        """Scroll trong container nhỏ để load hết tất cả bạn bè"""
        print("[INFO] Bắt đầu scroll trong container bạn bè...")
        
        # Lấy tổng số bạn bè
        total_friends = self.get_total_friends_count()
        
        # Tìm container chứa danh sách bạn bè
        friends_container = self.find_friends_container()
        
        if friends_container:
            print("[INFO] Scroll trong container bạn bè")
            return self.scroll_container(friends_container, max_scrolls)
        else:
            print("[INFO] Scroll toàn bộ trang")
            return self.scroll_page(max_scrolls)
    
    def scroll_container(self, container, max_scrolls=50):
        """Scroll trong container cụ thể"""
        scroll_count = 0
        no_new_content_count = 0
        last_scroll_top = 0
        
        while scroll_count < max_scrolls:
            try:
                # Scroll xuống trong container
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                time.sleep(random.uniform(2, 4))
                
                # Kiểm tra xem có scroll được không
                current_scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", container)
                
                if current_scroll_top == last_scroll_top:
                    no_new_content_count += 1
                    if no_new_content_count >= 3:
                        print("[INFO] Không còn content mới trong container")
                        break
                else:
                    no_new_content_count = 0
                    last_scroll_top = current_scroll_top
                
                scroll_count += 1
                print(f"[PROGRESS] Đã scroll container {scroll_count}/{max_scrolls} lần")
                
                # Nghỉ ngẫu nhiên
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"[ERROR] Lỗi khi scroll container: {e}")
                break
        
        print(f"[INFO] Hoàn thành scroll container. Đã scroll {scroll_count} lần")
        return scroll_count
    
    def scroll_page(self, max_scrolls=50):
        """Scroll toàn bộ trang (fallback)"""
        print("[INFO] Scroll toàn bộ trang...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        no_new_content_count = 0
        
        while scroll_count < max_scrolls:
            # Scroll xuống cuối trang
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            # Kiểm tra xem có load thêm content không
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                no_new_content_count += 1
                if no_new_content_count >= 3:
                    print("[INFO] Không còn content mới để load")
                    break
            else:
                no_new_content_count = 0
                last_height = new_height
            
            scroll_count += 1
            print(f"[PROGRESS] Đã scroll trang {scroll_count}/{max_scrolls} lần")
            
            # Nghỉ ngẫu nhiên
            time.sleep(random.uniform(1, 3))
        
        print(f"[INFO] Hoàn thành scroll trang. Đã scroll {scroll_count} lần")
        return scroll_count
    
    def extract_friends_data(self):
        """Trích xuất thông tin bạn bè từ trang - chỉ lấy tên và link Facebook"""
        print("[INFO] Bắt đầu trích xuất thông tin bạn bè...")
        
        friends_data = []
        
        try:
            # Tìm tất cả các link profile trong danh sách bạn bè
            profile_links = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@href, 'https://www.facebook.com/') and contains(@role, 'link')]"
            )
            
            print(f"[INFO] Tìm thấy {len(profile_links)} link profile")
            
            processed_urls = set()
            
            for link in profile_links:
                try:
                    profile_url = link.get_attribute('href')
                    if not profile_url or profile_url in processed_urls:
                        continue
                    
                    # Lọc bỏ các URL không phải profile thực sự
                    if not self.is_valid_profile_url(profile_url):
                        continue
                    
                    # Lấy tên bạn bè từ link hoặc container cha
                    friend_name = self.extract_friend_name_from_link(link)
                    if not friend_name:
                        continue
                    
                    friend_data = {
                        'name': friend_name,
                        'profile_url': profile_url
                    }
                    
                    friends_data.append(friend_data)
                    processed_urls.add(profile_url)
                    
                    print(f"[INFO] Đã trích xuất: {friend_name} - {profile_url}")
                    
                except Exception as e:
                    print(f"[DEBUG] Lỗi khi xử lý link: {e}")
                    continue
            
            print(f"[SUCCESS] Đã trích xuất {len(friends_data)} bạn bè")
            return friends_data
            
        except Exception as e:
            print(f"[ERROR] Lỗi khi trích xuất dữ liệu bạn bè: {e}")
            return []
    
    def is_valid_profile_url(self, url):
        """Kiểm tra URL profile có hợp lệ không"""
        if not url:
            return False
        
        # Lọc bỏ các URL không phải profile
        invalid_patterns = [
            'suggestions', 'search', 'friends/requests', 'friends/suggestions', 
            'friends/mutual', 'friends/all', 'friends/collections'
        ]
        
        if any(pattern in url.lower() for pattern in invalid_patterns):
            return False
        
        # Chỉ lấy URL profile thực sự
        return '/profile.php?id=' in url or (url.count('/') >= 3 and 'facebook.com' in url)
    
    def extract_friend_name_from_link(self, link):
        """Trích xuất tên bạn bè từ link"""
        try:
            # Cách 1: Lấy từ text của link
            link_text = link.text.strip()
            if self.is_valid_name(link_text):
                return link_text
            
            # Cách 2: Lấy từ aria-label của link
            aria_label = link.get_attribute('aria-label')
            if aria_label and self.is_valid_name(aria_label):
                return aria_label.strip()
            
            # Cách 3: Lấy từ title của link
            title = link.get_attribute('title')
            if title and self.is_valid_name(title):
                return title.strip()
            
            # Cách 4: Tìm tên trong container cha
            try:
                parent = link.find_element(By.XPATH, "./..")
                name_selectors = [
                    ".//span[not(contains(text(), 'Profile picture')) and not(contains(text(), 'mutual friend')) and not(contains(text(), 'bạn chung'))]",
                    ".//div[not(contains(text(), 'Profile picture')) and not(contains(text(), 'mutual friend')) and not(contains(text(), 'bạn chung'))]",
                    ".//h3//span",
                    ".//h3//div",
                    ".//strong",
                    ".//b"
                ]
                
                for selector in name_selectors:
                    try:
                        name_elements = parent.find_elements(By.XPATH, selector)
                        for name_elem in name_elements:
                            text = name_elem.text.strip()
                            if self.is_valid_name(text):
                                return text
                    except:
                        continue
            except:
                pass
            
            # Cách 5: Xử lý alt text của hình ảnh
            try:
                img_element = link.find_element(By.XPATH, ".//img")
                alt_text = img_element.get_attribute('alt')
                if alt_text and 'Profile picture of' in alt_text:
                    # Trích xuất tên từ "Profile picture of [Tên], who is a mutual friend"
                    if ', who is a mutual friend' in alt_text:
                        name = alt_text.replace('Profile picture of ', '').replace(', who is a mutual friend', '').strip()
                    elif 'Profile picture of' in alt_text:
                        name = alt_text.replace('Profile picture of ', '').strip()
                    else:
                        name = alt_text
                    
                    if self.is_valid_name(name):
                        return name
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] Lỗi khi lấy tên từ link: {e}")
            return None
    
    def is_valid_name(self, name):
        """Kiểm tra tên có hợp lệ không"""
        if not name or len(name) < 2 or len(name) > 50:
            return False
        
        # Lọc bỏ các tên không hợp lệ
        invalid_names = [
            'suggestions', 'suggestion', 'add friend', 'mutual friends', 
            'see all', 'more', '...', 'profile picture', 'bạn chung', 
            'friends', 'tất cả bạn bè', 'who is', 'profile'
        ]
        
        return not any(invalid in name.lower() for invalid in invalid_names)
    
    def save_friends_to_csv(self, friends_data):
        """Lưu danh sách bạn bè vào file CSV - chỉ tên và link"""
        try:
            # Tạo thư mục nếu chưa có
            os.makedirs(os.path.dirname(self.output_csv_path), exist_ok=True)
            
            # Tạo DataFrame và lưu CSV
            df = pd.DataFrame(friends_data)
            df.to_csv(self.output_csv_path, index=False, encoding='utf-8')
            
            print(f"[SUCCESS] Đã lưu {len(friends_data)} bạn bè vào {self.output_csv_path}")
            print(f"[INFO] File CSV chỉ chứa: name, profile_url")
            return True
            
        except Exception as e:
            print(f"[ERROR] Không thể lưu file CSV: {e}")
            return False
    
    def run_scraping(self, max_scrolls=50):
        """Chạy quá trình scrape bạn bè - scroll hết danh sách"""
        try:
            print("[INFO] Bắt đầu scrape danh sách bạn bè...")
            
            # Điều hướng đến trang bạn bè
            if not self.navigate_to_friends_page():
                return False
            
            # Đóng popup nếu có
            self.close_popup()
            time.sleep(2)
            
            # Scroll để load hết tất cả bạn bè
            self.scroll_and_load_friends(max_scrolls)
            
            # Trích xuất dữ liệu bạn bè (chỉ tên và link)
            friends_data = self.extract_friends_data()
            
            if not friends_data:
                print("[WARNING] Không tìm thấy bạn bè nào")
                return False
            
            # Lưu vào CSV
            if self.save_friends_to_csv(friends_data):
                print(f"[COMPLETE] Hoàn thành scrape {len(friends_data)} bạn bè")
                print(f"[INFO] File CSV chỉ chứa tên và link Facebook")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[ERROR] Lỗi trong quá trình scrape: {e}")
            return False
    
    def get_statistics(self):
        """Lấy thống kê bạn bè đã scrape"""
        try:
            if os.path.exists(self.output_csv_path):
                df = pd.read_csv(self.output_csv_path)
                return {
                    'total_friends': len(df),
                    'active_friends': len(df[df['status'] == 'active']),
                    'file_path': self.output_csv_path,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {
                    'total_friends': 0,
                    'active_friends': 0,
                    'file_path': self.output_csv_path,
                    'last_updated': 'Chưa có'
                }
        except Exception as e:
            print(f"[ERROR] Không thể đọc thống kê: {e}")
            return {}
    
    def print_statistics(self):
        """In thống kê bạn bè"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("THỐNG KÊ DANH SÁCH BẠN BÈ")
        print("="*50)
        print(f"Tổng số bạn bè: {stats.get('total_friends', 0)}")
        print(f"Bạn bè hoạt động: {stats.get('active_friends', 0)}")
        print(f"File lưu trữ: {stats.get('file_path', 'N/A')}")
        print(f"Cập nhật lần cuối: {stats.get('last_updated', 'N/A')}")
        print("="*50)

# Convenience functions
def run_get_all_friends(driver, max_scrolls=20, output_path="data/friends/friends.csv"):
    """Chạy scrape danh sách bạn bè với driver đã đăng nhập"""
    scraper = FacebookFriendScraper(output_path)
    scraper.driver = driver
    return scraper.run_scraping(max_scrolls)

def get_friends_statistics(csv_path="data/friends/friends.csv"):
    """Lấy thống kê từ file CSV bạn bè"""
    scraper = FacebookFriendScraper(csv_path)
    scraper.print_statistics()
    return scraper.get_statistics()

# Example usage
if __name__ == "__main__":
    # Khởi tạo scraper
    scraper = FacebookFriendScraper()
    
    # Lưu ý: Driver sẽ được truyền từ main.py
    # scraper.driver = driver  # Được set từ bên ngoài
    
    try:
        # Chạy scraping (cần driver đã được set)
        if scraper.driver:
            success = scraper.run_scraping(max_scrolls=10)
            
            if success:
                # In thống kê
                scraper.print_statistics()
            else:
                print("[ERROR] Scraping thất bại")
        else:
            print("[ERROR] Chưa có driver. Vui lòng set driver trước khi chạy scraping.")
            
    except Exception as e:
        print(f"[ERROR] Lỗi: {e}")