from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

def scrape_keells_with_smart_wait():
    options = Options()
    options.add_argument("--start-maximized") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("Launching Chrome...")
    driver = webdriver.Chrome(options=options)
    
    wait = WebDriverWait(driver, 15) 
    
    url = "https://www.keellssuper.com/showcaseint/items/keells_products"
    print(f"Loading {url}...")
    driver.get(url)

    scraped_products = {}

    try:
        # 1. Click the "Sort by" dropdown button
        print("Locating 'Sort by' dropdown...")
        sort_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.item-order-sort-link")))
        driver.execute_script("arguments[0].click();", sort_button)
        
        # 2. Select "Name (A - Z)"
        print("Selecting 'Name (A - Z)'...")
        az_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'dropdown-item') and text()='Name (A - Z)']")))
        driver.execute_script("arguments[0].click();", az_option)
        
        # Wait for the initial sorted load to finish
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".sk-cube-grid")))
        except:
            pass
        time.sleep(2) 
        
        # 3. Read, Extract, and Scroll Loop
        print("Starting extraction loop...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Step A: Find all products currently loaded in the HTML
            names = driver.find_elements(By.CSS_SELECTOR, ".product-card-nameV2")
            current_product_count = len(names) # Store how many products we see right now
            new_items_this_round = 0
            
            for name_el in names:
                try:
                    raw_name = name_el.text
                    name = " ".join(raw_name.split())
                    
                    if not name or name in scraped_products:
                        continue
                        
                    parent_container = name_el.find_element(By.XPATH, "..")
                    price_el = parent_container.find_element(By.CSS_SELECTOR, ".product-card-final-priceV2")
                    price = " ".join(price_el.text.split())
                    
                    img_el = parent_container.find_element(By.CSS_SELECTOR, ".product-card-image-containerV2-image")
                    img_url = img_el.get_attribute("src")
                    
                    scraped_products[name] = {
                        "Product Name": name, 
                        "Price": price,
                        "Image URL": img_url
                    }
                    new_items_this_round += 1
                except Exception as e:
                    continue
            
            print(f"Found {new_items_this_round} new products. Total unique products so far: {len(scraped_products)}")
            
            # Step B: Scroll down to trigger the next load
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Step C: Wait specifically for the loading cubes to vanish
            try:
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".sk-cube-grid")))
            except Exception as e:
                pass # If it doesn't appear, just move on to the smart wait
                
            # Step D: Smart Incremental Wait (Max 100 seconds)
            # Check every second if the number of products on the screen has increased.
            max_wait_seconds = 100
            time_waited = 0
            new_data_loaded = False
            
            while time_waited < max_wait_seconds:
                new_names_list = driver.find_elements(By.CSS_SELECTOR, ".product-card-nameV2")
                if len(new_names_list) > current_product_count:
                    # The DOM has updated with new items!
                    new_data_loaded = True
                    break 
                time.sleep(1)
                time_waited += 1

            if not new_data_loaded:
                print("Waited 100 seconds but no new products appeared. Assuming end of list.")
                break
            
            # Step E: Check if we are at the absolute bottom (Height fallback)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Reached the bottom of the page. No more products loading.")
                    break
            
            last_height = new_height

    finally:
        driver.quit()

    # 4. Save to CSV
    if scraped_products:
        filename = 'keells_az_products.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["Product Name", "Price", "Image URL"])
            writer.writeheader()
            writer.writerows(scraped_products.values())
        print(f"Successfully saved {len(scraped_products)} unique products to {filename}")
    else:
        print("No data was extracted.")

if __name__ == "__main__":
    scrape_keells_with_smart_wait()