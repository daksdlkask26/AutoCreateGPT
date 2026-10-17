import time
import re
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Cấu hình Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless") # Bỏ comment nếu muốn chạy ẩn danh (không hiện trình duyệt)
chrome_options.add_argument("--disable-notifications")
ROOT_DIR = Path(__file__).resolve().parents[1]
EMAILS_FILE = ROOT_DIR / "data" / "input" / "newEmail.txt"

def extract_otps(text):
    """Tìm tất cả các chuỗi 6 số (OTP) trong đoạn văn bản"""
    return re.findall(r'\b\d{6}\b', text)

def process_tool():
    # Kiểm tra file đầu vào
    if not EMAILS_FILE.exists():
        print("[-] Không tìm thấy file newEmail.txt")
        return

    # Khởi tạo trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # Truy cập website
        url = "https://dongvanfb.net/read_mail_box/"
        driver.get(url)

        with open(EMAILS_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            print(f"\n[*] Đang xử lý: {line.split('|')[0]}")

            try:
                # Tìm ô nhập dữ liệu (TextArea)
                input_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                input_field.clear()
                input_field.send_keys(line)

                # Tìm và nhấn nút thực hiện (Nút màu xanh)
                # Dựa trên ảnh, nút có thể là button với class success hoặc text chứa 'thực hiện'
                submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'thực hiện')]")
                submit_btn.click()

                # Đợi bảng kết quả hiện ra và tải xong (đợi khoảng vài giây cho realtime)
                time.sleep(5) 

                # Lấy tất cả nội dung trong bảng kết quả
                rows = driver.find_elements(By.XPATH, "//table//tr")
                
                all_otps = []
                for row in rows:
                    content = row.text
                    otps = extract_otps(content)
                    if otps:
                        all_otps.extend(otps)

                # Loại bỏ mã trùng và in ra kết quả
                unique_otps = list(set(all_otps))
                if unique_otps:
                    print(f"[+] Tìm thấy OTP: {', '.join(unique_otps)}")
                else:
                    print("[-] Không tìm thấy mã OTP nào.")

            except Exception as e:
                print(f"[!] Lỗi khi xử lý dòng này: {e}")
                continue

    except Exception as e:
        print(f"[!] Lỗi hệ thống: {e}")
    finally:
        print("\n[+] Đã hoàn thành danh sách.")
        driver.quit()

if __name__ == "__main__":
    process_tool()