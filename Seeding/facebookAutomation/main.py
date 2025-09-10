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
from util import addNewFriend, loginFacebookWithCookies, acceptFriend, postNews

sys.stdout.reconfigure(encoding="utf-8")


def main():
    accounts = os.listdir("data/account")
    groups = pd.read_csv("data/group/group-test.csv")
    content_path = "data/content/content.csv"

    for acc in accounts:
        cookiePath = "data/account/" + acc
        driver = loginFacebookWithCookies.runLogin(cookiePath)

        # addNewFriend.runAddFriend(groups, driver, max_scroll=2, max_requests=3)
        # acceptFriend.runAcceptFriend(driver=driver)

        if driver:
            postNews.runPostNews(driver=driver, groups=groups, path=content_path)
        else:
            print(f"Failed to login with cookies for account: {acc}")


if __name__ == "__main__":
    main()
