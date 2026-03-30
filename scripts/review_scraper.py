from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains 
import pandas as pd
import time
from datetime import datetime

banks = ["Attijariwafa bank", "Banque Populaire", "BMCE Bank", "Crédit du Maroc", "Société Générale Maroc", "CIH Bank"]
cities = ["Rabat", "Casablanca", "Marrakech", "Fès", "Tanger"]

def scrape_bank_city(bank, city):
    # Setup Options
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    reviews_list = []
    local_results = [] # This must be inside the function
    try:
        print(f"--- Scraping {bank} in {city} ---")
        driver.get("https://www.google.com/maps")
        
        # 1. Handle Consent
        try:
            consent_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'Accept') or contains(text(), 'Accepter')]")))
            consent_btn.click()
            time.sleep(2)
        except:
            pass

        # 2. Search
        search_query = f"{bank} {city} Morocco"
        search_box = wait.until(EC.element_to_be_clickable((By.NAME, "q")))
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER)
        time.sleep(6)

        # 3. Disambiguate Results
        try:
            first_result = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if len(first_result) > 0:
                first_result[0].click()
                time.sleep(4)
        except:
            pass

        # 4. Open Reviews
        try:
            # We first try to click the "X reviews" trigger
            trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'avis') or contains(@aria-label, 'reviews')]")))
            trigger.click()
            time.sleep(3)
        except:
            # Fallback to coordinate-based click if button is hidden

            element = driver.find_element(By.TAG_NAME, "h1")
            ActionChains(driver).move_to_element(element).move_by_offset(0, 50).click().perform()
            time.sleep(3)

        # 5. Scroll to Load Data
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='main'][@tabindex='-1']")))
            for i in range(3): # Lowered to 3 for faster multi-bank scraping
                driver.execute_script("arguments[0].scrollBy(0, 1000);", scrollable_div)
                time.sleep(2)
        except:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 6. Extract Data
        review_elements = driver.find_elements(By.CLASS_NAME, "wiI7pd")
        print(f"Found {len(review_elements)} review text elements for {bank} {city}!")

        for text_element in review_elements:
            try:
                review_content = text_element.text
                if not review_content: continue # Skip if no text
                
                # Attempt to get author/rating, but don't crash if it fails
                try:
                    parent = text_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'jftiEf')]")
                    author = parent.find_element(By.CLASS_NAME, "d4r55").text
                    rating = parent.find_element(By.CLASS_NAME, "kvMYyc").get_attribute("aria-label")
                except:
                    author, rating = "Anonymous", "Unknown"

                local_results.append({
                    "bank_name": bank,
                    "city": city,
                    "author": author,
                    "rating": rating,
                    "review_text": review_content,
                    "extraction_date": datetime.now().strftime("%Y-%m-%d")
                })
            except Exception as e:
                print(f"Error extracting a single review: {e}")
                continue
    except Exception as e:
        print(f"General error in {bank} {city}: {e}")
    finally:
        driver.quit()
    
    return local_results # CRITICAL: Ensure this is indented correctly!

# --- MASTER EXECUTION ---
all_reviews = []
for bank in banks:
    for city in cities:
        results = scrape_bank_city(bank, city)
        if results:
            all_reviews.extend(results) # Add the list to our master collection
            print(f"Successfully added {len(results)} reviews to master list.")
        else:
            print(f"No results returned for {bank} in {city}.")

# Save everything at the end
if all_reviews:
    df = pd.DataFrame(all_reviews)
    df.to_csv("master_bank_reviews.csv", index=False)
    print(f"SUCCESS: Total reviews in CSV: {len(all_reviews)}")
else:
    print("FAILURE: Master list is still empty.")