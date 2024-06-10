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

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, message, retry_delay=30, max_attempts=5):
    """Gửi tin nhắn đến nhóm Telegram với khả năng thử lại sau khi gửi thất bại"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    attempt = 0
    while attempt < max_attempts:
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("Gửi tin nhắn Telegram thành công")
            return  # Thoát khỏi vòng lặp nếu gửi tin nhắn thành công
        except requests.exceptions.RequestException as e:
            logger.error("Gửi tin nhắn Telegram thất bại: %s", e)
            if attempt == max_attempts - 1:
                # Gửi tin nhắn cho admin sau khi thử max_attempts lần
                send_telegram_message(TELEGRAM_ADMIN_UID, f"Gửi tin nhắn Telegram thất bại sau {max_attempts} lần thử: {e}")
            logger.info(f"Thử lại sau {retry_delay} giây...")
            time.sleep(retry_delay)
            attempt += 1
    logger.error(f"Đã thử {max_attempts} lần, không thể gửi tin nhắn.")

def extract_links(text):
    """Tìm tất cả các liên kết https"""
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)
    return urls

def extract_codes(text):
    """Tìm mã 4 chữ số sau 'Enter this code to sign in'"""
    text = re.sub(r'\s+', ' ', text)
    codes = re.search(r'(?<=Enter this code to sign in )\d{4}', text)
    if codes:
        return codes.group()
    codes = re.search(r'(?<=Mã đăng nhập )\d{4}', text)
    if codes:
        return codes.group()
    return None

def get_all_images(link):
    """Mở Selenium và lấy mã OTP từ liên kết"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Remote(
        command_executor='http://tb_watcher_selenium:4444/wd/hub',
        options=options
    )
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

if __name__ == "__main__":
    logger.info('KHỞI TẠO THÀNH CÔNG')
    url = input("Nhập URL: ")
    images = get_all_images(url)
    logger.info(f"Số lượng hình ảnh: {len(images)}")
    for i, image in enumerate(images, start=1):
        logger.info(f"Link hình ảnh {i}: {image}")
