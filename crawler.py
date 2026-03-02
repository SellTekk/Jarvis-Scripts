import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

INPUT_FILE = "F:/crawlerv5/RELEASE.xlsx"
OUTPUT_FILE = "F:/crawlerv5/RELEASE_ergebnis.xlsx"
VERKAUFEN_BASE_URL = "https://www.verkaufen.de"
PAUSE_SECONDS = 3

class PreisCrawler:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        print("Browser gestartet")
        
    def close(self):
        if self.driver:
            self.driver.quit()
    
    def extract_product_name(self, url):
        match = re.search(r"/([a-z0-9-]+)_h_\\d+", url)
        if match:
            name = match.group(1).replace("-", " ")
            return " ".join(word.capitalize() for word in name.split())
        return ""
    
    def search_on_verkaufen(self, search_term):
        try:
            search_query = search_term.lower().replace(" ", "+")
            search_url = f"{VERKAUFEN_BASE_URL}/?s={search_query}"
            print(f"Suche: {search_term}")
            self.driver.get(search_url)
            time.sleep(PAUSE_SECONDS)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
            product_links = self.driver.find_elements(By.CSS_SELECTOR, "main a[href*='/handy-verkaufen/']")
            if product_links:
                return product_links[0].get_attribute("href")
            return ""
        except Exception as e:
            print(f"Fehler: {e}")
            return ""
    
    def get_neuware_price(self, product_url):
        try:
            print(f"Oeffne: {product_url}")
            self.driver.get(product_url)
            time.sleep(PAUSE_SECONDS)
            try:
                neuware_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Neuware')]"))
                )
                neuware_btn.click()
                time.sleep(2)
            except:
                pass
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "main li a p")
                price_text = price_elem.text
                price_match = re.search(r"[\d,]+", price_text.replace(".", ""))
                if price_match:
                    preis = float(price_match.group().replace(",", "."))
                    return round(preis * 0.9, 2)
            except:
                pass
            return 0.0
        except Exception as e:
            print(f"Preis-Fehler: {e}")
            return 0.0
    
    def run(self):
        print("Starte Preis-Crawler v1.0")
        self.setup_driver()
        df = pd.read_excel(INPUT_FILE)
        print(f"{len(df)} Produkte gefunden")
        
        # Test: nur erste 3 Produkte
        df = df.head(3)
        
        results = []
        for index, row in df.iterrows():
            print(f"[{index + 1}/{len(df)}] {row['Name']}")
            url_scrape = str(row['url scrape'])
            sku = row['sku']
            
            product_name = self.extract_product_name(url_scrape)
            if not product_name:
                product_name = row['Name']
            
            vk_link = self.search_on_verkaufen(product_name)
            preis_mindert = 0.0
            if vk_link:
                preis_mindert = self.get_neuware_price(vk_link)
            
            results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis_minus_10p": preis_mindert
            })
            
            if (index + 1) % 10 == 0:
                temp_df = pd.DataFrame(results)
                temp_df.to_excel(OUTPUT_FILE, index=False)
                print(f"Zwischengespeichert")
        
        result_df = pd.DataFrame(results)
        result_df.to_excel(OUTPUT_FILE, index=False)
        print(f"Fertig!")
        self.close()

if __name__ == "__main__":
    crawler = PreisCrawler(headless=False)
    crawler.run()
