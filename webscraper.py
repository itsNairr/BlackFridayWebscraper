import os
import smtplib
from email.message import EmailMessage

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException 

from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
CC_EMAIL = os.environ.get("CC_EMAIL")

LAPTOP_SITE_LIST = {
    "Best Buy": "https://www.bestbuy.ca/en-ca/product/asus-proart-p16-16-4k-oled-touchscreen-copilot-pc-laptop-amd-ryzen-ai-9-hx-370-32gb-ram-1tb-ssd-rtx-4060/19326051",
}
TV_SITE_LIST = {
    "Best Buy": "https://www.bestbuy.ca/en-ca/product/lg-77-b5-4k-uhd-hdr-oled-smart-tv-oled77b5pua-2025/19281952",
    "LG": "https://www.lg.com/ca_en/tv-soundbars/oled/oled77b5pua/",
    "Amazon": "https://www.amazon.ca/LG-77-Inch-OLED-Smart-Built/dp/B0F8DL23H7?th=1",
    "Costco": "https://www.costco.ca/lg-77%22-class---oledb5-series---4k-uhd-oled-tv-.product.4000372801.html",
    "Vision Electronics": "https://www.visions.ca/lg-77-lg-oled-ai-b5-4k-smart-tv-2025-oled77b5pua-acc",
    "The Brick": "https://www.thebrick.com/products/lg-77-oled-evo-ai-b5-4k-smart-tv-oled77b5pua-acc",
}


class WebScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument("window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 60)
        
        self.SELECTOR_MAP = {
            "Best Buy": 'span[data-automation="product-price"] div[aria-hidden="true"] div',
            "LG": 'div[class="c-price__purchase"]',
            "Costco": 'div[id="pull-right-price"] span[class="value canada-currency-size"]',
            "Amazon": 'span[class="a-price-whole"]', 
            "Vision Electronics": 'span[class="price"]',
            "The Brick": 'span[id="productPrice"]'
        }
        print("WebScraper initialized")

    def open_page(self, url):
        self.driver.get(url)
        print(f"Opened page: {url}")

    def get_price(self, url_key):
        print(f"Getting price for: {url_key}")
        
        if url_key not in self.SELECTOR_MAP:
            print(f"Error: No selector defined for url_key: '{url_key}'")
            return "Not Found (No selector)"
            
        price_selector = self.SELECTOR_MAP[url_key]
        
        try:
            # Wait for the element to be visible
            price_element = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, price_selector))
            )
            price_text = price_element.text
            print(f"Price found: {price_text}")
            return price_text
            
        except TimeoutException: #TimeoutException that is caused due to waiting too long for an element to appear
            print(f"Error: Timed out waiting for element: {price_selector}")
            return "Could not find price due to timeout. Please click the link to check manually."
        except Exception as e: #Generic exception handling for any other exceptions that may occur
            print(f"Error: Could not find price. {e}")
            return "Not Found (Error)"

    def close(self):
        self.driver.quit()
        print("WebScraper closed")

# --- 3. THE EMAIL FUNCTION ---
def send_email(laptop_results, tv_results):
    print("Connecting to email server...")
    
    body = "Here is your daily price report:\n\n"
    
    body += "--- ASUS PROART P16 LAPTOP ---\n"
    body += "\n".join(laptop_results)  # Joins each item in the list with a new line
    body += "\n\n"
    
    body += "--- LG 77 B5 OLED TV ---\n"
    body += "\n".join(tv_results)
    body += "\n\nHave a great day!"

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = "Daily Price Tracker Report"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    
    # Only add CC if it exists
    if CC_EMAIL:
        msg['Cc'] = CC_EMAIL

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: Email failed to send. {e}")

# --- 4. THE MAIN SCRIPT ---
if __name__ == "__main__":
    driver = WebScraper()
    laptop_price_results = []
    tv_price_results = []

    # --- Scrape laptop prices ---
    print("\n--- Scraping Laptop Prices ---")
    for url_key, url in LAPTOP_SITE_LIST.items():
        try:
            driver.open_page(url)
            price = driver.get_price(url_key)
            laptop_price_results.append(f"{url_key}: {price} \n {url} \n")
        except Exception as e:
            print(f"FATAL ERROR scraping {url_key}: {e}")
            laptop_price_results.append(f"{url_key}: FAILED TO SCRAPE")
    
    # --- Scrape TV prices ---
    print("\n--- Scraping TV Prices ---")
    for url_key, url in TV_SITE_LIST.items():
        try:
            driver.open_page(url)
            price = driver.get_price(url_key)
            tv_price_results.append(f"{url_key}: {price} \n {url} \n")
        except Exception as e:
            print(f"FATAL ERROR scraping {url_key}: {e}")
            tv_price_results.append(f"{url_key}: FAILED TO SCRAPE")

    driver.close()

    # --- Send one summary email ---
    print("\n--- Sending Email ---")    
    # send_summary_email(laptop_price_results, tv_price_results)