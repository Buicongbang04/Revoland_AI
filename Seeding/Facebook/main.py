import sys
import os
import pandas as pd
import time
from util import (
    addNewFriend,
    acceptFriend,
    postNews,
    shareGroup,
    loginFacebookWithCookies,
    messageFriend,
    commentGroup,
)

sys.stdout.reconfigure(encoding="utf-8")


def show_account_menu(accounts: pd.DataFrame):
    print("\n====== DANH SÁCH TÀI KHOẢN ======")
    for stt, (_, account) in enumerate(accounts.iterrows(), 1):
        # account là một Series đại diện cho hàng hiện tại
        
        # Đảm bảo các cột acc_id, name, username tồn tại trước khi truy cập
        acc_id = account.get('acc_id', 'N/A')
        name = account.get('name', 'Unknown Name')
        username = account.get('username', 'N/A')
        
        print(f"{stt}. ID: {acc_id} | Tên: {name} ({username})")

    print("-1. Thoát chương trình") # Thường dùng 0 hoặc -1 cho thoát
    return input("Chọn tài khoản để xử lý: ")


def show_feature_menu():
    print("\n====== MENU CHỨC NĂNG ======")
    print("1. Thêm bạn mới")
    print("2. Chấp nhận lời mời kết bạn")
    print("3. Nhắn tin bạn bè")
    print("4. Đăng bài (post news)")
    print("5. Chia sẻ nhóm")
    print("6. Bình luận nhóm")
    print("0. Đăng xuất và chọn tài khoản khác")
    return input("Chọn chức năng: ")


def handle_account(account, groups):
    print(f"\n[INFO] Đang đăng nhập: {account['name']} ({account['username']})")
    driver = loginFacebookWithCookies.runLogin(f"data/account/cookie/{account['acc_id']}.json")

    if not driver:
        print(f"[ERROR] Đăng nhập thất bại cho {account['name']}")
        return

    print(f"[SUCCESS] Đăng nhập thành công cho {account['name']}")

    # Menu chức năng cho account này
    while True:
        choice = show_feature_menu()

        if choice == "1":
            addNewFriend.runAddFriend(groups, driver, max_scroll=2, max_requests=3)

        elif choice == "2":
            print(f"[INFO] Bắt đầu chấp nhận lời mời kết bạn cho {account['name']}")
            stats = acceptFriend.runAcceptFriend(driver, max_accept=100)
            print(f"[RESULT] Chấp nhận thành công {stats['successful_accepts']}/{stats['total_found']}")

        elif choice == "3":
            print(f"[INFO] Nhắn tin bạn bè cho {account['name']}")
            msg_manager = messageFriend.MessageFriendManager(
                friends_csv_path=f"data/friends/friends_{account['id']}.csv",
                messages_csv_path="data/content/messages.csv",
                progress_file=f"data/progress/message_progress_{account['id']}.json",
            )
            if not msg_manager.progress_data.get("teams"):
                msg_manager.create_teams(team_size=20)
            msg_manager.run_daily_messaging(driver, target_count=10)
            msg_manager.print_statistics()

        elif choice == "4":
            print(f"[INFO] Đăng bài cho {account['name']}")
            postNews.run_post(driver, "data/content/content.csv")

        elif choice == "5":
            print(f"[INFO] Chia sẻ bài viết vào nhóm cho {account['name']}")
            shareGroup.run_share(driver, groups, content_path="data/content/content.csv")

        elif choice == "6":
            print(f"[INFO] Bình luận nhóm cho {account['name']}")
            commentGroup.run_comment(driver, groups, content_path="data/content/content.csv")

        elif choice == "0":
            print(f"[INFO] Đăng xuất {account['name']}")
            driver.quit()
            break
        else:
            print("[ERROR] Lựa chọn không hợp lệ.")


def main():
    accounts = pd.read_csv("data/account/account.csv")
    groups = pd.read_csv("data/group/group.csv")

    while True:
        acc_choice = show_account_menu(accounts)

        if acc_choice == "-1":
            print("Thoát chương trình.")
            break

        try:
            acc_choice = int(acc_choice) - 1
            account = accounts.iloc[acc_choice]
        except (ValueError, IndexError):
            print("[ERROR] Lựa chọn không hợp lệ.")
            continue

        handle_account(account, groups)


if __name__ == "__main__":
    main()
