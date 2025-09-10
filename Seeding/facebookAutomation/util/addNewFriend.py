import json
import time
import random
import sys
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
from selenium.webdriver.chrome.webdriver import WebDriver
from datetime import datetime
import pandas as pd
import csv


def scroll_and_get_post_authors(driver, max_scroll=5):
    authors = set()

    for _ in range(max_scroll):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(3)

        try:
            # Lấy tất cả thẻ <a> có chứa "/user/" trong href
            a_tags = driver.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                try:
                    href = a.get_attribute("href")
                    if href and "/user/" in href:
                        # Loại bỏ query params nếu có
                        clean_href = href.split("?")[0]
                        full_url = (
                            f"https://m.facebook.com{clean_href}"
                            if clean_href.startswith("/")
                            else clean_href
                        )
                        authors.add(full_url)
                except:
                    continue  # Bỏ qua nếu phần tử bị lỗi
        except Exception as e:
            print(f"[WARNING] Lỗi khi xử lý thẻ <a>: {e}")

    print(f"[INFO] Tìm thấy {len(authors)} người đăng bài.")
    return list(authors)


def check_spam_flag(driver) -> bool:
    """
    Đợi tối đa 3s để phát hiện dialog spam-flag chứa đúng dòng text:
      "Giờ bạn chưa dùng được tính năng này"
    Nếu tìm thấy, in cảnh báo, đóng dialog và trả về True.
    Nếu không tìm thấy sau timeout, trả về False.
    """
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@role='dialog' and .//div[@aria-hidden='false']]"
                    "//h2/span[normalize-space(text())='Giờ bạn chưa dùng được tính năng này']",
                )
            )
        )
        # Nếu đến đây nghĩa là dialog spam-flag xuất hiện
        print(
            "[WARNING] Tài khoản này đã bị giới hạn (spam flag). Bỏ qua sang tài khoản mới."
        )
        # Nhấn ESC hai lần để đóng dialog
        ActionChains(driver).send_keys(Keys.ESCAPE).send_keys(Keys.ESCAPE).perform()
        return True

    except TimeoutException:
        # Không tìm thấy đúng dialog đó trong 3s → không phải spam-flag
        return False


def send_friend_request(driver, profile_url):
    print(f"[INFO] Truy cập profile: {profile_url}")
    driver.get(profile_url)
    time.sleep(5)

    try:
        # Kiểm tra nút đã gửi kết bạn hoặc đã là bạn bè
        buttons = driver.find_elements(By.XPATH, "//div[@role='button']")
        for btn in buttons:
            aria_label = btn.get_attribute("aria-label") or ""
            if any(
                kw in aria_label
                for kw in [
                    "Hủy lời mời",
                    "Đã gửi",
                    "Bạn bè",
                    "Cancel Request",
                    "Friends",
                ]
            ):
                print(f"[SKIP] Đã gửi kết bạn hoặc đã là bạn bè với: {profile_url}")
                return "skip", "already_friends_or_requested"

        # Tìm nút thêm bạn bè
        add_buttons = driver.find_elements(
            By.XPATH,
            "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div/div/div[4]/div/div/div[2]/div/div/div/div[1]/div[2]/span",
        )

        if not add_buttons:
            print(f"[SKIP] Không tìm thấy nút 'Thêm bạn bè', chuyển sang profile mới.")
            return "skip", "no_add_button"

        add_button = add_buttons[0]
        time.sleep(0.2)
        add_button.click()

        # Kiểm tra spam flag
        if check_spam_flag(driver):
            print(f"[INFO] Tài khoản bị spam flag khi xử lý: {profile_url}")
            return "flagged", "spam_flag"

        print(f"[SUCCESS] Đã gửi lời mời kết bạn đến: {profile_url}")
        time.sleep(12 + (time.time() % 2))
        return "sent", "ok"

    except Exception as e:
        print(f"[ERROR] Không gửi được lời mời ({profile_url}): {e}")
        return "error", str(e)


def addFullAuthors(driver: WebDriver, authorsList, max_requests=15):
    account_friends_sent = 0
    account_status = "completed"
    account_detail = ""
    friend_request_count = 0

    for i, author_url in enumerate(authorsList):
        if friend_request_count >= max_requests:
            print(f"[INFO] Đã gửi đủ {max_requests} lời mời, dừng tài khoản.")
            break

        print(f"\n[{i+1}/{len(authorsList)}] Xử lý: {author_url}")
        status, detail = send_friend_request(driver, author_url)

        if status == "sent":
            friend_request_count += 1
            account_friends_sent = friend_request_count
            print(
                f"[INFO] Gửi thành công. Tổng đã gửi: {friend_request_count}/{max_requests}"
            )

        elif status == "flagged":
            account_status = "flagged"
            account_detail = detail
            account_friends_sent = friend_request_count
            print(
                f"[INFO] Tài khoản bị flag sau khi gửi {friend_request_count} lời mời."
            )
            break

        elif status == "error":
            account_status = "stopped_error"
            account_detail = detail
            account_friends_sent = friend_request_count
            print(f"[INFO] Dừng vì lỗi sau {friend_request_count} lời mời: {detail}")
            break

        if friend_request_count >= max_requests:
            account_status = "completed"
            account_friends_sent = friend_request_count
            break

        delay = random.randint(3, 8)
        print(f"[INFO] Đợi {delay} giây trước khi kết bạn tiếp theo...")
        time.sleep(delay)

    if account_status in ("flagged", "stopped_error"):
        return

    if account_status == "completed":
        account_friends_sent = friend_request_count

    print(
        f"[INFO] Hoàn thành gửi kết bạn! trạng thái: {account_status}, đã gửi: {account_friends_sent}."
    )
    print("[INFO] Nghỉ trước khi chuyển sang tài khoản tiếp theo...\n")
    time.sleep(3 + random.uniform(3, 5))


def runAddFriend(groups: pd.DataFrame, driver: WebDriver, max_scroll=2, max_requests=3):
    for group in groups.values:
        print(f"[INFO] Truy cập group: {group[0]} với đường dẫn: {group[1]}")

        driver.get(group[1])
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        if "login" in driver.current_url:
            print("[ERROR] Cookie sai hoặc hết hạn!")
            continue
        else:
            print(f"[INFO] Truy cập thành công group: {group[0]}")

        # Lấy danh sách người đăng bài trong group
        authorsList = scroll_and_get_post_authors(driver, max_scroll=max_scroll)

        addFullAuthors(
            driver=driver, authorsList=authorsList, max_requests=max_requests
        )
