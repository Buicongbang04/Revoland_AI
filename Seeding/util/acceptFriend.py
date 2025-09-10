import json
import time
import random
import os
import pandas as pd
from datetime import datetime

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import logging
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver


def getFriendRequests(driver: WebDriver, max_scroll=5):
    users = set()

    for _ in range(max_scroll):
        try:
            a_tags = driver.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                try:
                    href = a.get_attribute("href")
                    if href and "/profile." in href:
                        users.add(href)
                except:
                    continue
        except Exception as e:
            print(f"[WARNING] Lỗi khi xử lý thẻ <a>: {e}")

    print(f"[INFO] Tìm thấy {len(users)} lời mời kết bạn.")
    return list(users)


def accept_friend_requests(driver: WebDriver, user_url):
    driver.get(user_url)
    time.sleep(5)
    acceptButton = driver.find_elements(
        By.XPATH,
        "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div/span",
    )

    if not acceptButton:
        print(f"[SKIP] Không tìm thấy nút 'Chấp nhận lời mời kết bạn'.")

    acceptButton = acceptButton[0]
    time.sleep(0.2)
    acceptButton.click()

    print(f"[SUCCESS] Chấp nhận kết bạn thành công: {user_url}")
    time.sleep(random.uniform(5, 8))


def runAcceptFriend(driver: WebDriver, max_accept=5):
    print(f"[INFO] Bắt đầu quy trình chấp nhận lời mời kết bạn.")
    friend_requests_url = "https://m.facebook.com/friends/requests"
    driver.get(friend_requests_url)
    time.sleep(random.uniform(4, 8))
    friendRequests = getFriendRequests(driver)
    print(friendRequests)
    for i, url in enumerate(friendRequests):
        print(f"[{i}/{len(friendRequests)}] Truy cập lời mời từ url: {url}")
        accept_friend_requests(driver=driver, user_url=url)
