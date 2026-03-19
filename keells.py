import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_keells():
    # 1. Native Selenium Setup
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("Launching Chrome...")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    short_wait = WebDriverWait(driver, 5)

    base_url = "https://www.keellssuper.com"
    filename = "keells_products.csv"
    total_products_scraped = 0

    # 2. Prepare CSV file
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Category", "Product Name", "Price", "Image URL"])
        writer.writeheader()

    try:
        print(f"Loading {base_url} to fetch categories...")
        driver.get(base_url)
        time.sleep(2) # Initial load buffer
        
        # Open the main category menu to count how many categories exist
        category_menu_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".category-ui")))
        category_menu_btn.click()
        time.sleep(1)

        categories = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[id^='dep_id_']")))
        num_categories = len(categories)
        print(f"Found {num_categories} categories. Starting extraction...\n")

        # 3. Iterate over each category by index (prevents StaleElementReferenceException)
        for i in range(num_categories):
            # Ensure we are on the base page before starting a new category
            if driver.current_url != base_url:
                driver.get(base_url)
                time.sleep(2)

            # Re-open the category menu
            try:
                category_menu_btn = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".category-ui")))
                driver.execute_script("arguments[0].click();", category_menu_btn)
                time.sleep(1)
            except Exception:
                pass # Already open or visible
            
            # Find the specific category in the list
            categories = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[id^='dep_id_']")))
            category_element = categories[i]
            
            # Extract category name for the CSV column
            try:
                category_name = category_element.text.replace('\n', ' ').strip()
                if not category_name:
                    category_name = f"Category_{i+1}"
            except Exception:
                category_name = f"Category_{i+1}"

            print(f"--- Scraping Category {i + 1}/{num_categories}: {category_name} ---")

            # Click the main category
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_element)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", category_element)

            # Click the "All [Category Name]" sub-category option
            try:
                all_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'sub-cat-span') and contains(text(), 'All')]")))
                driver.execute_script("arguments[0].click();", all_option)
            except Exception:
                print(f"    Could not find or click 'All' option for {category_name}. Skipping.")
                continue

            # Wait for and click the "View All" button if it exists
            try:
                view_all_btn = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-success")))
                if "View All" in view_all_btn.text:
                    driver.execute_script("arguments[0].click();", view_all_btn)
                    time.sleep(2)
            except Exception:
                pass # Proceed normally if there is no "View All" button

            page_number = 1

            # 4. Pagination Loop
            while True:
                print(f"  -> Scraping Page {page_number}...")
                
                # Wait for the product cards to load in the DOM
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card-image-containerV2")))
                    time.sleep(2) # Brief buffer to allow images/prices to render
                except Exception:
                    print("     No products found or took too long to load. Moving to next category.")
                    break

                # Step A: Extract products on the current page
                product_names = driver.find_elements(By.CSS_SELECTOR, ".product-card-nameV2")
                product_prices = driver.find_elements(By.CSS_SELECTOR, ".product-card-final-priceV2")
                product_images = driver.find_elements(By.CSS_SELECTOR, ".product-card-image-containerV2-image")
                
                products_data = []

                # Zip the elements together to process them concurrently
                for name_el, price_el, img_el in zip(product_names, product_prices, product_images):
                    try:
                        name = name_el.text.strip()
                        price = price_el.text.replace('\n', ' ').strip() # Keep 'Rs X.XX / KG' format clean
                        img_url = img_el.get_attribute("src")

                        if name and price:
                            products_data.append({
                                "Category": category_name,
                                "Product Name": name,
                                "Price": price,
                                "Image URL": img_url
                            })
                    except Exception:
                        continue # Skip malformed product entries

                # Append the current page's data to the CSV immediately
                if products_data:
                    with open(filename, 'a', newline='', encoding='utf-8') as file:
                        writer = csv.DictWriter(file, fieldnames=["Category", "Product Name", "Price", "Image URL"])
                        writer.writerows(products_data)
                    total_products_scraped += len(products_data)
                    print(f"     Saved {len(products_data)} products.")

                # Step B: Handle Pagination
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, ".pagination-wrapper .page-number-button-arrow")
                    
                    # Check if the button is disabled or we've hit the end
                    if not next_button.is_enabled() or "disabled" in next_button.get_attribute("class"):
                        print("     Reached the last page of this category.")
                        break
                        
                    # Click next using JS to bypass overlays
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button)
                    
                    page_number += 1
                    time.sleep(3) # Wait for network request for new page data
                    
                except Exception:
                    print("     Pagination error or no more pages.")
                    break

    finally:
        driver.quit()
        print(f"\nScraping complete! Total products scraped across all categories: {total_products_scraped}")
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    scrape_keells()