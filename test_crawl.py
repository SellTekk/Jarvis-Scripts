import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

INPUT_FILE = "F:/crawlerv5/RELEASE.xlsx"
OUTPUT_FILE = "F:/crawlerv5/RELEASE_ergebnis.xlsx"
VERKAUFEN_BASE_URL = "https://www.verkaufen.de"

print("=== START TEST ===")

# Read Excel
print("Reading Excel...")
df = pd.read_excel(INPUT_FILE)
print(f"Found {len(df)} rows")

# Just first row
row = df.iloc[0]
print(f"First product: {row['Name']}")
print(f"URL: {row['url scrape']}")
print(f"SKU: {row['sku']}")

# Setup browser
print("Starting browser...")
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

# Extract product name
url = str(row['url scrape'])
match = re.search(r"/([a-z0-9-]+)_h_\\d+", url)
if match:
    product_name = match.group(1).replace("-", " ")
    product_name = " ".join(word.capitalize() for word in product_name.split())
else:
    product_name = row['Name']

print(f"Searching for: {product_name}")

# Search on verkaufen.de
search_query = product_name.lower().replace(" ", "+")
search_url = f"{VERKAUFEN_BASE_URL}/?s={search_query}"
print(f"URL: {search_url}")

driver.get(search_url)
print("Page loaded, waiting...")
time.sleep(3)

# Find search box and type
try:
    search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[placeholder*='verkaufen'], input[type='text']")))
    print(f"Found search box: {search_box}")
    search_box.clear()
    search_box.send_keys(product_name)
    print("Typed product name")
    
    # Press Enter
    search_box.send_keys("\\n")
    print("Pressed Enter")
    time.sleep(3)
except Exception as e:
    print(f"Search box error: {e}")
    # Try direct navigation
    print("Trying direct URL...")

# Get page source for debugging
print(f"Current URL: {driver.current_url}")
print(f"Page title: {driver.title}")

# Find product links
try:
    # Try different selectors
    selectors = [
        "main a[href*='/handy-verkaufen/']",
        "a[href*='/handy-verkaufen/']",
        ".product-list a",
        "article a"
    ]
    
    for selector in selectors:
        links = driver.find_elements(By.CSS_SELECTOR, selector)
        if links:
            print(f"Found {len(links)} links with selector: {selector}")
            first_link = links[0].get_attribute("href")
            print(f"First link: {first_link}")
            break
except Exception as e:
    print(f"Link finding error: {e}")

# Close browser
print("Closing browser...")
driver.quit()

print("=== TEST DONE ===")
