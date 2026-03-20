import time # Add this to your imports at the top
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
# Set up Chrome options to keep the browser open
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Navigating to the website...")
    driver.get("https://www.keellssuper.com/fresh-vegetables")

    wait = WebDriverWait(driver, 200)
    
    print("Waiting for Ambarella product card to load...")
    ambarella_element = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'product-card-nameV2') and contains(text(), 'Ambarella')]")
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



    current_page = 0
    while True:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card-containerV2")))
        
        # 7. Find all the product cards on the screen
        product_cards = driver.find_elements(By.CLASS_NAME, "product-card-containerV2")
        print(f"Found {len(product_cards)} products. Extracting data...\n")

        extracted_products = []

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
                    "name": name,
                    "price": price,
                    "image_url": img_url
                }
                extracted_products.append(product_data)
                
                # Print as we go
                print(f"Extracted: {name} | {price}")
                
            except Exception as e:
                # If one card is missing a piece of data, we catch the error here 
                # so it skips that specific card instead of crashing the whole script
                print(f"Skipped a card due to missing data.")

        try:
            next_button = driver.find_element(By.CLASS_NAME, "page-number-button-arrow")
                    
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
        














except Exception as e:
    print(f"An error occurred: {e}")

finally:
    pass