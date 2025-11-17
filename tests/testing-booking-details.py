from seleniumwire import webdriver as seleniumwire_webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re

driver = None

def init_driver():
    global driver
    if driver is None:
        options = seleniumwire_webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        driver = seleniumwire_webdriver.Chrome(options=options)
    else:
        try:
            driver.current_url
        except:
            try:
                driver.quit()
            except:
                pass
            driver = None
            options = seleniumwire_webdriver.ChromeOptions()
            options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
            driver = seleniumwire_webdriver.Chrome(options=options)
    return driver


def list_available_trains():
    print("\nScanning page for available trains...")
    time.sleep(10)
    
    try:
        train_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-gplwa-d')]")
        print(f"Found {len(train_cards)} train cards\n")
        
        trains = []
        for idx, card in enumerate(train_cards, 1):
            try:
                train_name_elements = card.find_elements(By.XPATH, ".//p")
                for elem in train_name_elements:
                    text = driver.execute_script("return arguments[0].textContent;", elem).strip()
                    if '(' in text and ')' in text and text.count('(') == 1:
                        train_number = text.split('(')[1].split(')')[0]
                        if train_number.isdigit() and len(train_number) == 5:
                            trains.append({
                                "number": train_number,
                                "name": text
                            })
                            print(f"{idx}. {text} -> Train #{train_number}")
                            break
            except Exception as e:
                continue
        
        print(f"\nTotal trains extracted: {len(trains)}")
        return trains
        
    except Exception as e:
        print(f"Error listing trains: {e}")
        return []


def book_train(train_number):
    details = {
        "trainNumber": train_number,
        "available_quotas": {}
    }

    print(f"\nLooking for train {train_number}...")
    
    try:
        all_p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-gplwa-d')]//p")
        train_div = None
        
        for p_tag in all_p_tags:
            text = driver.execute_script("return arguments[0].textContent;", p_tag).strip()
            if f'({train_number})' in text:
                train_div = p_tag
                break
        
        if not train_div:
            print(f"Train {train_number} not found on the page!")
            return details
        
        train_card = train_div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'sc-gplwa-d')]")
    except Exception as e:
        print(f"Error finding train: {e}")
        return details
    
    print(f"Found train: {driver.execute_script('return arguments[0].textContent;', train_div).strip()}")
    time.sleep(2)
    
    ticket_buttons = train_card.find_elements(By.XPATH, ".//div[contains(@class, 'ticket-new')]")
    print(f"Found {len(ticket_buttons)} ticket options")
    
    if ticket_buttons:
        print("Clicking first ticket button...")
        ticket_buttons[0].click()
        time.sleep(5)
    else:
        print("No ticket buttons found!")
        return details

    print("\nLooking for Quota section...")
    try:
        quota_section = driver.find_element(By.XPATH, "//p[text()='Quota']/following-sibling::div")
        quota_divs = quota_section.find_elements(By.XPATH, "./div")
        print(f"Found {len(quota_divs)} quotas: {[q.text for q in quota_divs]}")
        
        for quota_div in quota_divs:
            quota_name = quota_div.text
            print(f"\nProcessing Quota: {quota_name}")
            quota_div.click()
            time.sleep(5)
            
            details["available_quotas"][quota_name] = {}
            
            class_section = driver.find_element(By.XPATH, "//p[text()='Class']/following-sibling::div")
            class_divs = class_section.find_elements(By.XPATH, "./div")
            print(f"Found {len(class_divs)} classes: {[c.text for c in class_divs]}")
            
            for class_div in class_divs:
                class_name = class_div.text
                print(f"\nProcessing Class: {class_name}")
                class_div.click()
                time.sleep(5)

                day_data = []
                daylist_divs = driver.find_elements(By.XPATH, "//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div[6]")
                print(daylist_divs)
                print(f"Found {len(daylist_divs)} date options")

                try:
                    for i in range(1, len(daylist_divs)):
                        i = 1
                        date_element = driver.find_element(By.XPATH, f"//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div[6]/div[{i}]")

                        date_text = date_element.text

                        availability_element = driver.find_element(By.XPATH, f"//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div[6]/div[{i}]/div[2]/div")
                        availability_text = availability_element.text
                        
                        availability_element.click()
                        time.sleep(3)
                        price_element = driver.find_element(By.XPATH, "//*[@id='drawer-footer']/div/div/span")
                        price_text = price_element.text

                        print(f"Date: {date_text}, Availability: {availability_text}, Price: {price_text}")

                        day_data.append({
                            "date": date_text,
                            "availability": availability_text,
                            "price": price_text
                        })

                        i += 1                                
                except Exception as e:
                    print(f"Error = {str(e)}")
                    continue
                
                details["available_quotas"][quota_name][class_name] = day_data
        
        print("\nBOOKING OPTIONS EXTRACTED SUCCESSFULLY")
        return details
        
    except Exception as e:
        print(f"\nError during booking process: {str(e)}")
        return details


if __name__ == "__main__":
    SRC = "NDLS"
    DST = "CDG"
    JDATE = "20251120"
    JQUOTA = "GN"

    print("Starting browser...")
    driver = init_driver()
    
    print(f"Loading page: FROM={SRC} TO={DST} DATE={JDATE}")
    driver.get(f"https://askdisha.irctc.co.in/?FROM={SRC}&TO={DST}&DATE={JDATE}&QUOTA={JQUOTA}")
    
    print("Waiting 10 seconds for page to fully load...")
    time.sleep(5)
    
    available_trains = list_available_trains()
    
    if available_trains:
        train_to_book = available_trains[0]["number"]
        print(f"\nAttempting to book train: {train_to_book}")
        result = book_train(train_to_book)
        
        print("\n" + "="*80)
        print("FINAL RESULT:")
        print("="*80)
        print(json.dumps(result, indent=2))
    else:
        print("\nNo trains found! Check browser window.")
    
    print("\nTest complete! Press Ctrl+C to close...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing browser...")
        driver.quit()
        print("Done!")