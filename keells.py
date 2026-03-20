import time # Add this to your imports at the top
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import csv
from sync import sync_to_cloud
import re
# Set up Chrome options to keep the browser open
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--headless=new") # Run without a window
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)


categories = [
    "fresh-vegetables",
    "fresh-fruits",
    "keells-meat-shop",
    "fresh-fish",
    "beverages",
    "chilled-products",
    "frozen-food",
    "grocery",
    "household-essentials",
    "hampers-and-vouchers",
    "keells-bakery",
    "electronic-devices"
]


def scrape(category):
    try:
        print("Navigating to the website...")
        url = "https://www.keellssuper.com/"+category
        driver.get(url)

        wait = WebDriverWait(driver, 200)

        category = category.replace("-", " ").title()
        
        print("Waiting for Ambarella product card to load...")
        ambarella_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'product-card-nameV2')]")
            )
        )
        print("Ambarella card loaded.")

        print("Scrolling to find the 'View All' button...")
        view_all_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[@type='button' and contains(@class, 'btn-success') and contains(text(), 'View All')]")
            )
        )
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", view_all_button)
        print("found it")

        # 5. Click the button
        view_all_button.click()
        print("Clicked 'View All'. Waiting for new items to load...")

        # 6. Give the DOM a moment to process the click and start loading new content
        time.sleep(3) 

        # Wait until the product cards are present on the new page


        extracted_products = []
        current_page = 0
        while True:
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card-containerV2")))
            
            # 7. Find all the product cards on the screen
            product_cards = driver.find_elements(By.CLASS_NAME, "product-card-containerV2")
            print(f"Found {len(product_cards)} products. Extracting data...\n")


            # 8. Loop through each card and extract specific data
            for card in product_cards:
                try:
                    # Extract Name
                    name_element = card.find_element(By.CLASS_NAME, "product-card-nameV2")
                    name = name_element.text.strip()
                    
                    # Extract Price
                    price_element = card.find_element(By.CLASS_NAME, "product-card-final-priceV2")
                    # Using replace('\n', ' ') in case the HTML formats the price and " / KG" on different lines
                    price = price_element.text.strip().replace('\n', ' ') 
                    
                    # Extract Image URL
                    img_element = card.find_element(By.TAG_NAME, "img")
                    img_url = img_element.get_attribute("src")
                    
                    # Store it in a dictionary
                    product_data = {
                        "category": category,
                        "name": name,
                        "price": price,
                        "image_url": img_url
                    }
                    price_str = price
                    extracted_products.append(product_data)
                    
                    numeric_part = re.search(r"([\d,]+\.?\d*)", price_str).group(1)

                    # 2. Convert to a clean integer string (removing .00 and commas if they exist)
                    price = str(int(float(numeric_part.replace(',', ''))))

                    # 3. Extract the unit
                    # This takes everything after the "/"
                    unit = price_str.split("/")[-1].strip()

                    sync_to_cloud(category,name,price,unit,"1",img_url,"keells")
                    
                    # Print as we go
                    print(f"Extracted: {name} | {price}")
                    
                except Exception as e:
                    # If one card is missing a piece of data, we catch the error here 
                    # so it skips that specific card instead of crashing the whole script
                    print(f"Skipped a card due to missing data.",e)

            try:
                next_button = next_button = driver.find_element(By.XPATH, "//button[contains(@class, 'page-number-button-arrow') and .//img[contains(@src, 'Right')]]")
                        
                        # Scroll to the pagination bar so the click isn't intercepted by a sticky footer/header
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                time.sleep(1) # Give it a second to finish scrolling
                        
                next_button.click()
                print("Moving to the next page...")
                        
                current_page += 1
                time.sleep(3) # Wait for the new products to populate the DOM
                        
            except NoSuchElementException:
                # If the next button isn't found, we are on the last page!
                print("\nNo more pages found. Scraping complete!")
                break
        print("\nExtraction complete!")
        return True
            
    except Exception as e:
        try:
            # Check if the "Your session expired!" text is present
            session_expired = driver.find_elements(By.XPATH, "//h5[contains(text(), 'Your session expired!')]")
            if session_expired:
                print("\n⚠️ Session Expired popup detected!")
                # Find and click the Ok button
                ok_button = driver.find_element(By.XPATH, "//button[normalize-space()='Ok']")
                ok_button.click()
                print("Clicked 'Ok'. Clearing session and returning false to trigger a restart...")
                time.sleep(2) # Give the modal a second to disappear
                return False # Returning False tells the main loop to retry
        except Exception as modal_error:
            print("Tried to close the session popup but failed:", modal_error)
        
        print(f"\nAn error occurred (not related to session expiry): {e}")
        return False # Return False so it can be retried anyway
    finally:
            
            
        print("Successfully saved to 'keells_vegetables.csv'!")


for category in categories:
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\n--- Starting {category} (Attempt {attempt + 1}/{max_retries}) ---")
        success = scrape(category)
        
        if success:
            print(f"Successfully scraped {category}!")
            break # Break out of the retry loop and move to the next category
        else:
            print(f"Failed to scrape {category}. Retrying in 3 seconds...")
            time.sleep(3)
            
    # Optional: Write a fallback if it fails 3 times
    if not success:
        print(f"Skipping {category} after {max_retries} failed attempts.")