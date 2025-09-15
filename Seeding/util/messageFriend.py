import time
import json
import sys
import random
import csv
import pandas as pd
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

sys.stdout.reconfigure(encoding='utf-8')

class MessageFriendManager:
    def __init__(self, friends_csv_path="data/friends/friends.csv", 
                 messages_csv_path="data/content/messages.csv",
                 progress_file="data/progress/message_progress.json"):
        self.friends_csv_path = friends_csv_path
        self.messages_csv_path = messages_csv_path
        self.progress_file = progress_file
        self.friends_data = self.load_friends()
        self.messages_data = self.load_messages()
        self.progress_data = self.load_progress()
        
        # Cấu hình mặc định
        self.default_team_size = 30  # Số bạn bè mỗi đội
        self.min_daily_messages = 150  # Tối thiểu tin nhắn/ngày
        self.max_daily_messages = 300  # Tối đa tin nhắn/ngày
        
    def load_friends(self):
        """Load danh sách bạn bè từ CSV"""
        try:
            if not os.path.exists(self.friends_csv_path):
                print(f"[WARNING] File bạn bè không tồn tại: {self.friends_csv_path}")
                return []
            
            df = pd.read_csv(self.friends_csv_path)
            friends = []
            for _, row in df.iterrows():
                friend = {
                    'name': str(row.get('name', '')).strip(),
                    'profile_url': str(row.get('profile_url', '')).strip(),
                }
                if friend['name'] and friend['profile_url']:
                    friends.append(friend)
            
            print(f"[INFO] Đã tải {len(friends)} bạn bè từ {self.friends_csv_path}")
            return friends
        except Exception as e:
            print(f"[ERROR] Không thể tải danh sách bạn bè: {e}")
            return []
    
    def load_messages(self):
        """Load danh sách tin nhắn từ CSV"""
        try:
            if not os.path.exists(self.messages_csv_path):
                print(f"[WARNING] File tin nhắn không tồn tại: {self.messages_csv_path}")
                return []
            
            df = pd.read_csv(self.messages_csv_path)
            messages = []
            for _, row in df.iterrows():
                message = {
                    'content': str(row.get('content', '')).strip(),
                    'type': str(row.get('type', 'text')).strip(),  # text, image, link
                    'priority': int(row.get('priority', 1))  # 1-5, 5 là cao nhất
                }
                if message['content']:
                    messages.append(message)
            
            # Sắp xếp theo độ ưu tiên
            messages.sort(key=lambda x: x['priority'], reverse=True)
            print(f"[INFO] Đã tải {len(messages)} tin nhắn từ {self.messages_csv_path}")
            return messages
        except Exception as e:
            print(f"[ERROR] Không thể tải danh sách tin nhắn: {e}")
            return []
    
    def load_progress(self):
        """Load tiến độ nhắn tin"""
        try:
            if not os.path.exists(self.progress_file):
                return {
                    'teams': {},
                    'current_team': 0,
                    'last_message_date': None,
                    'daily_count': 0,
                    'total_sent': 0,
                    'failed_messages': []
                }
            
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Không thể tải tiến độ: {e}")
            return {
                'teams': {},
                'current_team': 0,
                'last_message_date': None,
                'daily_count': 0,
                'total_sent': 0,
                'failed_messages': []
            }
    
    def save_progress(self):
        """Lưu tiến độ nhắn tin"""
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Đã lưu tiến độ vào {self.progress_file}")
        except Exception as e:
            print(f"[ERROR] Không thể lưu tiến độ: {e}")
    
    def validate_friends_data(self):
        """Validate và làm sạch dữ liệu bạn bè"""
        print("[INFO] Đang validate dữ liệu bạn bè...")
        
        valid_friends = []
        invalid_count = 0
        
        for friend in self.friends_data:
            # Kiểm tra các trường bắt buộc
            if not friend.get('name') or not friend.get('profile_url'):
                invalid_count += 1
                continue
            
            # Kiểm tra tên hợp lệ
            if len(friend['name'].strip()) < 2:
                invalid_count += 1
                continue
            
            # Kiểm tra URL hợp lệ
            if not ('https://www.facebook.com/' in friend['profile_url']):
                invalid_count += 1
                continue
            
            # Lọc bỏ các tên không hợp lệ
            invalid_names = ['suggestions', 'suggestion', 'add friend', 'mutual friends', 'see all', 'more', '...', 'friends']
            if friend['name'].lower().strip() in invalid_names:
                invalid_count += 1
                continue
            
            valid_friends.append(friend)
        
        self.friends_data = valid_friends
        print(f"[INFO] Đã validate: {len(valid_friends)} bạn bè hợp lệ, {invalid_count} bạn bè không hợp lệ")
        return len(valid_friends)
    
    def create_teams(self, team_size=None):
        """Chia danh sách bạn bè thành các đội"""
        if team_size is None:
            team_size = self.default_team_size
        
        # Validate dữ liệu trước khi chia đội
        valid_count = self.validate_friends_data()
       
        total_friends = len(self.friends_data)
        
        if total_friends == 0:
            print("[WARNING] Không có bạn bè nào để chia đội")
            return {}
        
        teams = {}
        num_teams = (total_friends + team_size - 1) // team_size  # Làm tròn lên
        
        for i in range(num_teams):
            start_idx = i * team_size
            end_idx = min((i + 1) * team_size, total_friends)
            team_friends = self.friends_data[start_idx:end_idx]
            
            teams[f'team_{i+1}'] = {
                'friends': team_friends,
                'size': len(team_friends),
                'current_index': 0,
                'messages_sent': 0,
                'last_activity': None
            }
        
        self.progress_data['teams'] = teams
        self.save_progress()
        
        print(f"[INFO] Đã chia {total_friends} bạn bè thành {num_teams} đội")
        for team_name, team_data in teams.items():
            print(f"  - {team_name}: {team_data['size']} bạn bè")
        
        return teams
    
    def get_current_team(self):
        """Lấy đội hiện tại cần nhắn tin"""
        if not self.progress_data['teams']:
            print("[INFO] Chưa có đội nào, tạo đội mới...")
            self.create_teams()
        
        teams = self.progress_data['teams']
        current_team_name = f"team_{self.progress_data['current_team'] + 1}"
        
        if current_team_name not in teams:
            # Quay về đội đầu tiên
            self.progress_data['current_team'] = 0
            current_team_name = "team_1"
        
        return current_team_name, teams[current_team_name]
    
    def get_next_friend(self, team_name, team_data):
        """Lấy bạn bè tiếp theo trong đội"""
        current_index = team_data['current_index']
        friends = team_data['friends']
        
        if current_index >= len(friends):
            # Đã nhắn hết đội này, chuyển sang đội tiếp theo
            self.progress_data['current_team'] = (self.progress_data['current_team'] + 1) % len(self.progress_data['teams'])
            return None
        
        friend = friends[current_index]
        team_data['current_index'] += 1
        return friend
    
    def get_random_message(self):
        """Lấy tin nhắn ngẫu nhiên từ danh sách"""
        if not self.messages_data:
            return "Xin chào! Tôi muốn kết nối với bạn."
        
        # Ưu tiên tin nhắn có priority cao
        high_priority_messages = [m for m in self.messages_data if m['priority'] >= 4]
        if high_priority_messages:
            return random.choice(high_priority_messages)['content']
        
        return random.choice(self.messages_data)['content']
    
    def send_message_to_friend(self, driver, friend, message):
        """Gửi tin nhắn cho một bạn bè"""
        try:
            print(f"[INFO] Đang nhắn tin cho: {friend['name']}")
            
            # Kiểm tra URL hợp lệ
            if not friend['profile_url'] or 'https://www.facebook.com/' not in friend['profile_url']:
                print(f"[WARNING] URL không hợp lệ cho {friend['name']}: {friend['profile_url']}")
                return False
            
            # Điều hướng đến trang cá nhân
            driver.get(friend['profile_url'])
            time.sleep(random.uniform(3, 5))
            
            # Tìm và click nút "Message" với nhiều selector khác nhau
            message_button = None
            selectors = [
                "//span[text()='Message' or text()='Nhắn tin']/ancestor::div[@role='button']",
            ]
            
            for selector in selectors:
                try:
                    message_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not message_button:
                print(f"[WARNING] Không tìm thấy nút Message cho {friend['name']} - có thể đã bị chặn hoặc không phải bạn bè")
                return False
            
            message_button.click()
            time.sleep(random.uniform(2, 4))
            
            # Tìm ô nhập tin nhắn
            try:
                message_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[@aria-label='Message' and @role='textbox' and @aria-placeholder='Aa']"
                    ))
                )
                
                # Xóa nội dung cũ và nhập tin nhắn mới
                message_input.clear()
                time.sleep(random.uniform(1, 2))
                
                # Nhập tin nhắn từng ký tự để giống người thật
                for char in message:
                    message_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                time.sleep(random.uniform(1, 3))
                
                # Gửi tin nhắn
                message_input.send_keys(Keys.ENTER)
                
                print(f"[SUCCESS] Đã gửi tin nhắn cho {friend['name']}")
                time.sleep(random.uniform(2, 4))
                message_input.send_keys(Keys.ESCAPE)  # Đóng hộp thoại tin nhắn
                return True
                
            except TimeoutException:
                print(f"[ERROR] Không tìm thấy ô nhập tin nhắn cho {friend['name']}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Lỗi khi nhắn tin cho {friend['name']}: {e}")
            return False
    
    def should_send_messages_today(self):
        """Kiểm tra xem có nên gửi tin nhắn hôm nay không"""
        today = datetime.now().strftime('%Y-%m-%d')
        last_date = self.progress_data.get('last_message_date')
        
        if last_date != today:
            # Ngày mới, reset counter
            self.progress_data['daily_count'] = 0
            self.progress_data['last_message_date'] = today
            return True
        
        # Kiểm tra xem đã gửi đủ tin nhắn hôm nay chưa
        daily_count = self.progress_data.get('daily_count', 0)
        return daily_count < self.max_daily_messages
    
    def run_daily_messaging(self, driver, target_count=None):
        """Chạy nhắn tin hàng ngày"""
        if not self.should_send_messages_today():
            print("[INFO] Đã gửi đủ tin nhắn hôm nay")
            return
        
        if target_count is None:
            target_count = random.randint(self.min_daily_messages, self.max_daily_messages)
        
        daily_count = self.progress_data.get('daily_count', 0)
        remaining_count = target_count - daily_count
        
        if remaining_count <= 0:
            print(f"[INFO] Đã đạt mục tiêu {target_count} tin nhắn hôm nay")
            return
        
        print(f"[INFO] Bắt đầu nhắn tin. Mục tiêu: {remaining_count} tin nhắn")
        
        sent_count = 0
        failed_count = 0
        
        while sent_count < remaining_count:
            # Lấy đội hiện tại
            team_name, team_data = self.get_current_team()
            
            # Lấy bạn bè tiếp theo
            friend = self.get_next_friend(team_name, team_data)
            
            if friend is None:
                print("[WARNING] Đã nhắn hết tất cả bạn bè trong các đội")
                break
            
            # Lấy tin nhắn ngẫu nhiên
            message = self.get_random_message()
            
            # Gửi tin nhắn
            if self.send_message_to_friend(driver, friend, message):
                sent_count += 1
                team_data['messages_sent'] += 1
                team_data['last_activity'] = datetime.now().isoformat()
                self.progress_data['total_sent'] += 1
                self.progress_data['daily_count'] += 1
                
                print(f"[PROGRESS] Đã gửi {sent_count}/{remaining_count} tin nhắn")
            else:
                failed_count += 1
                self.progress_data['failed_messages'].append({
                    'friend_name': friend['name'],
                    'friend_url': friend['profile_url'],
                    'timestamp': datetime.now().isoformat(),
                    'message': message
                })
            
            # Nghỉ ngẫu nhiên giữa các tin nhắn
            sleep_time = random.uniform(10, 30)  
            print(f"[INFO] Nghỉ {sleep_time:.1f}s trước khi gửi tin nhắn tiếp theo...")
            time.sleep(sleep_time)
            
            # Lưu tiến độ định kỳ
            if sent_count % 10 == 0:
                self.save_progress()
        
        # Lưu tiến độ cuối cùng
        self.save_progress()
        
        print(f"[COMPLETE] Hoàn thành nhắn tin hôm nay:")
        print(f"  - Đã gửi: {sent_count} tin nhắn")
        print(f"  - Thất bại: {failed_count} tin nhắn")
        print(f"  - Tổng cộng hôm nay: {self.progress_data['daily_count']} tin nhắn")
        print(f"  - Tổng cộng tất cả: {self.progress_data['total_sent']} tin nhắn")
    
    def get_statistics(self):
        """Lấy thống kê nhắn tin"""
        stats = {
            'total_friends': len(self.friends_data),
            'total_teams': len(self.progress_data.get('teams', {})),
            'current_team': self.progress_data.get('current_team', 0) + 1,
            'total_messages_sent': self.progress_data.get('total_sent', 0),
            'daily_messages_sent': self.progress_data.get('daily_count', 0),
            'failed_messages': len(self.progress_data.get('failed_messages', [])),
            'last_message_date': self.progress_data.get('last_message_date', 'Chưa có')
        }
        
        # Thống kê theo đội
        team_stats = {}
        for team_name, team_data in self.progress_data.get('teams', {}).items():
            team_stats[team_name] = {
                'size': team_data['size'],
                'messages_sent': team_data['messages_sent'],
                'current_index': team_data['current_index'],
                'completion_rate': (team_data['current_index'] / team_data['size'] * 100) if team_data['size'] > 0 else 0
            }
        
        stats['team_details'] = team_stats
        return stats
    
    def print_statistics(self):
        """In thống kê nhắn tin"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("THỐNG KÊ NHẮN TIN BẠN BÈ")
        print("="*50)
        print(f"Tổng số bạn bè: {stats['total_friends']}")
        print(f"Số đội: {stats['total_teams']}")
        print(f"Đội hiện tại: {stats['current_team']}")
        print(f"Tổng tin nhắn đã gửi: {stats['total_messages_sent']}")
        print(f"Tin nhắn hôm nay: {stats['daily_messages_sent']}")
        print(f"Tin nhắn thất bại: {stats['failed_messages']}")
        print(f"Ngày nhắn tin cuối: {stats['last_message_date']}")
        
        print("\nCHI TIẾT THEO ĐỘI:")
        for team_name, team_stats in stats['team_details'].items():
            print(f"  {team_name}:")
            print(f"    - Kích thước: {team_stats['size']} bạn bè")
            print(f"    - Đã nhắn: {team_stats['messages_sent']} tin")
            print(f"    - Tiến độ: {team_stats['current_index']}/{team_stats['size']} ({team_stats['completion_rate']:.1f}%)")
        
        print("="*50)

# Convenience functions
def run_message_friends(driver, target_count=None, team_size=None):
    """Chạy nhắn tin bạn bè"""
    manager = MessageFriendManager()
    
    if team_size:
        manager.create_teams(team_size)
    
    manager.run_daily_messaging(driver, target_count)
    manager.print_statistics()

