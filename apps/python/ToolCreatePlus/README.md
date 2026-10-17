# ChatGPT Auto Account Creator - Python Version

Tool tự động tạo tài khoản ChatGPT sử dụng Python + Selenium + undetected-chromedriver để bypass Cloudflare.

## 🚀 Cài đặt

### Bước 1: Cài Python packages

```bash
cd apps/python/ToolCreatePlus
pip install -r requirements.txt
```

### Bước 2: Cấu hình

Chỉnh sửa `config/python.config.json` từ thư mục root:

```json
{
  "defaultPassword": "DefaultPassw0rd!",
  "chatUrl": "https://chatgpt.com",
  "emailsFilePath": "data/input/newEmail.txt",
  "randomDataPath": "data/input/randomData.json",
  "otpAttempts": 4,
  "delayBetweenAccounts": 5
}
```

## 📝 Chạy tool

```bash
python apps/python/ToolCreatePlus/create_accounts.py
```

## ✨ Tính năng

- ✅ Bypass Cloudflare tự động (undetected-chromedriver)
- ✅ Tạo nhiều tài khoản ChatGPT từ file newEmail.txt
- ✅ Tự động lấy OTP từ dongvanfb.net
- ✅ Điền thông tin random từ randomData.json
- ✅ Human-like behavior (random delays, typing speed)
- ✅ Detect error pages và skip
- ✅ Sử dụng Chrome profile sạch
- ✅ Tổng kết kết quả cuối cùng

## 📂 Cấu trúc

```
atRegGPTpl/
├── apps/python/ToolCreatePlus/create_accounts.py
├── apps/python/ToolCreatePlus/Extension/
├── config/python.config.json
├── data/input/newEmail.txt
├── data/input/randomData.json
└── data/output/python/  # DoingProfile.txt, TaiKhoanThanhCong.txt
```

## ⚙️ Config Options

- `defaultPassword`: Mật khẩu mặc định cho tài khoản
- `chatUrl`: URL ChatGPT
- `mailReaderUrl`: URL mail reader
- `validSenders`: Danh sách email gửi hợp lệ
- `emailsFilePath`: Đường dẫn file emails
- `randomDataPath`: Đường dẫn file random data
- `otpAttempts`: Số lần thử lấy OTP
- `delayBetweenAccounts`: Delay giữa các tài khoản (giây)

## 🔧 Troubleshooting

### Lỗi ChromeDriver

```bash
pip install --upgrade undetected-chromedriver
```

### Cloudflare vẫn chặn

- Chạy lại, tool sẽ tự động retry
- undetected-chromedriver bypass tốt hơn Puppeteer

### Không tìm thấy element

- Website có thể đã thay đổi layout
- Check log để xem vấn đề ở đâu

## 📊 Output

Tool sẽ hiển thị:

- Progress cho mỗi tài khoản
- URL hiện tại
- Trạng thái từng bước
- Tổng kết cuối: Success/Failed/Total

## 🎯 So sánh với Node.js version

| Feature           | Node.js  | Python  |
| ----------------- | -------- | ------- |
| Bypass Cloudflare | ❌ Yếu   | ✅ Mạnh |
| Human-like        | ✅       | ✅      |
| OTP fetch         | ✅       | ✅      |
| Dễ debug          | ⚠️       | ✅      |
| Performance       | ✅ Nhanh | ✅ Ổn   |

Python version sử dụng **undetected-chromedriver** nên bypass Cloudflare tốt hơn nhiều!
