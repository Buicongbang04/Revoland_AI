import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def scroll_down(driver, delay=0.1):
    current_y = driver.execute_script("return window.scrollY;")
    target_y = current_y + random.choice([600, 1200])
    for y in range(current_y, target_y, 50):
        driver.execute_script(f"window.scrollTo(0, {y});")
        time.sleep(delay)
    driver.execute_script(f"window.scrollTo(0, {target_y});")
    print(f"[INFO] Scroll mượt từ {current_y} → {target_y}")


def comment_in_group(driver, content, ls_group):
    driver.refresh()
    time.sleep(2)

    driver.get(ls_group["Link"].values[0])
    time.sleep(7)

    actions = ActionChains(driver)

    comment_boxes = set()
    while len(comment_boxes) < 8:
        try:

            for _ in range(3):
                scroll_down(driver, delay=0.1)
                time.sleep(2)

                boxes = WebDriverWait(driver, 10).until(
                    EC.visibility_of_all_elements_located(
                        (By.XPATH, '//div[@aria-label="Viết bình luận"]')
                    )
                )

                print(boxes)
                print(len(boxes))

                for idx, box in enumerate(boxes):
                    if box not in comment_boxes:
                        actions.move_to_element(box).perform()
                        time.sleep(5)
                        can_click = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(box)
                        )
                        can_click.click()
                        time.sleep(2)
                        actions.send_keys(
                            random.choice(
                                ["nhà ở đâu ạ", "mình tham khảo giá được không"]
                            )
                        ).send_keys(Keys.ESCAPE).perform()
                        time.sleep(2)
                        comment_boxes.add(box)
                        print(f"[INFO] Đã comment xong {len(comment_boxes)} box")
                        if len(comment_boxes) >= 8:
                            break
                    else:
                        print(f"[INFO] Box {idx + 1} không comment được, bỏ qua")

        except TimeoutException:
            driver.refresh()
            time.sleep(2)

    # Chờ để xử lý
    print("[INFO] Hoàn tất vòng lặp. Đang giữ phiên để bạn quan sát...")
    while True:
        try:
            driver.title
            time.sleep(2)
        except Exception:
            print("[INFO] Trình duyệt đã đóng, kết thúc.")
            break
