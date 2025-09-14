import json
import time
import random
import sys
import schedule
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import csv
import pandas as pd
import os
from util import (
    addNewFriend,
    acceptFriend,
    postNews,
    shareGroup,
    loginAccount,
    getAllFriend, 
    messageFriend
)

sys.stdout.reconfigure(encoding='utf-8')

def main(): 
    # Initialize account manager
    account_manager = loginAccount.getAccountManager() 
    
    # List available accounts
    account_manager.list_accounts() # In ra danh sách các account 
    
    groups = pd.read_csv("data/group/group-test.csv")
    content_path = "data/content/content.csv"
    
    for account in account_manager.accounts:
        print(f"[INFO] Đang xử lý tài khoản: {account['name']} ({account['username']})")
        driver = account_manager.run_login(account_id=account['id'])
        
        if driver:
            print(f"[SUCCESS] Đăng nhập thành công cho {account['name']}")
            
            # Thêm bạn mới
            # addNewFriend.run_add_friend(groups, driver, max_scroll=2, max_requests=3)
            
            # # Chấp nhận lời mời kết bạn
            # print(f"[INFO] Bắt đầu chấp nhận lời mời kết bạn cho {account['name']}")
            # acceptor = acceptFriend.FriendRequestAcceptor(driver)
            # accept_stats = acceptor.run_accept_friend_requests(
            #     max_accept=5,  # Chấp nhận tối đa 5 lời mời
            #     max_scroll=2   # Scroll 2 lần để tìm lời mời
            # )
            # print(f"[INFO] Kết quả chấp nhận lời mời: {accept_stats['successful_accepts']}/{accept_stats['total_found']} thành công")
            
            # Lấy danh sách bạn bè (chỉ chạy lần đầu hoặc khi cần cập nhật)
            if not os.path.exists(f"data/friends/friends_{account['id']}.csv"):
                print(f"[INFO] Bắt đầu lấy danh sách bạn bè cho {account['name']}")
                friend_scraper = getAllFriend.FacebookFriendScraper(f"data/friends/friends_{account['id']}.csv")
                friend_scraper.driver = driver
                if friend_scraper.run_scraping(max_scrolls=10):
                    friend_scraper.print_statistics()
            
            # Nhắn tin bạn bè
            print(f"[INFO] Bắt đầu nhắn tin bạn bè cho {account['name']}")
            message_manager = messageFriend.MessageFriendManager(
                friends_csv_path=f"data/friends/friends_{account['id']}.csv",
                messages_csv_path="data/content/messages.csv",
                progress_file=f"data/progress/message_progress_{account['id']}.json"
            )
            
            # Tạo đội nếu chưa có
            if not message_manager.progress_data.get('teams'):
                message_manager.create_teams(team_size=20)
            
            # Chạy nhắn tin hàng ngày
            message_manager.run_daily_messaging(driver, target_count=10)
            message_manager.print_statistics()
            
            time.sleep(5)
            driver.quit()
        else:
            print(f"[ERROR] Đăng nhập thất bại cho {account['name']}")
        
        
        print("\n" + "=" * 30 + "\n")

if __name__ == "__main__": 
    main() 
