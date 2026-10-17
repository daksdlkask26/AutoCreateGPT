# atRegGPTpl — ChatGPT Auto Account Creator

Tool tự động tạo tài khoản ChatGPT hàng loạt, hỗ trợ cả hai phiên bản **Node.js** và **Python**.

---

## 📁 Cấu trúc thư mục

```
atRegGPTpl/
├── apps/
│   ├── node/                       # Phiên bản Node.js (Puppeteer)
│   │   ├── create_accounts.js      # Script tạo tài khoản chính
│   │   ├── tool.js                 # Tiện ích hỗ trợ
│   │   └── backup.js               # Backup dữ liệu
│   └── python/
│       └── ToolCreatePlus/         # Phiên bản Python (Selenium)
│           ├── create_accounts.py  # Script tạo tài khoản chính
│           ├── requirements.txt    # Python dependencies
│           ├── README.md           # Hướng dẫn chi tiết Python version
│           └── Extension/          # Chrome extension hỗ trợ
├── config/
│   ├── node.config.json            # Cấu hình cho Node.js version
│   └── python.config.json          # Cấu hình cho Python version
├── data/
│   ├── input/
│   │   ├── newEmail.txt            # Danh sách email để đăng ký
│   │   ├── randomData.json         # Dữ liệu ngẫu nhiên (tên, sinh nhật...)
│   │   └── Bin.csv                 # Dữ liệu thẻ thanh toán
│   └── output/
│       ├── profiles/               # Chrome profiles (tự tạo khi chạy)
│       ├── otp_results.txt         # Kết quả OTP
│       ├── Bin.json                # Bin.csv đã convert sang JSON
│       └── python/
│           ├── TaiKhoanThanhCong.txt   # Tài khoản tạo thành công
│           └── DoingProfile.txt        # Profile đang xử lý
├── scripts/
│   ├── get_otp.py                  # Script lấy OTP từ mail
│   └── convert.py                  # Convert Bin.csv → Bin.json
└── package.json                    # Node.js dependencies
```

---

## ⚙️ Yêu cầu

### Node.js version
- Node.js >= 16
- Google Chrome đã cài đặt

```bash
npm install
```

### Python version
- Python >= 3.8
- Google Chrome đã cài đặt

```bash
cd apps/python/ToolCreatePlus
pip install -r requirements.txt
```

---

## 🚀 Sử dụng

### 1. Chuẩn bị dữ liệu đầu vào

- Thêm email vào `data/input/newEmail.txt` (mỗi email một dòng)
- Kiểm tra `data/input/randomData.json` có đủ dữ liệu ngẫu nhiên

### 2. Cấu hình

Chỉnh sửa file config tương ứng:

| Tham số | Mô tả |
|---|---|
| `defaultPassword` | Mật khẩu mặc định cho tài khoản |
| `chatUrl` | URL ChatGPT |
| `mailReaderUrl` | URL đọc mail OTP |
| `emailsFilePath` | Đường dẫn file danh sách email |
| `otpAttempts` | Số lần thử lấy OTP |
| `delayBetweenAccounts` | Thời gian chờ giữa các tài khoản (giây) |
| `headless` | Chạy Chrome ẩn (true/false) |

### 3. Chạy

**Node.js version:**
```bash
node apps/node/create_accounts.js
```

**Python version:**
```bash
python apps/python/ToolCreatePlus/create_accounts.py
```

---

## ✨ Tính năng

| Tính năng | Node.js | Python |
|---|---|---|
| Bypass Cloudflare | ⚠️ Puppeteer Stealth | ✅ undetected-chromedriver |
| Tự động lấy OTP | ✅ | ✅ |
| Human-like behavior | ✅ | ✅ |
| Dữ liệu profile ngẫu nhiên | ✅ | ✅ |
| Chrome extension hỗ trợ | — | ✅ |
| Dễ debug | ⚠️ | ✅ |

> **Khuyến nghị:** Dùng Python version để bypass Cloudflare hiệu quả hơn.

---

## 📊 Output

- Tài khoản thành công lưu tại `data/output/python/TaiKhoanThanhCong.txt`
- Log quá trình hiển thị trực tiếp trên terminal

---

## 🔧 Troubleshooting

**ChromeDriver lỗi:**
```bash
pip install --upgrade undetected-chromedriver
```

**Cloudflare vẫn chặn:** Chạy lại, tool sẽ tự động retry.

**Không tìm thấy element:** ChatGPT có thể đã thay đổi layout — kiểm tra log để xác định bước bị lỗi.
