from selenium import webdriver

driver = webdriver.Chrome()

stationNameCodeMap = {
    
}


FROM = ""
TO = ""
DATE = ""
QUOTA = ""

url = f"https://askdisha.irctc.co.in/?FROM={FROM}&TO={TO}&DATE={DATE}&QUOTA={QUOTA}"

driver.get('')