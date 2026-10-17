const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

// Cấu hình
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const FILE_PATH = path.join(PROJECT_ROOT, "data", "input", "newEmail.txt");
const OUTPUT_FILE = path.join(
  PROJECT_ROOT,
  "data",
  "output",
  "otp_results.txt"
);
const TARGET_URL = "https://dongvanfb.net/read_mail_box/";

const delay = (time) => new Promise((resolve) => setTimeout(resolve, time));

(async () => {
  // 1. Kiểm tra file đầu vào
  if (!fs.existsSync(FILE_PATH)) {
    console.error("[-] Lỗi: Không tìm thấy file newEmail.txt");
    return;
  }

  const data = fs.readFileSync(FILE_PATH, "utf-8");
  const lines = data.split(/\r?\n/).filter((line) => line.trim() !== "");

  console.log("[*] Đang khởi động trình duyệt Chrome...");

  const browser = await puppeteer.launch({
    headless: false, // Hiện trình duyệt để bạn theo dõi
    defaultViewport: null,
    args: ["--start-maximized", "--no-sandbox", "--disable-setuid-sandbox"],
  });

  const page = await browser.newPage();

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const email = line.split("|")[0];
    console.log(`\n==================================================`);
    console.log(`[${i + 1}/${lines.length}] Đang xử lý: ${email}`);

    try {
      // --- BƯỚC 1: TRUY CẬP VÀ NHẬP LIỆU ---
      await page.goto(TARGET_URL, { waitUntil: "domcontentloaded" });

      // Đợi ô nhập liệu xuất hiện
      const inputSelector = "textarea.form-control, textarea";
      await page.waitForSelector(inputSelector, { timeout: 10000 });

      // Xóa cũ nhập mới
      await page.$eval(inputSelector, (el) => (el.value = ""));
      await page.type(inputSelector, line);
      console.log("   [OK] Đã nhập dữ liệu.");

      // --- BƯỚC 2: NHẤN NÚT ĐỌC HÒM THƯ (FIX LỖI) ---
      // Tìm nút bằng XPath chứa chữ "thực hiện" (bất kể class là gì)
      const buttonXPath = "//button[contains(., 'thực hiện')]";
      await page.waitForXPath(buttonXPath, { timeout: 5000 });
      const [submitBtn] = await page.$x(buttonXPath);

      if (submitBtn) {
        await submitBtn.click();
        console.log('   [OK] Đã nhấn nút "Đang thực hiện".');
      } else {
        throw new Error("Không tìm thấy nút bấm!");
      }

      // --- BƯỚC 3: ĐỢI DỮ LIỆU ---
      console.log("   [...] Đang quét hộp thư (đợi 15s)...");
      await delay(15000); // Đợi 15 giây để web tải thư về

      // --- BƯỚC 4: XỬ LÝ KẾT QUẢ ---
      // Chạy logic ngay trong trình duyệt để lấy dữ liệu chính xác nhất
      const result = await page.evaluate(() => {
        const rows = document.querySelectorAll("table tbody tr");

        // Duyệt qua từng dòng thư
        for (const row of rows) {
          const cells = row.querySelectorAll("td");
          if (cells.length < 6) continue;

          const sender = cells[2].innerText.trim().toLowerCase(); // Cột From
          const rawContent = cells[5].innerText.trim(); // Cột Code

          // ĐIỀU KIỆN LỌC:
          // 1. Người gửi phải có đuôi .openai.com
          // 2. Cột Code không được rỗng
          if (sender.includes(".openai.com") && rawContent.length > 0) {
            // Lọc lấy 6 số từ cột Code
            const match = rawContent.match(/\b\d{6}\b/);
            if (match) {
              return {
                success: true,
                email: sender,
                code: match[0],
                fullText: rawContent,
              };
            }
          }
        }
        return { success: false };
      });

      // --- BƯỚC 5: IN KẾT QUẢ RA MÀN HÌNH ---
      if (result.success) {
        console.log(`   [SUCCESS] TÌM THẤY OTP!`);
        console.log(`   + Người gửi: ${result.email}`);
        console.log(`   + OTP CODE : ${result.code}`);

        // (Tùy chọn) Lưu kết quả vào file
        fs.appendFileSync(OUTPUT_FILE, `${email} | ${result.code}\n`);
        console.log(`   -> Đã lưu vào file otp_results.txt`);
      } else {
        console.log("   [FAIL] Không tìm thấy thư OpenAI hoặc chưa có mã.");
      }
    } catch (error) {
      console.log(`   [ERROR] Lỗi ở bước này: ${error.message}`);
    }
  }

  console.log("\n[DONE] Hoàn thành toàn bộ danh sách.");
  // await browser.close(); // Bỏ comment nếu muốn tự động tắt
})();
