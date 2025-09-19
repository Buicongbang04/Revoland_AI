# shareGroup.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def open_post(driver, post_url: str, timeout: int = 15):
    """
    Mở bài post Facebook và đợi load xong.
    """
    try:
        print(f"[INFO] Điều hướng tới post: {post_url}")
        driver.get(post_url)

        # Đợi body load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Kiểm tra URL
        cur = (driver.current_url or "").lower()
        if "login" in cur or "checkpoint" in cur or "error" in cur:
            print("[ERROR] Không thể truy cập post (login/checkpoint/error).")
            return False

        print("[INFO] Đã mở post thành công.")
        return True

    except Exception as e:
        print(f"[ERROR] Lỗi trong open_post: {e}")
        return False


def find_share_btn(
    driver, share_label: str, max_tabs: int = 200, tab_delay: float = 0.3
):
    """
    TAB để tìm nút Chia sẻ dựa trên aria-label.
    """
    try:
        actions = ActionChains(driver)
        found_share = False

        for _ in range(max_tabs):
            actions.send_keys(Keys.TAB).perform()
            time.sleep(tab_delay)  # độ trễ mỗi lần tab

            active = driver.switch_to.active_element
            aria = active.get_attribute("aria-label") or ""
            if share_label in aria:
                active.click()
                print("[INFO] Đã click nút Chia sẻ, chờ popup hiện ra...")
                found_share = True
                time.sleep(2)
                break

        if not found_share:
            print("[WARN] Không tìm thấy nút Chia sẻ bằng TAB")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Lỗi trong find_share_btn: {e}")
        return False


def find_gr_btn(driver, group_label: str, max_tabs: int = 300, tab_delay: float = 0.35):
    """
    TAB để tìm nút Nhóm dựa trên text hoặc aria-label.
    """
    try:
        actions = ActionChains(driver)
        found_group = False

        for i in range(max_tabs):
            actions.send_keys(Keys.TAB).perform()
            time.sleep(tab_delay)  # độ trễ mỗi lần tab

            active = driver.switch_to.active_element
            text = (active.text or "").strip()
            aria = active.get_attribute("aria-label") or ""

            if group_label in text or group_label in aria:
                try:
                    active.click()
                except Exception as e:
                    print(f"[WARN] Không thể click nút {group_label}: {e}")
                found_group = True
                time.sleep(2)
                break

        if not found_group:
            print(f"[WARN] Không tìm thấy nút '{group_label}' trong popup")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Lỗi trong find_gr_btn: {e}")
        return False


def find_target_group(driver, btn_label, tab: int):
    actions = ActionChains(driver)

    print("[INFO] Bắt đầu chọn nhóm...")
    for _ in range(tab):
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.35)

    active = driver.switch_to.active_element
    text = (active.text or "").strip()
    if text:
        print(f"[INFO] Đã chọn nhóm: {text}")
        try:
            active.click()
            print("[INFO] Đã click chọn nhóm.")
        except Exception as e:
            print(f"[WARN] Không thể click chọn nhóm: {e}")
        time.sleep(3)
        # Dán nội message vào ô nhập
        actions.send_keys("Bài viết hay, mọi người cùng xem nhé!").perform()
        time.sleep(2)
        for _ in range(200):
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.3)

            active = driver.switch_to.active_element
            text = (active.text or "").strip()
            aria = active.get_attribute("aria-label") or ""

            if btn_label in text or btn_label in aria:
                actions.send_keys(Keys.ENTER).perform()
                break
        print("[INFO] Đã gửi bài vào nhóm.")
        time.sleep(5)


def share_to_group(driver, post_url: str, timeout: int = 15):
    """
    Mở bài post Facebook, TAB tìm nút Chia sẻ, click ->
    tiếp tục TAB tìm nút 'Nhóm' trong popup.
    """
    try:
        for i in range(3, 18, 2):
            # Bước 1: Mở bài post
            if not open_post(driver, post_url, timeout):
                return False

            print("[INFO] Đã mở post, bắt đầu TAB để tìm nút Chia sẻ...")

            # Bước 2: Tìm nút Chia sẻ
            if not find_share_btn(
                driver,
                "Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn.",
                max_tabs=200,
                tab_delay=0.5,
            ):
                return False

            # Bước 3: Tìm nút 'Nhóm'
            if not find_gr_btn(
                driver,
                "Nhóm",
                max_tabs=300,
                tab_delay=0.5,
            ):
                return False

            # Bước 4: Chia sẻ vào nhóm
            find_target_group(driver=driver, btn_label="Đăng", tab=i)
            time.sleep(5)

    except Exception as e:
        print(f"[ERROR] Lỗi trong share_to_group: {e}")
        return False
