#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT Auto Account Creator - Python Version
Bypass Cloudflare using undetected-chromedriver
"""

import random
from itertools import cycle
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import json
import time
import random
import re
import subprocess
import os
import sys
import pyautogui  # For physical mouse automation
import traceback
from pathlib import Path

index = 0  # Global index variable

def init_profile_iterator(profiles):
    idx = list(range(len(profiles)))
    random.shuffle(idx)
    return cycle(idx)

class ChatGPTAccountCreator:
    def __init__(self, config_path=None):
        """Initialize the account creator with config"""
        self.project_root = Path(__file__).resolve().parents[3]
        self.output_dir = self.project_root / 'data' / 'output' / 'python'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Default to root config/python.config.json
        if config_path is None:
            config_path = self.project_root / 'config' / 'python.config.json'
        else:
            config_path = Path(config_path)
            if not config_path.is_absolute():
                config_path = self.project_root / config_path
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.default_password = self.config.get('defaultPassword', 'ChatgptTest@')
        self.chat_url = self.config.get('chatUrl', 'https://chatgpt.com')
        self.mail_reader_url = self.config.get('mailReaderUrl', 'https://dongvanfb.net/read_mail_box/')
        self.valid_senders = self.config.get('validSenders', [])
        self.otp_attempts = self.config.get('otpAttempts', 4)
        self.delay_between_accounts = self.config.get('delayBetweenAccounts', 5)
        
        # Load emails
        emails_file = self.config.get('emailsFilePath', 'newEmail.txt')
        if not os.path.isabs(emails_file):
            emails_file = self.project_root / emails_file
        with open(emails_file, 'r', encoding='utf-8') as f:
            self.email_lines = [line.strip() for line in f if line.strip()]
        
        # Load random data
        random_data_file = self.config.get('randomDataPath', 'randomData.json')
        if not os.path.isabs(random_data_file):
            random_data_file = self.project_root / random_data_file
        with open(random_data_file, 'r', encoding='utf-8') as f:
            self.random_pool = json.load(f)
        
        self.driver = None
        self.mail_driver = None
    
    def human_delay(self, min_sec=1, max_sec=3):
        """Random delay to simulate human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def human_type(self, element, text, min_delay=0.05, max_delay=0.15):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))
    
    def setup_driver(self, profile_path=None):
        """Setup undetected Chrome driver"""
        options = uc.ChromeOptions()
        
        # Use profile if provided
        if profile_path and os.path.exists(profile_path):
            options.add_argument(f'--user-data-dir={profile_path}')
        
        # Load payment extension
        current_dir = os.path.dirname(os.path.abspath(__file__))
        extension_path = os.path.join(current_dir, 'Extension')
        if os.path.exists(extension_path):
            options.add_argument(f'--load-extension={extension_path}')
        
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Let undetected-chromedriver auto-detect Chrome version
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        })
        
        return driver
    
    def fetch_otp_using_tooljs(self, email_line):
        """Use tool.js (Node.js) to fetch OTP - avoids Cloudflare issues"""
        try:
            tool_js_path = self.project_root / 'apps' / 'node' / 'tool.js'
            
            if not os.path.exists(tool_js_path):
                print(f"   [OTP] tool.js not found at: {tool_js_path}")
                return None
            
            print(f"   [OTP] Running: node tool.js {email_line.split('|')[0]}")
            
            # Run tool.js with Node.js - fix encoding issue
            result = subprocess.run(
                ['node', tool_js_path, email_line],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=60,  # Increase timeout to 60s (tool.js needs ~15s to wait for emails)
                cwd=self.project_root
            )
            
            output = result.stdout.strip()
            
            if result.returncode == 0 or output:  # Success even if returncode != 0
                # tool.js outputs the OTP code - look for patterns
                # Pattern 1: "-> Mã mới nhất: 123456"
                match = re.search(r'Mã mới nhất:\s*(\d{6})', output)
                if match:
                    code = match.group(1)
                    print(f"   [OTP] ✓ Retrieved code: {code}")
                    return code
                
                # Pattern 2: Any 6-digit code
                match = re.search(r'\b(\d{6})\b', output)
                if match:
                    code = match.group(1)
                    print(f"   [OTP] ✓ Retrieved code: {code}")
                    return code
                
                print(f"   [OTP] Output received but no code found")
                print(f"   [OTP] Output preview: {output[:200]}")
            else:
                print(f"   [OTP] tool.js failed: {result.stderr}")
            
            return None
            
        except subprocess.TimeoutExpired:
            print("   [OTP] tool.js timed out after 30s")
            return None
        except FileNotFoundError:
            print("   [OTP] Node.js not found. Install Node.js first.")
            return None
        except Exception as e:
            print(f"   [OTP] Error running tool.js: {e}")
            return None
    
    def fetch_otp_from_mail(self, email_line, attempts=4):
        """Fetch OTP from dongvanfb.net mail reader"""
        print(f"\\n[OTP] Fetching OTP from mail reader...")
        
        for attempt in range(1, attempts + 1):
            print(f"   [OTP] Attempt {attempt}/{attempts}...")
            
            try:
                # Setup separate driver for mail reader if not exists
                if not self.mail_driver:
                    self.mail_driver = self.setup_driver()
                
                self.mail_driver.get(self.mail_reader_url)
                time.sleep(2)
                
                # Find textarea and input email line
                textarea = WebDriverWait(self.mail_driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea.form-control, textarea'))
                )
                textarea.clear()
                textarea.send_keys(email_line)
                
                # Click read mailbox button
                try:
                    btn = self.mail_driver.find_element(By.CSS_SELECTOR, '.btn-buy-home.btn-checked')
                    btn.click()
                except:
                    print("   [OTP] Read button not found")
                
                # Wait for results with backoff
                wait_time = 8 + (5 * attempt)
                print(f"   [OTP] Waiting {wait_time}s for emails...")
                time.sleep(wait_time)
                
                # Search for OTP in table rows
                rows = self.mail_driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
                
                for row in rows:
                    try:
                        # Get sender
                        sender_el = None
                        try:
                            sender_el = row.find_element(By.CSS_SELECTOR, '.readmail_from')
                        except:
                            try:
                                sender_el = row.find_element(By.CSS_SELECTOR, '[class*="readmail_from"]')
                            except:
                                pass
                        
                        if not sender_el:
                            continue
                        
                        sender = sender_el.text.strip().lower()
                        
                        # Check if valid sender
                        is_valid = any(s in sender for s in self.valid_senders)
                        if not is_valid:
                            continue
                        
                        # Get code/content
                        raw_text = ""
                        try:
                            code_el = row.find_element(By.CSS_SELECTOR, '.readmail_code')
                            raw_text = code_el.text
                        except:
                            try:
                                content_el = row.find_element(By.CSS_SELECTOR, '.content_email_content')
                                raw_text = content_el.text
                            except:
                                pass
                        
                        # Clean text and search for 6-digit code
                        raw_text = raw_text.replace('=20', '').replace('\\xa0', ' ').strip()
                        
                        # Try strict match
                        match = re.search(r'\\b\\d{6}\\b', raw_text)
                        if not match:
                            # Try extracting digits
                            digits_only = re.sub(r'[^0-9]', '', raw_text)
                            match = re.search(r'(\\d{6})', digits_only)
                        
                        if match:
                            code = match.group(0)
                            print(f"   [OTP] ✓ Found code: {code} from {sender}")
                            return code
                    
                    except Exception as e:
                        continue
                
            except Exception as e:
                print(f"   [OTP] Error: {e}")
            
            time.sleep(3)
        
        print("   [OTP] ✗ No OTP found after all attempts")
        return None
    
    def detect_current_page(self):
        """Detect which page we're currently on"""
        current_url = self.driver.current_url.lower()
        
        # Check URL patterns first (most reliable)
        # ONLY detect dashboard if URL has /c/ (actual conversation page)
        if 'chatgpt.com' in current_url and '/c/' in current_url:
            return 'dashboard'
        elif 'email-verification' in current_url or 'verify' in current_url:
            return 'otp'
        elif 'accounts.google.com' in current_url or 'login.microsoftonline.com' in current_url:
            return 'oauth_error'
        elif '/error' in current_url:
            return 'error'
        
        # Check page content (order matters!)
        try:
            # Check for chatgpt.com homepage WITH chat interface (logged in successfully)
            if 'chatgpt.com' in current_url:
                # Look for email input first - if present, it's login page
                login_elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')
                if login_elements:
                    return 'login'
                
                # No email input - check for logged-in dashboard elements
                # Look for sidebar, navigation, or chat interface
                dashboard_selectors = [
                    'textarea[placeholder*="Message" i]',
                    'div.flex-col.flex-1',  # Main layout
                    'div.relative.flex.h-full',  # Sidebar container
                    'nav',
                    'button[aria-label*="New chat" i]',
                    'div[class*="sidebar"]'
                ]
                
                for selector in dashboard_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            return 'dashboard'
                    except:
                        continue
            
            # Check for email input field (login/signup page)
            if self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]'):
                return 'login'
            
            # Check for profile setup page
            if self.driver.find_elements(By.CSS_SELECTOR, 'input[name="name"], input[placeholder*="full name" i]'):
                return 'profile'
            
            # Check for OTP input
            if self.driver.find_elements(By.CSS_SELECTOR, 'input[type="tel"], input[maxlength="6"]'):
                return 'otp'
            
            # Check for landing page (has "Log in" or "Sign up" buttons)
            # This should match the chatgpt.com homepage
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            buttons.extend(self.driver.find_elements(By.TAG_NAME, 'a'))
            
            for btn in buttons:
                text = btn.text.strip().lower()
                if 'log in' in text or 'sign up' in text or text == 'login' or text == 'signup':
                    return 'landing'
        except:
            pass
        
        return 'unknown'
    
    def handle_already_logged_in(self):
        """Handle case when already logged in"""
        print(" - ✓ Already logged in to ChatGPT!")
        print("\n→ Account ready, starting Business plan upgrade...")
        
        # Proceed to upgrade Business plan
        if self.upgrade_to_business_plan():
            return True
        else:
            print("\n⚠️  Business plan upgrade failed")
            return True  # Still return True since login was successful
    
    def handle_profile_page(self, profile_data):
        """Handle profile setup page"""
        print(" - On profile setup page, filling information...")
        
        self.human_delay(1, 2)
        
        # Fill full name
        try:
            name_input = self.driver.find_element(By.CSS_SELECTOR, 
                'input[name="name"], input[placeholder*="full name" i], input[placeholder*="name" i]')
            name_input.clear()
            first_name = profile_data.get('firstName', 'User')
            last_name = profile_data.get('lastName', 'Name')
            full_name = f"{first_name} {last_name}"
            name_input.send_keys(full_name)
            print(f"   ✓ Full name: {full_name}")
            self.human_delay(0.5, 1)
        except Exception as e:
            print(f"   - Could not fill name: {e}")
        
        # Fill birthday
        if 'dob' in profile_data and profile_data['dob']:
            self.fill_birthday(profile_data['dob'])
        
        self.human_delay(1, 2)
        
        # Check agreement checkbox
        print(" - Looking for agreement checkbox...")
        try:
            checkbox_selectors = [
                'input[type="checkbox"]',
                'label:has(input[type="checkbox"])',
                'input[name*="consent" i]',
                'input[id*="checkbox" i]'
            ]
            
            for selector in checkbox_selectors:
                try:
                    checkbox = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if checkbox.get_attribute('type') == 'checkbox':
                        if not checkbox.is_selected():
                            checkbox.click()
                        print("   ✓ Checked agreement checkbox")
                        break
                except:
                    continue
        except Exception as e:
            print(f"   - Could not find checkbox: {e}")
        
        self.human_delay(1, 2)
        
        # Click Continue
        print(" - Looking for Continue button...")
        return self.click_continue_button()
    
    def fill_birthday(self, dob_string):
        """Fill birthday field - separated for reuse"""
        try:
            dob_parts = dob_string.split('-')
            if len(dob_parts) == 3:
                year, month, day = dob_parts
                
                print(f" - Filling birthday: {month}/{day}/{year}")
                
                js_find_container = """
                // Approach 1: Find hidden input and click its parent container
                var hiddenInput = document.querySelector('input[name="birthday"]');
                if (hiddenInput) {
                    var container = hiddenInput.closest('[role="group"]');
                    if (!container) {
                        container = hiddenInput.parentElement;
                    }
                    if (container) {
                        var clickableDiv = container.querySelector('div[role="presentation"], div[contenteditable], div:not([hidden])');
                        if (clickableDiv) {
                            clickableDiv.scrollIntoView({block: 'center'});
                            clickableDiv.click();
                            return 'method1-clickableDiv';
                        }
                        container.scrollIntoView({block: 'center'});
                        container.click();
                        return 'method1-container';
                    }
                }
                
                // Approach 2: Find any div that looks like a date input
                var allDivs = document.querySelectorAll('div');
                for (var i = 0; i < allDivs.length; i++) {
                    if (allDivs[i].textContent.includes('MM') || allDivs[i].textContent.includes('DD') || allDivs[i].textContent.includes('YYYY')) {
                        allDivs[i].scrollIntoView({block: 'center'});
                        allDivs[i].click();
                        return 'method2-textSearch';
                    }
                }
                
                return false;
                """
                
                found = self.driver.execute_script(js_find_container)
                if not found:
                    print(f"   ✗ Birthday field not found")
                else:
                    time.sleep(1.5)
                    
                    from selenium.webdriver.common.keys import Keys
                    active_element = self.driver.switch_to.active_element
                    
                    # Month
                    for digit in month:
                        active_element.send_keys(digit)
                        time.sleep(random.uniform(0.12, 0.2))
                    
                    active_element.send_keys(Keys.TAB)
                    time.sleep(0.3)
                    
                    # Day
                    active_element = self.driver.switch_to.active_element
                    for digit in day:
                        active_element.send_keys(digit)
                        time.sleep(random.uniform(0.12, 0.2))
                    
                    active_element.send_keys(Keys.TAB)
                    time.sleep(0.3)
                    
                    # Year
                    active_element = self.driver.switch_to.active_element
                    for digit in year:
                        active_element.send_keys(digit)
                        time.sleep(random.uniform(0.12, 0.2))
                    
                    print(f"   ✓ Birthday entered: {month}/{day}/{year}")
                    time.sleep(0.5)
                
                self.human_delay(1, 2)
                
        except Exception as e:
            print(f"   - Error filling birthday: {e}")
    
    def click_continue_button(self):
        """Find and click Continue button - separated for reuse"""
        continue_selectors = [
            'button:has-text("Continue")',
            'button[type="submit"]',
            'button.continue-btn',
            'button[aria-label*="continue" i]',
            '//button[contains(translate(text(), "CONTINUE", "continue"), "continue")]'
        ]
        
        for selector in continue_selectors:
            try:
                if selector.startswith('//'):
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                if btn:
                    self.human_delay(0.5, 1)
                    btn.click()
                    print(" - ✓ Clicked Continue button")
                    return True
            except:
                continue
        
        print(" - ✗ Continue button not found")
        return False
    

    def fill_payment_form(self):
        """Fill payment form using JavaScript - integrated directly"""
        try:
            print("\n" + "="*60)
            time.sleep(5)
            print("FILLING PAYMENT FORM")
            print("="*60)
            
            # Load payment data
            current_dir = os.path.dirname(os.path.abspath(__file__))
            payment_data_path = os.path.join(current_dir, 'Extension', 'payment_data.json')
            
            with open(payment_data_path, 'r', encoding='utf-8') as f:
                payment_data = json.load(f)

            payment_data["profile_iter"] = init_profile_iterator(payment_data["profiles"])
            
            index = next(payment_data["profile_iter"])
            profile = payment_data["profiles"][index]

            with open(self.output_dir / "DoingProfile.txt", "a", encoding="utf-8") as pf:
                pf.write(f"{profile['name']} + {profile['payment']}\n")
                pf.flush()

            email = self.current_email
            
            print(f" - Using profile: {profile['name']}")
            print(f" - Email: {email}")
            
            # JavaScript to fill form (using exact selectors from HTML analysis)
            fill_script = f"""
            (async function() {{
                console.log("🚀 Starting payment form fill...");
                
                // Helper: Set native value for React/Stripe compatibility
                function setNativeValue(element, value) {{
                    if (!element || !value) return false;
                    
                    try {{
                        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value')?.set;
                        const prototype = Object.getPrototypeOf(element);
                        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;

                        if (valueSetter && valueSetter !== prototypeValueSetter) {{
                            prototypeValueSetter.call(element, value);
                        }} else if (valueSetter) {{
                            valueSetter.call(element, value);
                        }}
                        
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        return true;
                    }} catch (e) {{
                        console.warn("Error setting value:", e);
                        return false;
                    }}
                }}
                
                // Helper: Fill input
                function fillInput(selector, value) {{
                    const input = document.querySelector(selector);
                    if (input && value) {{
                        input.focus();
                        if (setNativeValue(input, value)) {{
                            console.log("✅ Filled:", selector);
                            return true;
                        }}
                    }}
                    return false;
                }}
                
                // Helper: Select dropdown
                function selectOption(selector, value) {{
                    const select = document.querySelector(selector);
                    if (select && value) {{
                        select.value = value;
                        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        console.log("✅ Selected:", selector);
                        return true;
                    }}
                    return false;
                }}
                
                // Wait for page ready
                await new Promise(r => setTimeout(r, 1500));
                
                // Fill Email
                fillInput('input#email', '{email}');
                await new Promise(r => setTimeout(r, 800));
                
                // Fill Card Info (may be blocked by Stripe iframe)
                const cardFilled = fillInput('input#cardNumber', '{profile['payment']['cardNumber']}');
                await new Promise(r => setTimeout(r, 600));
                const expiryFilled = fillInput('input#cardExpiry', '{profile['payment']['expireMonth']} / {profile['payment']['expireYear'][-2:]}');
                await new Promise(r => setTimeout(r, 600));
                const cvvFilled = fillInput('input#cardCvc', '{profile['payment']['cvv']}');
                await new Promise(r => setTimeout(r, 800));
                
                if (!cardFilled || !expiryFilled || !cvvFilled) {{
                    console.warn('⚠️ Card fields may be blocked by Stripe iframe!');
                    console.warn('Card:', cardFilled, 'Expiry:', expiryFilled, 'CVV:', cvvFilled);
                }}
                
                // Fill Cardholder Name
                fillInput('input#billingName', '{profile['contact']['fullName']}');
                await new Promise(r => setTimeout(r, 800));
                
                // Select Country
                selectOption('select#billingCountry', '{profile['billing']['countryCode']}');
                await new Promise(r => setTimeout(r, 1200));
                
                // Select Province (서울특별시)
                selectOption('select#billingAdministrativeArea', '서울특별시');
                await new Promise(r => setTimeout(r, 800));
                
                // Fill Address
                fillInput('input#billingAddressLine1', '{profile['billing']['street']}');
                await new Promise(r => setTimeout(r, 500));
                fillInput('input#billingLocality', '{profile['billing']['city']}');
                await new Promise(r => setTimeout(r, 500));
                fillInput('input#billingDependentLocality', '{profile['billing']['district']}');
                await new Promise(r => setTimeout(r, 500));
                fillInput('input#billingPostalCode', '{profile['billing']['postalCode']}');
                await new Promise(r => setTimeout(r, 1000));
                
                // Check Terms of Service (required)
                const termsCheckbox = document.querySelector('input#termsOfServiceConsentCheckbox');
                if (termsCheckbox && !termsCheckbox.checked) {{
                    termsCheckbox.click();
                    console.log("✅ Terms checkbox checked");
                }}
                
                await new Promise(r => setTimeout(r, 500));
                
                console.log("✅ Payment form filled!");
                return true;
            }})();
            """
            
            # Execute the script
            result = self.driver.execute_script(fill_script)
            print(" - ✓ Payment form filled successfully")
            
            # Wait longer for Stripe to validate all fields and enable button
            print(" - Waiting 12s for Stripe to validate form...")
            time.sleep(12)
            
            # Click Subscribe button with exact selector from HTML
            print(" - Looking for Subscribe button...")
            submit_clicked = False
            
            # Try with element_to_be_clickable (correct approach)
            try:
                print(" - Waiting for Subscribe button to be clickable...")
                submit_btn = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="hosted-payment-submit-button"]'))
                )
                
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                time.sleep(1)
                
                # Click using JavaScript for reliability
                self.driver.execute_script("arguments[0].click();", submit_btn)
                print(" - ✓ Clicked Subscribe button")
                submit_clicked = True
                
            except Exception as e:
                print(f" - ✗ Failed with primary selector: {e}")
                
                # Fallback: Try finding by text
                try:
                    print(" - Trying fallback: finding button by text...")
                    submit_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Subscribe")]'))
                    )
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    print(" - ✓ Clicked Subscribe button (fallback)")
                    submit_clicked = True
                except Exception as e2:
                    print(f" - ✗ Fallback also failed: {e2}")
            
            if not submit_clicked:
                print(" - ✗ Subscribe button not found after all attempts")
                # Debug: print all buttons on page
                try:
                    print(" - Debug: Looking for all buttons on page...")
                    all_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                    print(f" - Found {len(all_buttons)} buttons:")
                    for i, btn in enumerate(all_buttons[:15]):
                        try:
                            text = btn.text.strip()
                            btn_type = btn.get_attribute('type')
                            btn_class = btn.get_attribute('class')
                            data_testid = btn.get_attribute('data-testid')
                            if text or data_testid:
                                print(f"   [{i+1}] Text: '{text}', Type: {btn_type}, Class: {btn_class}, TestID: {data_testid}")
                        except:
                            pass
                except:
                    pass
                return False
            
            # Wait longer for hCaptcha verification challenge to appear
            print(" - Waiting 10s for verification challenge...")
            time.sleep(10)
            
            # Look for "I am human" checkbox
            print(" - Looking for 'I am human' verification checkbox...")
            verification_found = False
            
            # Strategy 1: Look for the modal first, then checkbox inside
            try:
                # Wait for modal with "One more step" text
                modal = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "One more step")]'))
                )
                print(" - ✓ Found verification modal")
                time.sleep(2)
                
                # Now find checkbox - try multiple approaches
                checkbox_selectors = [
                    '//input[@type="checkbox"]',
                    '//div[@role="checkbox"]',
                    '//*[contains(text(), "I am human")]//preceding::input[@type="checkbox"][1]',
                    '//*[contains(text(), "I am human")]//following::input[@type="checkbox"][1]',
                    '//*[contains(text(), "I am human")]/ancestor::div//input[@type="checkbox"]'
                ]
                
                for selector in checkbox_selectors:
                    try:
                        checkbox = self.driver.find_element(By.XPATH, selector)
                        if checkbox and not checkbox.is_selected():
                            # Try multiple click methods
                            try:
                                # Method 1: JavaScript click
                                self.driver.execute_script("arguments[0].click();", checkbox)
                                print(f" - ✓ Clicked checkbox with JavaScript (selector: {selector})")
                                verification_found = True
                                break
                            except:
                                try:
                                    # Method 2: Regular click
                                    checkbox.click()
                                    print(f" - ✓ Clicked checkbox normally (selector: {selector})")
                                    verification_found = True
                                    break
                                except:
                                    continue
                    except:
                        continue
                        
            except Exception as e:
                print(f" - Modal not found: {e}")
            
            # Strategy 2: Look in hCaptcha iframe - NESTED IFRAME SUPPORT
            if not verification_found:
                try:
                    print(" - 🕵️ Searching for hCaptcha iframe with nested iframe support...")
                    
                    # Step 1: Find outer iframe with hcaptcha-inner in src
                    iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                    print(f" - Found {len(iframes)} total iframes on main page")
                    
                    outer_iframe = None
                    for idx, iframe in enumerate(iframes):
                        try:
                            src = iframe.get_attribute('src') or ''
                            size = iframe.size
                            
                            # Must have hcaptcha-inner AND be visible (> 100x100)
                            if 'hcaptcha-inner' in src.lower() and size['width'] > 100 and size['height'] > 100:
                                outer_iframe = iframe
                                print(f" - ✓ Found outer iframe #{idx}: {size['width']}x{size['height']}")
                                print(f" - Outer iframe src: {src[:100]}")
                                break
                        except:
                            continue
                    
                    if not outer_iframe:
                        print(" - ✗ No visible hCaptcha outer iframe found")
                    else:
                        # Step 2: Switch into outer iframe
                        print(" - ✓ Switching into outer iframe...")
                        self.driver.switch_to.frame(outer_iframe)
                        time.sleep(2)
                        
                        # Step 3: Look for NESTED iframe inside (HCaptcha.html)
                        print(" - 🔍 Looking for nested iframe inside...")
                        nested_iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                        print(f" - Found {len(nested_iframes)} nested iframe(s)")
                        
                        inner_iframe = None
                        for idx, iframe in enumerate(nested_iframes):
                            try:
                                src = iframe.get_attribute('src') or ''
                                if 'hcaptcha.html' in src.lower() or 'b.stripecdn.com' in src.lower():
                                    inner_iframe = iframe
                                    print(f" - ✓ Found inner iframe #{idx}")
                                    print(f" - Inner iframe src: {src[:100]}")
                                    break
                            except:
                                continue
                        
                        if not inner_iframe:
                            print(" - ⚠️ No nested iframe found, trying to click in outer iframe...")
                        else:
                            # Step 4: Switch into NESTED iframe
                            print(" - ✓ Switching into nested iframe...")
                            self.driver.switch_to.frame(inner_iframe)
                            time.sleep(3)
                        
                        # Debug: Log current iframe HTML
                        try:
                            iframe_html = self.driver.execute_script("return document.body.innerHTML;")
                            print(f" - Current iframe HTML length: {len(iframe_html)} chars")
                            if len(iframe_html) > 0:
                                print(f" - HTML preview: {iframe_html[:250]}")
                        except:
                            pass
                        
                        # Step 5: Try to find checkbox element with JavaScript
                        checkbox_selectors = [
                            "#checkbox",
                            "div[id='checkbox']",
                            ".ctp-checkbox-label",
                            "label",
                            "#anchor",
                            "div.check",
                            "[role='checkbox']"
                        ]
                        
                        checkbox_found = False
                        for selector in checkbox_selectors:
                            try:
                                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if element.is_displayed():
                                    print(f" - ✓ Found checkbox with selector: {selector}")
                                    # Scroll into view
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(0.5)
                                    # Click
                                    self.driver.execute_script("arguments[0].click();", element)
                                    print(" - ✓ Clicked checkbox with JavaScript")
                                    checkbox_found = True
                                    verification_found = True
                                    time.sleep(2)
                                    break
                            except:
                                continue
                        
                        # Step 6: If no element found, try PHYSICAL MOUSE CLICK (PyAutoGUI)
                        if not checkbox_found:
                            print(" - ⚠️ No checkbox element found, trying PHYSICAL mouse click...")
                            try:
                                # Switch back to main content to get iframe position on screen
                                self.driver.switch_to.default_content()
                                time.sleep(0.5)
                                
                                # Find outer iframe again
                                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                                for iframe in iframes:
                                    src = iframe.get_attribute('src') or ''
                                    if 'hcaptcha-inner' in src.lower():
                                        # Get iframe position and size
                                        iframe_rect = iframe.rect
                                        iframe_x = iframe_rect['x']
                                        iframe_y = iframe_rect['y']
                                        iframe_width = iframe_rect['width']
                                        iframe_height = iframe_rect['height']
                                        
                                        print(f" - Iframe position: ({iframe_x}, {iframe_y})")
                                        print(f" - Iframe size: {iframe_width}x{iframe_height}")
                                        
                                        # Calculate checkbox position on screen
                                        # hCaptcha checkbox is usually at center-left of widget
                                        # Adjusted: +50px right, +50px down from original position
                                        checkbox_screen_x = int(iframe_x + (iframe_width / 2) - 120 + 380)
                                        checkbox_screen_y = int(iframe_y + (iframe_height / 2) + 250)
                                        
                                        print(f" - 🖱️  Physical click at screen position: ({checkbox_screen_x}, {checkbox_screen_y})")
                                        
                                        # Move mouse slowly (human-like) and click
                                        pyautogui.moveTo(checkbox_screen_x, checkbox_screen_y, duration=0.5)
                                        time.sleep(0.3)
                                        
                                        # Click 3 times with small delays
                                        for i in range(3):
                                            pyautogui.click()
                                            print(f" - ✓ Physical click #{i+1}")
                                            time.sleep(0.2)
                                        
                                        print(" - ✓ Physical mouse click executed!")
                                        verification_found = True
                                        checkbox_found = True
                                        break
                                
                                if not checkbox_found:
                                    print(" - ✗ Could not find iframe for physical click")
                                    
                            except Exception as e:
                                print(f" - Physical click failed: {str(e)[:100]}")
                                traceback.print_exc()
                            
                            # Always switch back to main content
                            try:
                                self.driver.switch_to.default_content()
                            except:
                                pass
                        
                        # Step 7: Switch back to main content (exit all iframes)
                        self.driver.switch_to.default_content()
                        print(" - ✓ Switched back to main content")
                        
                        if verification_found:
                            print(" - ✓ Verification checkbox clicked, waiting for response...")
                            time.sleep(3)
                
                except Exception as e:
                    print(f" - Error in iframe handling: {str(e)[:100]}")
                    # Always switch back even on error
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
            
            # Strategy 3: Simple checkbox search on main page
            if not verification_found:
                try:
                    checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                    print(f" - Found {len(checkboxes)} checkboxes on page")
                    
                    for idx, cb in enumerate(checkboxes):
                        try:
                            if cb.is_selected() or not cb.is_displayed():
                                continue
                            
                            # Try to click
                            self.driver.execute_script("arguments[0].click();", cb)
                            print(f" - ✓ Clicked checkbox #{idx}")
                            verification_found = True
                            break
                        except:
                            continue
                except:
                    pass
            
            if not verification_found:
                print(" - ⚠️  Could not find or click verification checkbox")
                print(" - ⚠️  MANUAL ACTION REQUIRED: Please click the 'I am human' checkbox in the browser")
                print(" - Waiting 30s for manual verification...")
                time.sleep(30)  # Give user time to manually click
            else:
                # Wait for automated verification processing
                print(" - Waiting for payment processing...")
                time.sleep(10)  # Initial wait for processing to start
            
            # Check payment status
            print(" - Checking payment status...")
            payment_success = False
            max_checks = 6  # Check for up to 60 seconds (6 x 10s)
            
            for check_attempt in range(max_checks):
                try:
                    current_url = self.driver.current_url.lower()
                    print(f" - Payment check {check_attempt + 1}/{max_checks}: {current_url[:80]}")
                    
                    # Success indicators
                    # 1. Redirected to dashboard/team page
                    if 'chatgpt.com/g/' in current_url or '/team/' in current_url or (current_url == 'https://chatgpt.com/' or current_url == 'https://chatgpt.com'):
                        print(" - ✓ Redirected to ChatGPT dashboard - Payment likely successful!")
                        payment_success = True
                        break
                    
                    # 2. Check for success message on page
                    try:
                        success_indicators = [
                            '//*[contains(text(), "successfully")]',
                            '//*[contains(text(), "Success")]',
                            '//*[contains(text(), "complete")]',
                            '//*[contains(text(), "Thank you")]',
                            '//*[contains(text(), "Welcome to")]'
                        ]
                        for indicator in success_indicators:
                            if self.driver.find_elements(By.XPATH, indicator):
                                print(" - ✓ Found success message - Payment successful!")
                                payment_success = True
                                break
                        if payment_success:
                            break
                    except:
                        pass
                    
                    # 3. Check for error messages
                    try:
                        error_indicators = [
                            '//*[contains(text(), "declined")]',
                            '//*[contains(text(), "failed")]',
                            '//*[contains(text(), "error")]',
                            '//*[contains(text(), "invalid")]',
                            '//*[contains(text(), "unable to process")]'
                        ]
                        for indicator in error_indicators:
                            if self.driver.find_elements(By.XPATH, indicator):
                                print(" - ✗ Found error message - Payment failed!")
                                print(" - ✗ Payment processing failed")
                                return False
                    except:
                        pass
                    
                    # Still on payment page, wait and check again
                    if check_attempt < max_checks - 1:
                        print(" - Still processing, waiting 10s...")
                        time.sleep(10)
                    
                except Exception as e:
                    print(f" - Error checking payment status: {str(e)[:100]}")
                    if check_attempt < max_checks - 1:
                        time.sleep(10)
            
            if not payment_success:
                print(" - ⚠️  Could not confirm payment success after 60s")
                print(" - ⚠️  Manual verification recommended")
            
            # Try to close "Save card?" modal if it appears
            try:
                print(" - Looking for 'No thanks' button...")
                no_thanks_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "No thanks")]'))
                )
                no_thanks_btn.click()
                print(" - ✓ Clicked 'No thanks' button")
                time.sleep(2)
            except:
                print(" - 'No thanks' button not found (may not appear)")
            
            if payment_success:
                print(" - ✓ Payment confirmed successful!")
                return True
            else:
                print(" - ⚠️  Payment status unclear, may need manual check")
                return True  # Return True to continue, but with warning
            
        except Exception as e:
            print(f" - ✗ Error filling payment form: {{e}}")
            import traceback
            traceback.print_exc()
            return False
    
    def upgrade_to_business_plan(self):

        print("Đã bỏ qua phần nâng cấp lên Business plan để tập trung vào flow tạo tài khoản và thanh toán. Phần nâng cấp sẽ được hoàn thiện sau khi đảm bảo flow chính hoạt động ổn định.")

        return True  # TEMPORARY: Skip upgrade for now, focus on account creation and payment flow
    
        """Upgrade account to Business plan with 1 month free trial"""
        try:
            print("\n" + "="*60)
            print("UPGRADING TO BUSINESS PLAN")
            print("="*60)
            
            # Navigate directly to promo URL (don't open new tab)
            promo_url = "https://chatgpt.com/?promo_campaign=team-1-month-free&utm_campaign=WEB-team-1-month-free&utm_internal_medium=referral&utm_internal_source=openai_business#pricing"
            print(f" - Navigating to promo page...")
            self.driver.get(promo_url)
            print(f" - Current URL: {self.driver.current_url}")
            self.human_delay(5, 7)
            
            # Step 1: Navigate 2 times, then reload 1 time before checking Business toggle
            print(" - Preparing to load pricing page...")
            
            # Navigate twice
            for i in range(2):
                print(f" - Navigation attempt {i + 1}/2...")
                self.driver.get(promo_url)
                time.sleep(4)
                print(f" - Current URL: {self.driver.current_url}")
            
            # Then reload once
            print(" - Reloading page...")
            self.driver.refresh()
            time.sleep(4)
            print(f" - Current URL after reload: {self.driver.current_url}")
            
            # Remove overlays
            print(" - Removing overlays...")
            try:
                self.driver.execute_script("""
                    // Remove fixed overlays with high z-index
                    const overlays = document.querySelectorAll('[data-state="open"].fixed, .fixed.inset-0, [role="dialog"]');
                    overlays.forEach(el => {
                        const zIndex = window.getComputedStyle(el).zIndex;
                        if (zIndex && parseInt(zIndex) > 40) {
                            el.style.display = 'none';
                            el.remove();
                        }
                    });
                    
                    // Remove backdrop elements
                    const backdrops = document.querySelectorAll('.backdrop-blur, [class*="backdrop"]');
                    backdrops.forEach(el => {
                        el.style.display = 'none';
                        el.remove();
                    });
                    
                    // Remove pointer-events blocking elements
                    document.querySelectorAll('[style*="pointer-events"]').forEach(el => {
                        if (el.style.pointerEvents === 'auto' || el.style.pointerEvents === 'all') {
                            const zIndex = window.getComputedStyle(el).zIndex;
                            if (zIndex && parseInt(zIndex) > 40) {
                                el.style.display = 'none';
                            }
                        }
                    });
                """)
                print(" - ✓ Removed overlay elements")
            except Exception as e:
                print(f" - Overlay cleanup warning: {str(e)[:100]}")
            
            # Reload page after removing overlay to fix page state
            print(" - Reloading page after removing overlay...")
            self.driver.refresh()
            time.sleep(4)
            print(f" - Current URL after final reload: {self.driver.current_url}")
            
            # Step 2: Toggle to Business mode
            print(" - Looking for Business toggle...")
            try:
                # Find the Business toggle button
                toggle_selectors = [
                    'button[aria-label*="Business" i]',
                    'button[role="radio"][aria-label*="Business" i]',
                    '//button[contains(@aria-label, "Business")]',
                    '//button[contains(text(), "Business")]'
                ]
                
                business_toggle = None
                for selector in toggle_selectors:
                    try:
                        if selector.startswith('//'):
                            business_toggle = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            business_toggle = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        
                        if business_toggle:
                            break
                    except:
                        continue
                
                if business_toggle:
                    # Check if already selected
                    is_checked = business_toggle.get_attribute('aria-checked')
                    if is_checked != 'true':
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", business_toggle)
                        time.sleep(0.5)
                        
                        # Try normal click first
                        try:
                            business_toggle.click()
                            print(" - ✓ Toggled to Business mode (normal click)")
                        except Exception as click_error:
                            # If normal click fails, use JavaScript
                            print(f" - Normal click failed, trying JavaScript...")
                            self.driver.execute_script("arguments[0].click();", business_toggle)
                            print(" - ✓ Toggled to Business mode (JavaScript click)")
                        
                        self.human_delay(2, 3)
                    else:
                        print(" - ✓ Already in Business mode")
                else:
                    print(" - ✗ Business toggle not found")
                    return False
            except Exception as e:
                print(f" - Error toggling Business mode: {e}")
                return False
            
            # Step 2: Click "Claim free offer" button
            print(" - Looking for Claim free offer button...")
            try:
                claim_selectors = [
                    'button[data-testid="select-plan-button-teams-create"]',
                    'button.btn-purple.btn-large',
                    '//button[@data-testid="select-plan-button-teams-create"]',
                    '//button[contains(text(), "claim free offer")]',
                    '//button[contains(text(), "Claim free offer")]'
                ]
                
                claim_button = None
                for selector in claim_selectors:
                    try:
                        if selector.startswith('//'):
                            claim_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            claim_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        
                        if claim_button:
                            print(f" - Found button with selector: {selector}")
                            break
                    except:
                        continue
                
                if claim_button:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", claim_button)
                    time.sleep(0.5)
                    
                    # Try normal click first, fallback to JavaScript
                    try:
                        claim_button.click()
                        print(" - ✓ Clicked Claim free offer (normal click)")
                    except Exception as click_error:
                        print(f" - Normal click failed, trying JavaScript...")
                        self.driver.execute_script("arguments[0].click();", claim_button)
                        print(" - ✓ Clicked Claim free offer (JavaScript click)")
                    
                    self.human_delay(3, 5)
                else:
                    print(" - ✗ Claim free offer button not found")
                    return False
            except Exception as e:
                print(f" - Error clicking Claim free offer: {e}")
                return False
            
            # Step 3: Continue through the process (single attempt)
            print(" - Checking for Continue button...")
            try:
                if self.click_continue_button():
                    print(" - ✓ Clicked Continue, waiting...")
                    self.human_delay(3, 5)
                else:
                    # No continue button found, might be at billing step already
                    print(" - No Continue button, proceeding to billing...")
            except:
                pass
            
            # Wait before looking for billing button
            self.human_delay(2, 3)
            
            # Step 4: Click "Continue to billing"
            print(" - Looking for Continue to billing button...")
            try:
                billing_selectors = [
                    'button.btn.relative.btn-green.mt-8.w-full.rounded-xl',
                    'button.btn-green.rounded-xl',
                    'button.btn-green',
                    'button.btn.btn-green',
                    '//button[contains(., "Continue to billing")]',
                    '//button[contains(., "continue to billing")]',
                    '//button[contains(text(), "Continue to billing")]',
                    '//button[contains(text(), "continue to billing")]',
                    '//a[contains(text(), "Continue to billing")]'
                ]
                
                billing_button = None
                for selector in billing_selectors:
                    try:
                        if selector.startswith('//'):
                            billing_button = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            billing_button = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        
                        if billing_button:
                            print(f" - Found button with selector: {selector}")
                            break
                    except:
                        continue
                
                if billing_button:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", billing_button)
                    time.sleep(0.5)
                    billing_button.click()
                    print(" - ✓ Clicked Continue to billing")
                    self.human_delay(5, 7)
                    
                    print("\n✓ Reached payment page!")
                    
                    # Fill payment form directly with JavaScript
                    if self.fill_payment_form():
                        print("✅ Payment form filled and submitted!")
                        return True
                    else:
                        print("⚠️  Payment form filling had issues")
                        return False
                else:
                    print(" - ✗ Continue to billing button not found")
                    # Print current URL for debugging
                    print(f" - Current URL: {self.driver.current_url}")
                    # Try to find all buttons on page
                    try:
                        buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                        print(f" - Found {len(buttons)} buttons on page:")
                        for i, btn in enumerate(buttons[:10]):  # Show first 10
                            try:
                                text = btn.text.strip()
                                classes = btn.get_attribute('class')
                                if text:
                                    print(f"   Button {i+1}: '{text}' (class: {classes})")
                            except:
                                pass
                    except:
                        pass
                    return False
            except Exception as e:
                print(f" - Error clicking Continue to billing: {e}")
                return False
                
        except Exception as e:
            print(f"\n✗ Error upgrading to Business plan: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_account(self, email_line):
        """Create one ChatGPT account - adaptive flow based on current page state"""
        email = email_line.split('|')[0]
        # Store email for later use in payment form
        self.current_email = email
        # Always use password from config for ChatGPT account
        password = self.default_password
        
        # Track if this is first visit to chatgpt.com in this profile
        self.first_chatgpt_visit = True
        
        print(f"\\n{'='*60}")
        print(f"Creating account for: {email}")
        print(f"{'='*60}")
        
        try:
            # Navigate to ChatGPT homepage
            print(f" - Navigating to {self.chat_url}")
            self.driver.get(self.chat_url)
            self.human_delay(3, 5)
            
            # State machine: adapt to current page
            max_iterations = 15  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                current_page = self.detect_current_page()
                current_url = self.driver.current_url.lower()
                print(f" - Current page detected: {current_page}")
                
                # CRITICAL: First visit MUST login, non-first visit MUST upgrade
                if self.first_chatgpt_visit:
                    # FIRST VISIT - Must go through login flow
                    # Ignore dashboard/unknown detection (false positives on fresh profile)
                    if current_page in ['landing', 'dashboard', 'unknown']:
                        # Look for and click login button
                        print(" - First visit: looking for Log in button...")
                        try:
                            # Wait for any overlays to disappear
                            time.sleep(2)
                            
                            # Try to close any modals/overlays first
                            try:
                                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                                    'button[aria-label*="close" i], button[aria-label*="dismiss" i], [role="dialog"] button')
                                for close_btn in close_buttons:
                                    try:
                                        close_btn.click()
                                        time.sleep(0.5)
                                    except:
                                        pass
                            except:
                                pass
                            
                            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                            buttons.extend(self.driver.find_elements(By.TAG_NAME, 'a'))
                            
                            login_btn = None
                            for btn in buttons:
                                text = btn.text.strip().lower()
                                if 'log in' in text or text == 'login':
                                    login_btn = btn
                                    break
                            
                            if login_btn:
                                # Try JavaScript click to bypass overlay
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
                                    time.sleep(0.5)
                                    self.driver.execute_script("arguments[0].click();", login_btn)
                                    print(" - ✓ Clicked Log in button")
                                except:
                                    # Fallback to regular click
                                    login_btn.click()
                                    print(" - ✓ Clicked Log in button")
                                
                                # Wait longer for page transition
                                self.human_delay(5, 7)
                                continue
                            else:
                                print(" - ✗ Log in button not found, will try email input")
                                # Continue to try handle_login_flow
                        except Exception as e:
                            print(f" - Error looking for Log in button: {e}")
                    
                    # Handle login page - enter email/password/OTP
                    if current_page in ['login', 'signup', 'unknown', 'landing', 'dashboard']:
                        if not self.handle_login_flow(email, password):
                            return False
                        # Check if we successfully logged in (back to chatgpt.com without login form)
                        self.human_delay(2, 3)
                        # Re-detect page after login
                        new_page = self.detect_current_page()
                        new_url = self.driver.current_url.lower()
                        if 'chatgpt.com' in new_url and new_page in ['dashboard', 'unknown']:
                            # Successfully logged in, no more login forms
                            print(" - ✓ Login successful, marking as past first visit")
                            self.first_chatgpt_visit = False
                        continue
                    
                    # Handle profile page
                    if current_page == 'profile':
                        # Need to fill profile
                        profile = random.choice(self.random_pool) if self.random_pool else {}
                        success = self.handle_profile_page(profile)
                        if success:
                            # After profile, mark as past first visit
                            print(" - ✓ Profile completed, marking as past first visit")
                            self.first_chatgpt_visit = False
                            self.human_delay(2, 3)
                        continue
                    
                    # Handle OTP page
                    if current_page == 'otp':
                        # Need to enter OTP
                        print(" - Waiting for OTP email...")
                        time.sleep(5)
                        
                        print(" - Opening tool.js to fetch OTP...")
                        otp = self.fetch_otp_using_tooljs(email_line)
                        
                        if not otp:
                            print(" - ✗ Failed to get OTP")
                            return False
                        
                        # Enter OTP
                        print(f" - Got OTP: {otp}, entering...")
                        if self.enter_otp(otp):
                            # Mark that we've passed login stage
                            self.first_chatgpt_visit = False
                            print(" - ✓ OTP entered, marking as past first visit")
                            self.human_delay(2, 3)
                            # Check if Continue button needed
                            if self.click_continue_button():
                                self.human_delay(4, 6)
                        continue
                    
                    # Handle OAuth or error
                    if current_page == 'oauth_error':
                        print("\\n✗ ERROR: Redirected to Google/Microsoft OAuth")
                        return False
                    
                    if current_page == 'error':
                        print("\\n✗ ERROR: Error page detected")
                        return False
                
                else:
                    # NOT FIRST VISIT - After OTP, proceed to upgrade
                    # But first check if we're on profile page
                    if current_page == 'profile':
                        print(" - On profile page (after OTP), filling information...")
                        profile = random.choice(self.random_pool) if self.random_pool else {}
                        success = self.handle_profile_page(profile)
                        if success:
                            self.human_delay(2, 3)
                            # return True  # Profile completed, account ready
                        continue
                    
                    if 'chatgpt.com' in current_url:
                        print(" - ✓ Not first visit, on chatgpt.com → Proceeding to Business upgrade...")
                        self.human_delay(2, 3)
                        
                        if self.upgrade_to_business_plan():
                            return True
                        else:
                            print("\n⚠️  Business plan upgrade failed, but account was created")
                            return True
                    else:
                        print(f" - Waiting for redirect to chatgpt.com (current: {current_url})...")
                        self.human_delay(3, 5)
                        continue
            
            print("\\n✗ Max iterations reached, stopping")
            return False
            
        except Exception as e:
            print(f"\\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def enter_otp(self, otp):
        """Enter OTP code"""
        otp_selectors = [
            'input[type="tel"]',
            'input[maxlength="6"]',
            'input[aria-label*="code" i]',
            'input[name*="code" i]',
            'input[id*="code" i]'
        ]
        
        for selector in otp_selectors:
            try:
                otp_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if otp_input:
                    otp_input.clear()
                    for digit in otp:
                        otp_input.send_keys(digit)
                        time.sleep(random.uniform(0.05, 0.15))
                    print(" - ✓ OTP entered")
                    return True
            except:
                continue
        
        print(" - ✗ Could not find OTP input field")
        return False
    
    def handle_login_flow(self, email, password):
        """Handle email and password entry flow"""
        # Look for login/signup button first
        print(" - Looking for Log in button...")
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            buttons.extend(self.driver.find_elements(By.TAG_NAME, 'a'))
            
            for btn in buttons:
                text = btn.text.strip().lower()
                if 'log in' in text or 'login' in text or text == 'sign in':
                    btn.click()
                    print(" - ✓ Clicked Log in button")
                    self.human_delay(2, 3)
                    break
        except Exception as e:
            print(f" - Could not find Log in button (may already be on login page)")
        
        # Find and fill email input
        print(" - Looking for email input...")
        email_input = None
        
        selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email"]',
            'input[placeholder*="email" i]'
        ]
        
        for selector in selectors:
            try:
                # Wait for element to be visible and interactable
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                # Double check it's interactable
                email_input = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if email_input:
                    break
            except:
                continue
        
        if not email_input:
            print(" - ✗ Email input not found!")
            return False
        
        # Scroll into view and focus
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_input)
        time.sleep(0.5)
        
        # Type email using JavaScript to clear first (more reliable)
        print(f" - Typing email: {email}")
        self.driver.execute_script("arguments[0].value = '';", email_input)
        self.driver.execute_script("arguments[0].focus();", email_input)
        time.sleep(0.3)
        
        # Type with human-like behavior
        self.human_type(email_input, email)
        print(" - ✓ Email entered")
        self.human_delay(1, 2)
        
        # Click Continue after email
        print(" - Looking for Continue button...")
        if not self.click_continue_button():
            # Fallback: press Enter
            from selenium.webdriver.common.keys import Keys
            email_input.send_keys(Keys.RETURN)
            print(" - ✓ Pressed Enter")
        
        self.human_delay(2, 3)
        
        # Look for password input
        print(" - Looking for password input...")
        password_input = None
        
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]',
            'input[placeholder*="password" i]'
        ]
        
        for selector in password_selectors:
            try:
                password_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if password_input:
                    break
            except:
                continue
        
        if not password_input:
            print(" - ✗ Password input not found (may not be needed)")
            return True  # Some flows don't need password at this stage
        
        # Type password using JavaScript focus
        print(" - Typing password...")
        self.driver.execute_script("arguments[0].focus();", password_input)
        time.sleep(0.3)
        self.human_type(password_input, password)
        print(" - ✓ Password entered")
        
        self.human_delay(1, 2)
        
        # Click Continue after password
        print(" - Looking for Continue button after password...")
        if not self.click_continue_button():
            # Fallback: press Enter
            from selenium.webdriver.common.keys import Keys
            try:
                password_input.send_keys(Keys.RETURN)
                print(" - ✓ Pressed Enter")
            except:
                pass
        
        self.human_delay(3, 5)
        
        # Check URL for errors
        current_url = self.driver.current_url
        print(f" - Current URL: {current_url}")
        
        if '/api/auth/error' in current_url or '/error' in current_url:
            print("\\n✗ ERROR: Auth error page detected")
            print("   Possible reasons:")
            print("   - Email domain blocked")
            print("   - Email already registered")
            print("   - Rate limiting")
            return False
        
        return True
    
    def run(self):
        """Main execution loop"""
        print("\\n" + "="*60)
        print("ChatGPT Auto Account Creator - Python Version")
        print("="*60)
        print(f"Total emails to process: {len(self.email_lines)}\\n")
        
        success_count = 0
        failed_count = 0
        
        # Process each account one at a time
        for i, line in enumerate(self.email_lines, 1):
            print(f"\\n[{i}/{len(self.email_lines)}] Processing...")
            
            # Create unique profile for this account
            profile_path = os.path.join(os.path.dirname(__file__), f'chrome-profile-temp-{i}')
            
            try:
                # Create fresh profile directory
                if os.path.exists(profile_path):
                    import shutil
                    shutil.rmtree(profile_path, ignore_errors=True)
                os.makedirs(profile_path, exist_ok=True)
                
                print(f"Using fresh Chrome profile: {profile_path}")
                print("="*60)
                
                # Setup fresh driver for this account
                self.driver = self.setup_driver(profile_path)
                
                # Create account
                result = self.create_account(line)
                
                if result:
                    success_count += 1
                    with open(self.output_dir / "TaiKhoanThanhCong.txt", 'a', encoding='utf-8') as f:
                        f.write(line + '\n')
                        
                    print(f"\\n✅ Account {i} created successfully!")
                else:
                    failed_count += 1
                    print(f"\\n❌ Account {i} failed")
                    
            except Exception as e:
                print(f"\\n❌ Error processing account {i}: {e}")
                failed_count += 1
            finally:
                # Close driver after each account
                if self.driver:
                    try:
                        self.driver.quit()
                        print(f"\\n🔒 Browser closed for account {i}")
                    except:
                        pass
                    self.driver = None
                
                # Clean up temporary profile to free disk space
                try:
                    if os.path.exists(profile_path):
                        import shutil
                        shutil.rmtree(profile_path, ignore_errors=True)
                        print(f"🧹 Cleaned up profile: {profile_path}")
                except Exception as cleanup_error:
                    print(f"⚠️  Could not clean profile: {cleanup_error}")
            
            # Delay between accounts
            if i < len(self.email_lines):
                print(f"\\n⏳ Waiting {self.delay_between_accounts}s before next account...")
                time.sleep(self.delay_between_accounts)
        
        print("\\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"✓ Success: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"Total: {len(self.email_lines)}")
        print("="*60)


if __name__ == '__main__':
    try:
        creator = ChatGPTAccountCreator()
        creator.run()
    except KeyboardInterrupt:
        print("\\n\\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
