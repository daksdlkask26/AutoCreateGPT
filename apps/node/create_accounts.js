const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
puppeteer.use(StealthPlugin());

const PROJECT_ROOT = path.resolve(__dirname, "../..");
const CONFIG_PATH = path.join(PROJECT_ROOT, "config", "node.config.json");
const EMAILS_PATH = path.join(PROJECT_ROOT, "data", "input", "newEmail.txt");
const RANDOM_DATA = path.join(
  PROJECT_ROOT,
  "data",
  "input",
  "randomData.json"
);

const delay = (ms) => new Promise((res) => setTimeout(res, ms));
const isAbsoluteLike = (targetPath) =>
  path.isAbsolute(targetPath) || /^[A-Za-z]:[\\/]/.test(targetPath);
const resolveFromProjectRoot = (targetPath) =>
  isAbsoluteLike(targetPath)
    ? targetPath
    : path.join(PROJECT_ROOT, targetPath);

if (!fs.existsSync(CONFIG_PATH)) {
  console.error("Missing config/node.config.json");
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
const defaultPassword = config.defaultPassword || "DefaultPassw0rd!";
const profilesDir = resolveFromProjectRoot(
  config.profilesDir || "data/output/profiles"
);
const headless = !!config.headless;
const chatUrl = config.chatUrl || "https://chatgpt.com";
const useInstalledChrome = config.useInstalledChrome !== false;
const chromePath =
  config.chromePath ||
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const waitForCloudflareBypass = config.waitForCloudflareBypass !== false;
const useSharedProfile = config.useSharedProfile !== false;
const sharedProfilePath =
  config.sharedProfilePath ||
  path.join(PROJECT_ROOT, "data", "output", "chrome-profile-clean");
const MAIL_READER_URL = "https://dongvanfb.net/read_mail_box/";
const MAIL_TEXTAREA_SELECTOR = "textarea.form-control, textarea";
const MAIL_READ_BTN = ".btn-buy-home.btn-checked";

if (!fs.existsSync(EMAILS_PATH)) {
  console.error("Missing newEmail.txt");
  process.exit(1);
}

const lines = fs
  .readFileSync(EMAILS_PATH, "utf8")
  .split(/\r?\n/)
  .filter(Boolean);
let randomPool = [];
if (fs.existsSync(RANDOM_DATA))
  randomPool = JSON.parse(fs.readFileSync(RANDOM_DATA, "utf8"));

(async () => {
  if (!fs.existsSync(profilesDir))
    fs.mkdirSync(profilesDir, { recursive: true });

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const email = line.split("|")[0];
    console.log(
      `\n=== [${i + 1}/${lines.length}] Starting account creation for: ${email}`
    );

    // Use shared clean profile or create dedicated profile folder
    let profilePath;
    if (useSharedProfile) {
      profilePath = sharedProfilePath;
      if (!fs.existsSync(profilePath)) {
        fs.mkdirSync(profilePath, { recursive: true });
        console.log(" - Created shared profile at:", profilePath);
      }
      console.log(" - Using shared Chrome profile (no Cloudflare)");
    } else {
      // create a dedicated profile folder for this email
      const safeName = email.replace(/[^a-z0-9@.\-_]/gi, "_");
      profilePath = path.join(profilesDir, safeName);
      if (!fs.existsSync(profilePath))
        fs.mkdirSync(profilePath, { recursive: true });
    }

    const launchOptions = {
      headless: false,
      userDataDir: profilePath,
      defaultViewport: {
        width: 1920,
        height: 1080,
      },
      args: [
        "--start-maximized",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-web-security",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      ],
      ignoreDefaultArgs: ["--enable-automation"],
    };

    // Use installed Chrome if available
    if (useInstalledChrome && fs.existsSync(chromePath)) {
      launchOptions.executablePath = chromePath;
      console.log(" - Using installed Chrome at:", chromePath);
    }

    const browser = await puppeteer.launch(launchOptions);

    try {
      const page = await browser.newPage();
      page.setDefaultTimeout(30000);

      // Set realistic user agent and navigator properties
      await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, "webdriver", { get: () => false });
        Object.defineProperty(navigator, "languages", {
          get: () => ["en-US", "en"],
        });
        Object.defineProperty(navigator, "plugins", {
          get: () => [1, 2, 3, 4, 5],
        });
      });

      console.log(" - Navigating to", chatUrl);
      await page.goto(chatUrl, { waitUntil: "networkidle2", timeout: 60000 });

      // Check if Cloudflare challenge is present
      if (waitForCloudflareBypass) {
        const hasCloudflare = await page.evaluate(() => {
          const text = document.body.innerText.toLowerCase();
          return (
            text.includes("cloudflare") ||
            text.includes("verify you are human") ||
            text.includes("checking your browser")
          );
        });

        if (hasCloudflare) {
          console.log("\n⚠️  CLOUDFLARE DETECTED!");
          console.log(
            "   Please manually complete the Cloudflare challenge in the browser."
          );
          console.log(
            "   After you see the ChatGPT homepage, press ENTER here to continue..."
          );

          // Wait for user to press Enter
          await new Promise((resolve) => {
            const readline = require("readline").createInterface({
              input: process.stdin,
              output: process.stdout,
            });
            readline.question("", () => {
              readline.close();
              resolve();
            });
          });

          console.log("   ✓ Continuing automation...");
        }
      }

      await delay(3000 + Math.random() * 2000); // Random delay 3-5s

      // Click 'Sign up for free' button to start registration
      try {
        let clicked = false;
        await delay(2000 + Math.random() * 1000); // Random delay 2-3s

        // 1) Try to find "Sign up" button by text
        clicked = await page.evaluate(() => {
          const buttons = Array.from(document.querySelectorAll("button, a"));
          for (const b of buttons) {
            const text = (b.innerText || b.textContent || "")
              .trim()
              .toLowerCase();
            if (text.includes("sign up") || text.includes("signup")) {
              try {
                b.click();
                return true;
              } catch (e) {}
            }
          }
          return false;
        });
        if (clicked) {
          console.log(" - Clicked Sign up button");
        }

        // 2) Fallback: try data-testid for signup
        if (!clicked) {
          try {
            const signupBtn = await page.$(
              'button[data-testid="signup-button"], a[href*="signup"]'
            );
            if (signupBtn) {
              await signupBtn.click();
              console.log(" - Clicked Sign up via selector");
              clicked = true;
            }
          } catch (e) {}
        }

        if (!clicked)
          console.log(" - Sign up button not found, continuing anyway");
      } catch (e) {
        console.log(" - Error clicking sign up button:", e.message || e);
      }

      // Wait for modal or email input
      await delay(1500);
      // Try common email input selectors
      const emailSelectors = [
        "input[type='email']",
        "input[name='email']",
        "input[id*='email']",
      ];
      let emailInput = null;
      for (const sel of emailSelectors) {
        try {
          const el = await page.$(sel);
          if (el) {
            emailInput = el;
            break;
          }
        } catch (e) {}
      }

      if (!emailInput) {
        // try within modal: find input by placeholder using evaluate
        emailInput = await page.evaluateHandle(() => {
          const inputs = Array.from(document.querySelectorAll("input"));
          return (
            inputs.find((inp) => {
              const ph = (inp.placeholder || "").toLowerCase();
              return ph.includes("email");
            }) || null
          );
        });
        if (emailInput && emailInput.asElement && !emailInput.asElement())
          emailInput = null;
      }

      if (!emailInput) {
        console.log(" - Email input not found. Page may have different flow.");
      } else {
        await delay(500 + Math.random() * 500); // Random delay before typing
        await emailInput.click({ clickCount: 3 });
        await delay(300);
        // Type with human-like speed variations
        for (const char of email) {
          await emailInput.type(char, { delay: 80 + Math.random() * 80 });
        }
        console.log(" - Entered email");
        await delay(1500 + Math.random() * 1000); // Longer random delay 1.5-2.5s

        // Click Continue button using evaluate
        let clickedContinue = await page.evaluate(() => {
          const buttons = Array.from(document.querySelectorAll("button"));
          for (const btn of buttons) {
            const text = (btn.innerText || btn.textContent || "")
              .trim()
              .toLowerCase();
            if (text === "continue" || text.includes("continue")) {
              try {
                btn.click();
                return true;
              } catch (e) {}
            }
          }
          return false;
        });
        if (!clickedContinue) {
          // fallback press Enter in email input
          await page.keyboard.press("Enter");
          console.log(" - Pressed Enter to submit email");
        } else {
          console.log(" - Clicked Continue");
        }

        // Wait for navigation and check for error page
        await delay(4000);
        const currentUrl = page.url();
        console.log(" - Current URL:", currentUrl);

        if (
          currentUrl.includes("/api/auth/error") ||
          currentUrl.includes("/error")
        ) {
          console.log("\n❌ ERROR: ChatGPT returned auth error page");
          const errorInfo = await page.evaluate(() => {
            return document.body.innerText;
          });
          console.log(" - Error details:", errorInfo.substring(0, 200));
          console.log(" - Possible reasons:");
          console.log("   1. Email domain may be blocked by ChatGPT");
          console.log("   2. Email already registered");
          console.log("   3. Rate limiting or suspicious activity detected");
          console.log(" - Skipping this email and continuing to next...\n");
          continue; // Skip to next email
        }

        // Wait for OTP email to arrive (ChatGPT sends OTP after email submission)
        console.log(" - Waiting for OTP email to arrive...");
        await delay(8000); // Wait longer for email to arrive
        // --- OTP: try to fetch OTP from dongvanfb.net for this email line ---
        const fetchOtpFromDongvan = async (
          browser,
          emailLine,
          attempts = 3
        ) => {
          for (let attempt = 1; attempt <= attempts; attempt++) {
            console.log(
              `   [OTP] Attempt ${attempt}/${attempts} to fetch OTP from mail reader...`
            );
            const mailPage = await browser.newPage();
            try {
              await mailPage.goto(MAIL_READER_URL, {
                waitUntil: "domcontentloaded",
              });
              await mailPage.waitForSelector(MAIL_TEXTAREA_SELECTOR, {
                timeout: 8000,
              });
              await mailPage.$eval(
                MAIL_TEXTAREA_SELECTOR,
                (el) => (el.value = "")
              );
              await mailPage.type(MAIL_TEXTAREA_SELECTOR, emailLine, {
                delay: 20,
              });
              // click read mailbox
              try {
                await mailPage.waitForSelector(MAIL_READ_BTN, {
                  visible: true,
                  timeout: 5000,
                });
                await mailPage.click(MAIL_READ_BTN);
              } catch (e) {
                console.log("   [OTP] Read button not found or not clickable.");
              }
              // wait for results (backoff)
              await delay(8000 + 5000 * attempt);
              const res = await mailPage.evaluate(
                (validSenders) => {
                  const rows = Array.from(
                    document.querySelectorAll("table tbody tr")
                  );
                  for (const row of rows) {
                    const senderEl =
                      row.querySelector(".readmail_from") ||
                      row.querySelector("[class*='readmail_from']");
                    const codeEl =
                      row.querySelector(".readmail_code") ||
                      row.querySelector("[class*='readmail_code']");
                    const contentEl = row.querySelector(
                      ".content_email_content"
                    );
                    const sender = senderEl
                      ? senderEl.innerText.trim().toLowerCase()
                      : "";
                    const raw = (
                      codeEl
                        ? codeEl.innerText
                        : contentEl
                        ? contentEl.innerText
                        : ""
                    )
                      .replace(/=20/g, "")
                      .replace(/\u00A0/g, " ")
                      .trim();
                    const isValidSender = validSenders.some((s) =>
                      sender.includes(s)
                    );
                    if (!isValidSender) continue;
                    let m = raw.match(/\b\d{6}\b/);
                    if (!m) {
                      const norm = raw.replace(/[^0-9]/g, "");
                      const m2 = norm.match(/(\d{6})/);
                      if (m2) m = m2;
                    }
                    if (m) return { code: m[0], sender };
                  }
                  return null;
                },
                ["noreply@tm.openai.com", "otp@tm1.openai.com", ".openai.com"]
              );
              if (res && res.code) {
                console.log(
                  `   [OTP] Found code ${res.code} from ${res.sender}`
                );
                await mailPage.close();
                return res.code;
              }
            } catch (err) {
              console.log(
                "   [OTP] Error while checking mail reader:",
                err.message || err
              );
            } finally {
              try {
                await mailPage.close();
              } catch (e) {}
            }
            await new Promise((r) => setTimeout(r, 3000));
          }
          return null;
        };

        const otp = await fetchOtpFromDongvan(browser, line, 4);
        if (otp) {
          console.log(" - OTP retrieved:", otp);
          try {
            const codeSelectors = [
              "input[type='tel']",
              "input[type='text'][maxlength='6']",
              "input[aria-label*='code']",
              "input[name*='code']",
              "input[id*='code']",
            ];
            let codeInput = null;
            for (const sel of codeSelectors) {
              try {
                const el = await page.$(sel);
                if (el) {
                  codeInput = el;
                  break;
                }
              } catch (e) {}
            }
            if (codeInput) {
              await codeInput.click({ clickCount: 3 });
              await codeInput.type(otp, { delay: 50 });
              console.log(" - Entered OTP into the page");
              try {
                await page.keyboard.press("Enter");
                console.log(" - Pressed Enter to submit OTP");
              } catch (e) {}

              // Wait for next step after OTP verification
              await delay(3000);

              // Fill profile information from randomData.json
              try {
                const rnd = randomPool.length
                  ? randomPool[Math.floor(Math.random() * randomPool.length)]
                  : null;
                if (rnd) {
                  console.log(" - Filling profile information...");

                  // Try to fill name fields
                  const firstSel = await page.$(
                    "input[name='firstName'], input[id*='first'], input[placeholder*='First'], input[placeholder*='first'], input[placeholder*='name']"
                  );
                  if (firstSel) {
                    await firstSel.click({ clickCount: 3 });
                    await firstSel.type(rnd.firstName, { delay: 20 });
                    console.log(" - Filled first name:", rnd.firstName);
                  }

                  const lastSel = await page.$(
                    "input[name='lastName'], input[id*='last'], input[placeholder*='Last'], input[placeholder*='last']"
                  );
                  if (lastSel) {
                    await lastSel.click({ clickCount: 3 });
                    await lastSel.type(rnd.lastName, { delay: 20 });
                    console.log(" - Filled last name:", rnd.lastName);
                  }

                  // Try to fill password if required
                  const passSel = await page.$("input[type='password']");
                  if (passSel) {
                    await passSel.click({ clickCount: 3 });
                    await passSel.type(defaultPassword, { delay: 30 });
                    console.log(" - Filled password from config");
                  }

                  // Look for and click final submit button
                  await delay(1000);
                  const finalSubmit = await page.evaluate(() => {
                    const buttons = Array.from(
                      document.querySelectorAll("button")
                    );
                    for (const btn of buttons) {
                      const text = (btn.innerText || "").trim().toLowerCase();
                      if (
                        text.includes("continue") ||
                        text.includes("create") ||
                        text.includes("finish") ||
                        text.includes("done")
                      ) {
                        try {
                          btn.click();
                          return true;
                        } catch (e) {}
                      }
                    }
                    return false;
                  });
                  if (finalSubmit) {
                    console.log(" - Clicked final submit button");
                  }

                  await delay(3000);
                  console.log(" - Profile setup completed!");
                }
              } catch (e) {
                console.log(" - Error filling profile:", e.message || e);
              }
            } else {
              console.log(
                " - OTP found but no input selector matched; paste it manually:",
                otp
              );
            }
          } catch (e) {
            console.log(
              " - Failed to enter OTP into chat page:",
              e.message || e
            );
          }
        } else {
          console.log("   [OTP] No OTP found after attempts.");
        }
      }

      console.log(
        `=== Done attempt for ${email}. Close browser to keep profile for reuse.`
      );
    } catch (err) {
      console.error("Error during automation for", email, err.message || err);
    } finally {
      await browser.close();
    }
  }

  console.log("\nAll done.");
})();
