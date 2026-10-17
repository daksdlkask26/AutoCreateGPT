# ChatGPT Auto Account Creator

A tool for automating bulk ChatGPT account creation, with two supported implementations: **Node.js** and **Python**.

---

## 📁 Project Structure

```
atRegGPTpl/
├── apps/
│   ├── node/                       # Node.js version (Puppeteer)
│   │   ├── create_accounts.js      # Main account creation script
│   │   ├── tool.js                 # Helper utilities
│   │   └── backup.js               # Data backup
│   └── python/
│       └── ToolCreatePlus/         # Python version (Selenium)
│           ├── create_accounts.py  # Main account creation script
│           ├── requirements.txt    # Python dependencies
│           ├── README.md           # Detailed guide for the Python version
│           └── Extension/          # Supporting Chrome extension
├── config/
│   ├── node.config.json            # Config for the Node.js version
│   └── python.config.json          # Config for the Python version
├── data/
│   ├── input/
│   │   ├── newEmail.txt            # List of emails to register
│   │   ├── randomData.json         # Random data (names, birthdays, etc.)
│   │   └── Bin.csv                 # Payment card data
│   └── output/
│       ├── profiles/               # Chrome profiles (auto-generated at runtime)
│       ├── otp_results.txt         # OTP results
│       ├── Bin.json                # Bin.csv converted to JSON
│       └── python/
│           ├── TaiKhoanThanhCong.txt   # Successfully created accounts
│           └── DoingProfile.txt        # Profile currently being processed
├── scripts/
│   ├── get_otp.py                  # Script for fetching OTP from mail
│   └── convert.py                  # Converts Bin.csv → Bin.json
└── package.json                    # Node.js dependencies
```

---

## ⚙️ Requirements

### Node.js version
- Node.js >= 16
- Google Chrome installed

```bash
npm install
```

### Python version
- Python >= 3.8
- Google Chrome installed

```bash
cd apps/python/ToolCreatePlus
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Prepare input data

- Add emails to `data/input/newEmail.txt` (one email per line)
- Make sure `data/input/randomData.json` contains enough random data

### 2. Configuration

Edit the corresponding config file:

| Parameter | Description |
|---|---|
| `defaultPassword` | Default password for accounts |
| `chatUrl` | ChatGPT URL |
| `mailReaderUrl` | OTP mail reader URL |
| `emailsFilePath` | Path to the email list file |
| `otpAttempts` | Number of OTP retrieval attempts |
| `delayBetweenAccounts` | Delay between accounts (seconds) |
| `headless` | Run Chrome headless (true/false) |

### 3. Run

**Node.js version:**
```bash
node apps/node/create_accounts.js
```

**Python version:**
```bash
python apps/python/ToolCreatePlus/create_accounts.py
```

---

## ✨ Features

| Feature | Node.js | Python |
|---|---|---|
| Cloudflare bypass | ⚠️ Puppeteer Stealth | ✅ undetected-chromedriver |
| Automatic OTP retrieval | ✅ | ✅ |
| Human-like behavior | ✅ | ✅ |
| Random profile data | ✅ | ✅ |
| Supporting Chrome extension | — | ✅ |
| Easy to debug | ⚠️ | ✅ |

> **Recommendation:** Use the Python version for more reliable Cloudflare bypass.

---

## 📊 Output

- Successful accounts are saved to `data/output/python/TaiKhoanThanhCong.txt`
- Progress logs are printed directly to the terminal

---

## 🔧 Troubleshooting

**ChromeDriver errors:**
```bash
pip install --upgrade undetected-chromedriver
```

**Still blocked by Cloudflare:** Re-run the tool, it will automatically retry.

**Element not found:** ChatGPT's layout may have changed — check the logs to identify which step failed.
