from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from sync import sync_to_cloud
import re

def scrape_cargills():
    options = Options()
    options.add_argument("--start-maximized") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("detach", True)
    options.add_argument("--headless=new") # Run without a window
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    print("Launching Chrome...")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    base_url = "https://cargillsonline.com/"
    
    try:
        # 1. Visit the main page to get all category links
        print(f"Loading {base_url} to fetch categories...")
        driver.get(base_url)
        
        # Open the dropdown menu to expose the category links (sometimes required by the DOM)
        try:
            dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.shops-cat")))
            driver.execute_script("arguments[0].click();", dropdown)
            time.sleep(1)
        except:
            pass # If it's already open or accessible, skip

        # Extract all the category hrefs
        category_elements = driver.find_elements(By.CSS_SELECTOR, "div.dropdown-menu a.dropdown-item")
        category_urls = [elem.get_attribute("href") for elem in category_elements if elem.get_attribute("href")]
        
        print(f"Found {len(category_urls)} categories. Starting extraction...\n")
        
        # Prepare CSV file
       
        total_products_scraped = 0
        
        # 2. Iterate over each category URL
        for index, cat_url in enumerate(category_urls):
            # Extract the category name from the URL for our CSV column
            category_name = cat_url.split("?")[0].split("/")[-1].replace("-", " ")
            print(f"--- Scraping Category {index + 1}/{len(category_urls)}: {category_name} ---")
            
            driver.get(cat_url)
            page_number = 1
            
            while True:
                print(f"  -> Scraping Page {page_number}...")
                
                # Wait for the product cards to load in the DOM
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cargillProd")))
                    time.sleep(2) # Brief buffer to allow images/prices to bind in AngularJS
                except Exception as e:
                    print("     No products found or took too long to load. Moving to next category.")
                    break
                
                # Step A: Extract products on the current page
                products = driver.find_elements(By.CSS_SELECTOR, "div.cargillProd")
                products_data = []
                
                for prod in products:
                    try:
                        # Product Name
                        name_el = prod.find_element(By.CSS_SELECTOR, "div.veg p")
                        name = name_el.get_attribute("title") or name_el.text.strip()
                        
                        # Price
                        price_el = prod.find_element(By.CSS_SELECTOR, "div.strike1 h4")
                        # The text might include the MRP strike-through (e.g., "Rs. 630.00 MRP: Rs. 900.00")
                        # We split by newline or space to grab just the actual price
                        raw_price = price_el.text.split("MRP")[0].strip()
                        price = " ".join(raw_price.split())


                        
                        # Image URL
                        img_el = prod.find_element(By.CSS_SELECTOR, "div.cargillProdNeedImg img")
                        img_url = img_el.get_attribute("src")

                        unit_el = prod.find_element(By.CSS_SELECTOR, "button.dropbtn1")
                        raw_text = unit_el.text.strip() # Example: "500.00 g" or "1 kg"
                        
                        match = re.match(r"([\d\.,]+)\s*([a-zA-Z]+)", raw_text)
                        if match:
                            quantity = match.group(1) # "500.00"
                            unit = match.group(2)     # "g"
                        else:
                            # Fallback just in case it's a weird string like "1 Pack"
                            quantity = raw_text
                        
                        products_data.append({
                            "Category": category_name,
                            "Product Name": name,
                            "Price": price,
                            "Image URL": img_url
                        })

                        sync_to_cloud(category_name,name,price,unit,quantity,img_url,"cargills")


                    except Exception as e:
                        # Skip if a product is malformed
                        continue
                

                
                # Step B: Handle Pagination
                try:
                    # Check if the "Next" button exists AND does not have the "disabled" class
                    next_button = driver.find_elements(By.CSS_SELECTOR, "li.pagination-next:not(.disabled) a")
                    
                    if next_button:
                        # Click the "Next" button using JS to avoid interception
                        driver.execute_script("arguments[0].click();", next_button[0])
                        page_number += 1
                        time.sleep(3) # Wait for the new page data to request and load
                    else:
                        print("     Reached the last page of this category.")
                        break # Break out of the while loop to move to the next category
                except Exception as e:
                    print("     Pagination error or no more pages.")
                    break
                    
    finally:
        driver.quit()
        print(f"\nScraping complete! Total products scraped across all categories: {total_products_scraped}")
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    scrape_cargills()