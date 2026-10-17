const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

// --- CẤU HÌNH ---
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const FILE_PATH = path.join(PROJECT_ROOT, "data", "input", "newEmail.txt");
const TARGET_URL = "https://dongvanfb.net/read_mail_box/";
const OUTPUT_FILE = path.join(
  PROJECT_ROOT,
  "data",
  "output",
  "otp_results.txt"
);

// Danh sách người gửi cần lấy (chữ thường)
const VALID_SENDERS = [
  "noreply@tm.openai.com",
  "otp@tm1.openai.com",
  ".openai.com", // Thêm dự phòng nếu họ đổi sub-domain
];

const delay = (time) => new Promise((resolve) => setTimeout(resolve, time));

(async () => {
  // Check if email line is provided as command line argument
  const emailLineArg = process.argv[2];

  let lines;
  if (emailLineArg && emailLineArg.trim()) {
    // Use the provided email line argument
    lines = [emailLineArg.trim()];
    console.log("[*] Chạy cho email: " + emailLineArg.split("|")[0]);
  } else {
    // Fallback: read from file if no argument provided
    if (!fs.existsSync(FILE_PATH)) {
      console.error(
        "[-] Lỗi: Không tìm thấy file newEmail.txt và không có argument"
      );
      return;
    }
    const data = fs.readFileSync(FILE_PATH, "utf-8");
    lines = data.split(/\r?\n/).filter((line) => line.trim() !== "");
    console.log(
      "[*] Đọc từ file newEmail.txt - tổng " + lines.length + " email"
    );
  }

  // Xóa file kết quả cũ
  if (fs.existsSync(OUTPUT_FILE)) fs.unlinkSync(OUTPUT_FILE);

  console.log("[*] Đang khởi động trình duyệt Chrome...");

  const browser = await puppeteer.launch({
    headless: false, // Để false để bạn quan sát tool chạy
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

      // Tìm ô nhập liệu
      const inputSelector = "textarea.form-control, textarea";
      await page.waitForSelector(inputSelector, { timeout: 10000 });

      // Xóa và nhập dữ liệu
      await page.$eval(inputSelector, (el) => (el.value = ""));
      await page.type(inputSelector, line);
      console.log("   [OK] Đã nhập dữ liệu.");

      // --- BƯỚC 2: NHẤN NÚT "ĐỌC HÒM THƯ" (CẬP NHẬT CLASS MỚI) ---
      // Class bạn cung cấp: "btn-buy-home mt-2 btn-checked"
      // Trong CSS Selector dấu cách thay bằng dấu chấm (.)
      const btnReadMailSelector = ".btn-buy-home.btn-checked";

      try {
        await page.waitForSelector(btnReadMailSelector, {
          visible: true,
          timeout: 5000,
        });
        await page.click(btnReadMailSelector);
        console.log('   [OK] Đã nhấn nút "Đọc hòm thư".');
      } catch (e) {
        throw new Error(
          "Không tìm thấy nút Đọc hòm thư (sai class hoặc web chưa load)."
        );
      }

      // --- BƯỚC 3: ĐỢI DỮ LIỆU ---
      console.log("   [...] Đang đợi thư về (10s)...");
      await delay(10000);

      // --- BƯỚC 4: QUÉT VÀ LẤY OTP (dùng class selectors để bền hơn) ---
      // Đợi bảng hiện ra (nếu có)
      try {
        await page.waitForSelector("table tbody tr", { timeout: 8000 });
      } catch (e) {
        // Nếu không có hàng nào, tiếp tục vòng lặp
      }

      const result = await page.evaluate((validSenders) => {
        const rows = Array.from(document.querySelectorAll("table tbody tr"));
        const collected = [];
        let firstCode = null;
        let firstCopyRow = null;
        const debug = [];

        const cleanText = (t) => {
          if (!t) return "";
          return t
            .replace(/=20/g, "")
            .replace(/\u00A0/g, " ")
            .replace(/\s+/g, " ")
            .trim();
        };

        rows.forEach((row, idx) => {
          const senderEl =
            row.querySelector(".readmail_from") ||
            row.querySelector("[class*='readmail_from']");
          const codeEl =
            row.querySelector(".readmail_code") ||
            row.querySelector("[class*='readmail_code']");
          const dateEl = row.querySelector(".readmail_date");
          const contentEl =
            row.querySelector(".content_email") ||
            row.querySelector(".content_email_content") ||
            row.querySelector("[class*='content_email']");

          const sender = senderEl
            ? senderEl.innerText.trim().toLowerCase()
            : "";

          const isValidSender = validSenders.some((s) => sender.includes(s));

          // Check if sender is from openai.com
          const isOpenAISender = sender.includes("openai.com");

          let code = null;
          const copyBtn = row.querySelector(".btn-quantity");
          const copyBtnFound = !!copyBtn;

          // If OpenAI sender without Copy button, extract from content directly
          if (isOpenAISender && !copyBtnFound && contentEl) {
            const rawContent = contentEl.innerText;
            const cleanContent = cleanText(rawContent);
            // Find 6-digit code in content
            const match = cleanContent.match(/\b\d{6}\b/);
            if (match) {
              code = match[0];
            }
          }

          // Otherwise, use the old method (from code element or content)
          if (!code) {
            const rawFromCode = codeEl ? codeEl.innerText : null;
            const rawFromContent = contentEl ? contentEl.innerText : null;
            const rawText = cleanText(
              rawFromCode ? rawFromCode : rawFromContent ? rawFromContent : ""
            );

            // Try strict 6-digit first, then tolerant search after normalizing digits
            let match = rawText.match(/\b\d{6}\b/);
            code = match ? match[0] : null;
            if (!code) {
              const normalized = rawText.replace(/[^0-9]/g, "");
              const m2 = normalized.match(/(\d{6})/);
              if (m2) code = m2[1];
            }
          }

          // Prepare rawText for debug output
          const rawFromCode = codeEl ? codeEl.innerText : null;
          const rawFromContent = contentEl ? contentEl.innerText : null;
          const rawText = cleanText(
            rawFromCode ? rawFromCode : rawFromContent ? rawFromContent : ""
          );

          // Save debug info per row
          debug.push({
            rowIndex: idx,
            sender,
            rawTextSnippet: rawText.slice(0, 160),
            isValidSender,
            hasMatch: !!code,
            code: code,
            copyBtnFound,
          });

          if (isValidSender) {
            if (code) {
              collected.push({
                sender,
                code,
                time: dateEl ? dateEl.innerText.trim() : "",
              });
              if (!firstCode) {
                if (copyBtnFound) {
                  try {
                    copyBtn.click();
                  } catch (e) {}
                  firstCopyRow = idx;
                }
                firstCode = code;
              }
            }
          }
        });

        return {
          collected,
          firstCode,
          firstCopyRow,
          rowsCount: rows.length,
          debug,
        };
      }, VALID_SENDERS);

      // Extra logs about rows and debug info
      console.log(`   [INFO] Số hàng trong bảng: ${result.rowsCount}`);
      if (result.rowsCount === 0)
        console.log("   [INFO] Bảng rỗng hoặc chưa tải thư.");
      // print debug lines for rows that had valid sender or match
      for (const d of result.debug || []) {
        if (d.isValidSender || d.hasMatch) {
          console.log(
            `   [ROW ${d.rowIndex + 1}] sender=${d.sender} validSender=${
              d.isValidSender
            } hasMatch=${d.hasMatch} code=${d.code || "-"} copyBtn=${
              d.copyBtnFound
            }`
          );
        }
      }
      if (result.firstCopyRow !== null) {
        console.log(
          `   [ACTION] Đã cố gắng nhấn nút Copy tại hàng #${
            result.firstCopyRow + 1
          }`
        );
      } else {
        console.log(
          `   [ACTION] Không tìm thấy nút Copy phù hợp (hoặc chưa có thư phù hợp).`
        );
      }

      // --- BƯỚC 5: IN KẾT QUẢ VÀ LƯU ---
      if (result.collected.length > 0) {
        console.log(
          `   [SUCCESS] Tìm thấy ${result.collected.length} mã. (Đã cố gắng nhấn Copy)`
        );

        let logContent = `\n--- Email: ${email} ---\n`;
        result.collected.forEach((item, index) => {
          const prefix = index === 0 ? ">>> (Mới nhất)" : "    (Cũ hơn)";
          console.log(
            `   ${prefix} Code: ${item.code} | Time: ${item.time} | From: ${item.sender}`
          );
          logContent += `Time: ${item.time} | Code: ${item.code} | From: ${item.sender}\n`;
        });

        // Ghi file kết quả
        fs.appendFileSync(OUTPUT_FILE, logContent);

        // Hiển thị mã mới nhất lên console (không ghi clipboard tại đây)
        if (result.firstCode) {
          console.log(`   -> Mã mới nhất: ${result.firstCode}`);
        }

        console.log(`   -> Đã lưu vào ${OUTPUT_FILE}`);
      } else {
        console.log("   [FAIL] Không có thư nào từ OpenAI.");
      }
    } catch (error) {
      console.log(`   [ERROR] Lỗi: ${error.message}`);
    }
  }

  console.log("\n[DONE] Hoàn thành toàn bộ.");

  // Close browser after getting OTP
  await browser.close();
})();
