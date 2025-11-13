# from selenium import webdriver as selenium_webdriver
from seleniumwire import webdriver as seleniumwire_webdriver 
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from flask import Flask
from datetime import date, timedelta
import time
import json

# options = Options()
# options.add_argument('--disable-blink-features=AutomationControlled')
# options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
    
# driver = selenium_webdriver.Chrome(options=options)

stationNameCodeMap = {
    
}

FROM = ""
TO = ""
DATE = ""
QUOTA = ""

url = f"https://askdisha.irctc.co.in/?FROM={FROM}&TO={TO}&DATE={DATE}&QUOTA={QUOTA}"

app = Flask()

@app.route("/getFreshTokens", methods=["GET"])
def getFreshTokens():
    options = seleniumwire_webdriver.ChromeOptions()
    options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
    driver = seleniumwire_webdriver.Chrome(options=options)
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y%m%d")
    driver.get(f"https://askdisha.irctc.co.in/?FROM=DLI&TO=MMCT&DATE={tomorrow}&QUOTA=GN")
    time.sleep(5)

    from_tab = driver.find_element(By.CSS_SELECTOR, 'div[aria-label="From"]')
    from_tab.click()
    time.sleep(2)
    from_input = driver.find_element(By.ID, 'station-textbox')
    from_input.send_keys("NDLS")
    from_input_option = driver.find_element(By.XPATH, '//p[text()="NLDS"]')
    from_input_option.click()

    to_tab = driver.find_element(By.CSS_SELECTOR, 'div[aria-label="To"]')
    to_tab.click()
    time.sleep(2)
    to_input = driver.find_element(By.ID, 'station-textbox')
    to_input.send_keys("CDG")
    to_input_option = driver.find_element(By.XPATH, '//p[text()="CDG"]')
    to_input_option.click()

    time.sleep(2)
    search_button = driver.find_element(By.XPATH, '//button[text()="Search Trains"]');
    search_button.click()

    for request in driver.requests:
        if 'https://api.disha.corover.ai/dishaAPI/bot/editTrains/en' in request.url:
            body = request.body.decode('utf-8')
            payload = json.loads(body)

            return {
                'userToken': payload.get("userToken"),
                'dSession': payload.get("dSession"),
                'sessionId': payload.get("sessionId"),
            }

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)