import re
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_images(link):
    """Mở Selenium và lấy mã OTP từ liên kết"""
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome()
    cookie_file_path = 'tb.json'
    try:
        driver.get("https://world.taobao.com")

        # Đọc file cookie và thêm vào driver
        with open(cookie_file_path, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                # Chuyển đổi định dạng cookies nếu cần
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                if 'sameSite' not in cookie or cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    cookie['sameSite'] = 'Lax'
                driver.add_cookie(cookie)

        driver.get(link)
        logger.info(driver.page_source)
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'PicGallery--')]"))
        )
        image_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'PicGallery--')]//img")
        logger.info("waitted")
        logger.info(driver.page_source)
        print("something")
        wait = input("Press Enter to continue.")
        print("something")
        # Trích xuất liên kết hình ảnh
        logger.info(image_elements)
        image_links = []
        for img in image_elements:
            src = img.get_attribute('src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                image_links.append(src)
        logger.info(image_links)
        return image_links
    except TimeoutException as e:
        message = f"Lỗi: {e}"
        logger.error(message)
    except WebDriverException as e:
        message = f"Lỗi WebDriver: {e}"
        logger.error(message)
        send_telegram_message(TELEGRAM_ADMIN_UID, message)
    finally:
        driver.quit()
    return []

@app.route('/get_images', methods=['POST'])
def get_images():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    images = get_all_images(url)
    return jsonify({"images": images})

if __name__ == "__main__":
    app.run(debug=True)
