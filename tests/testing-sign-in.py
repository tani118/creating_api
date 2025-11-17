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

def sign_in():
    number = "8837320987"
    print("Clicking on Sign In button...")
    sign_in_button = driver.find_element(By.XPATH, "//*[@id='corover-body']/div[1]/div/div[2]/button/span")
    sign_in_button.click()
    
    print("Filling in mobile number...")
    mobile_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div/div[2]/input"))
    )
    mobile_input.send_keys(number)
    
    print("Submitting sign in form...")
    submit_button = driver.find_element(By.XPATH, "//*[@id='drawer-footer']/span/button")
    submit_button.click()

    time.sleep(3)

    otp = "123456"

    otp_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div/div[2]/input"))
    )
    otp_input.send_keys(otp)

    time.sleep(2)

    submit_button = driver.find_element(By.XPATH, "//*[@id='drawer-footer']/span/button")
    submit_button.click()

    time.sleep(3)

if __name__ == "__main__":
    driver = init_driver()
    driver.get("https://askdisha.irctc.co.in/")
    
    sign_in()