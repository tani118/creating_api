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
        
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
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
            
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            driver = seleniumwire_webdriver.Chrome(options=options)
    return driver

def book_train_submit():
    train_number = "12449"
    quota = "General"
    travel_class = "2A"
    journey_date = "26 Nov, Wed"

    passenger_details = [
        {
            "name": "John Doe",
            "age": 30,
            "gender": "Male",
            "berth_preference": "Lower",
            "food_preference": "Vegetarian"
        },
        {
            "name": "Jane Smith",
            "age": 28,
            "gender": "Female",
            "berth_preference": "Middle",
            "food_preference": "Non-Vegetarian"
        },
        {
            "name": "Alice Johnson",
            "age": 5,
            "gender": "Female",
            "berth_preference": "Lower",
            "food_preference": "Vegetarian"
        }
    ]

    print("Waiting for page to load...")
    time.sleep(5)

    print(f"Looking for train {train_number}...")
    all_p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-gplwa-d')]//p")
    train_div = None
    
    for p_tag in all_p_tags:
        text = driver.execute_script("return arguments[0].textContent;", p_tag).strip()
        if f'({train_number})' in text:
            train_div = p_tag
            break
    
    if not train_div:
        print(f"Train {train_number} not found on the page!")
        return {"error": "Train not found"}
    
    train_card = train_div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'sc-gplwa-d')]")
    print(f"Found train: {driver.execute_script('return arguments[0].textContent;', train_div).strip()}")
    
    time.sleep(2)
    print("Clicking ticket button...")
    ticket_buttons = train_card.find_elements(By.XPATH, ".//div[contains(@class, 'ticket-new')]")
    if ticket_buttons:
        ticket_buttons[0].click()
        time.sleep(5)
    else:
        return {"error": "No ticket buttons found"}

    print(f"Selecting quota: {quota}")
    quota_section = driver.find_element(By.XPATH, "//p[text()='Quota']/following-sibling::div")
    quota_divs = quota_section.find_elements(By.XPATH, "./div")
    for q_div in quota_divs:
        if q_div.text == quota:
            q_div.click()
            break
    time.sleep(5)
    
    print(f"Selecting class: {travel_class}")
    class_section = driver.find_element(By.XPATH, "//p[text()='Class']/following-sibling::div")
    class_divs = class_section.find_elements(By.XPATH, "./div")
    for c_div in class_divs:
        if c_div.text == travel_class:
            c_div.click()
            break
    time.sleep(5)
    
    print(f"Selecting date: {journey_date}")
    date_divs = driver.find_elements(By.XPATH, "//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div[6]/div")
    for date_div in date_divs:
        date_text = driver.execute_script("return arguments[0].textContent;", date_div).strip()
        if journey_date in date_text:
            date_div.click()
            break
    time.sleep(3)

    print("Clicking BOOK TICKET button...")
    book_button = driver.find_element(By.XPATH, "//button[contains(text(), 'BOOK TICKET')]")
    book_button.click()
    time.sleep(5)

    try:
        print("Confirming booking...")
        confirm_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
        confirm_button.click()
        time.sleep(5)
        print("Confirm button clicked successfully")
    except Exception as e:
        print(f"Confirm button not found or not needed: {e}")
        time.sleep(5)
        pass

    print("Filling passenger details...")
    for idx, passenger in enumerate(passenger_details):
        if(idx != 0):
            print(f"Adding passenger {idx + 1}...")
            time.sleep(3)
            add_passenger_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Add Passenger')]")
            add_passenger_button.click()
            time.sleep(3)
        
        gender = passenger.get('gender')
        print(f"Selecting gender: {gender}")
        if gender == "Male":  # Changed from 'is' to '=='
            driver.find_element(By.XPATH, "//*[@id='passengers']/div/div/div/div[2]/div[1]/div/span/div[1]/div[1]/div").click()
            time.sleep(1)
        elif gender == "Female":  # Changed from 'is' to '=='
            driver.find_element(By.XPATH, "//*[@id='passengers']/div/div/div/div[2]/div[1]/div/span/div[1]/div[2]/div").click()
            time.sleep(1)

        time.sleep(2)  # Add small delay after gender selection

        print(f"Entering name: {passenger.get('name')}")
        name_field = driver.find_element(By.ID, "name")
        name_field.clear()
        name_field.send_keys(passenger.get('name'))
        time.sleep(1)
        
        print(f"Entering age: {passenger.get('age')}")
        age_field = driver.find_element(By.ID, "age")
        age_field.clear()
        age_field.send_keys(str(passenger.get('age')))
        time.sleep(1)

        # if passenger.get('food_preference'):
        #     try:
        #         food_pref = passenger.get('food_preference')
        #         print(f"Selecting food preference: {food_pref}")
        #         driver.find_element(By.XPATH, f"//div[contains(text(), '{food_pref}')]").click()
        #         time.sleep(2)
        #     except Exception as e:
        #         print(f"Could not set food preference: {e}")
        #         pass

        # if passenger.get('berth_preference'):
        #     try:
        #         berth_pref = passenger.get('berth_preference')
        #         print(f"Selecting berth preference: {berth_pref}")
        #         driver.find_element(By.XPATH, f"//*[@id='passengers']/div/div/div/div[2]/div[4]/div/div").click()
        #         time.sleep(2)
        #     except Exception as e:
        #         print(f"Could not set berth preference: {e}")
        #         pass


        driver.find_element(By.XPATH, "//button[contains(text(), 'Add Passenger')]").click()

    print("Clicking Review Journey...")
    driver.find_element(By.XPATH, "//*[@id='pass-step']/button").click()
    time.sleep(5)

    driver.find_element(By.XPATH, "//*[@id='drawer-footer']/div/button").click()
    time.sleep(3)

    otp_field = driver.find_element(By.XPATH, "//*[@id='disha-drawer-2']/div/div[1]/div[2]/div/div/div[1]/input")
    
    otp_field.send_keys("123456")
    time.sleep(2)

    driver.find_element(By.XPATH, "//*[@id='disha-drawer-2']/div/div[1]/div[2]/div/div/div[2]/button[1]").click()
    time.sleep(10)


    print("Booking process completed!")
    return {"status": "success", "message": "Booking form filled successfully"}


if __name__ == "__main__":
    print("IMPORTANT: First open Chrome with remote debugging enabled:")
    print("Run this command in another terminal:")
    print("google-chrome --remote-debugging-port=9222 --user-data-dir='/tmp/chrome_dev_session'\n")
    print("Then press Enter to continue...")
    input()
    
    print("Connecting to browser...")
    driver = init_driver()
    
    SRC = "NDLS"
    DST = "CDG"
    JDATE = "20251120"
    JQUOTA = "GN"

    print(f"Loading page: FROM={SRC} TO={DST} DATE={JDATE}")
    driver.get(f"https://askdisha.irctc.co.in/?FROM={SRC}&TO={DST}&DATE={JDATE}&QUOTA={JQUOTA}")
    
    result = book_train_submit()
    print(f"\nResult: {json.dumps(result, indent=2)}")
    
    print("\nBooking form filled! Check the browser.")
    print("Press Ctrl+C to close...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nScript stopped. Browser will remain open.")
        print("Done!")