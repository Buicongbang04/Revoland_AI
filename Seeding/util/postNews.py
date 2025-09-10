import re
import os
import sys
import json
import time
import random
import shutil
import tempfile
import math
from selenium.common.exceptions import TimeoutException
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from datetime import datetime
import pandas as pd


def post_to_facebook_group(driver: WebDriver, group_url: str, content, img):
    driver.get(group_url)
    time.sleep(random.uniform(4, 7))

    post_box = driver.find_element(
        By.XPATH,
        "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[4]/div/div[2]/div/div/div/div[1]/div/div/div/div[1]/div/div[1]/span",
    )

    if not post_box:
        print(f"[SKIP] Không tìm thấy nút 'Đăng bài'.")

    time.sleep(0.2)
    post_box.click()
    time.sleep(random.uniform(3, 5))

    # Nhập content
    active_box = driver.find_element(
        By.XPATH,
        "/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/div/div[1]/form/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div[1]/div[1]/div/div/div[1]",
    )
    active_box.send_keys(content)
    time.sleep(random.uniform(3, 5))

    # Tải hình ảnh lên
    file_input = driver.find_element(
        By.XPATH,
        "//input[@type='file' and @accept='image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv']",
    )
    file_input.send_keys(img)
    time.sleep(random.uniform(3, 5))

    # Nút đăng bài
    post_button = driver.find_element(By.XPATH, "//div[@aria-label='Đăng']")
    post_button.click()
    time.sleep(5)


def read_content(path):
    contents = pd.read_csv(path)
    contents["Status"] = contents["Status"].astype(int)
    return contents


def runPostNews(driver: WebDriver, groups: pd.DataFrame, path: str):
    print(f"[INFO] Bắt đầu quy trình đăng bài trên group.")

    contents = read_content(path)

    for idx, row in contents.iterrows():
        content, img_link, status = row
        if status == 0:  # Chưa đăng
            for fanpage, link in groups.values:
                print(f"[INFO] Tiến hành đăng bài trên group: {fanpage}")
                post_to_facebook_group(
                    driver, group_url=link, content=content, img=img_link
                )
                print(
                    f"[SUCCESS] Đăng thành công bài viết với ID: [{idx}] tại group: {fanpage}"
                )

            # Cập nhật Status thành đã đăng
            contents.at[idx, "Status"] = 1
            contents.to_csv(path, index=False)
        else:
            print(
                f"[WARNING] Bài viết với ID: [{idx}] đã được đăng, chuyển qua bài tiếp theo."
            )
            continue
