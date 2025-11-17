from seleniumwire import webdriver as seleniumwire_webdriver 
from selenium.webdriver.common.by import By
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import date, timedelta, datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import requests as re
from agent import chat, clear_history

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

driver = None
cached_train_data = None

userTokens = {
    'userName': {
        'userToken': None,
        'dSession': None,
        'sessionId': None,
        'capturedPayload': None,
        'capturedHeaders': None
    }
}

"""
def init_driver():
    global driver
    if driver is None:
        options = seleniumwire_webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        options.add_argument('--window-position=-2400,-2400')  # Start hidden off-screen
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
            options.add_argument('--window-position=-2400,-2400')
            driver = seleniumwire_webdriver.Chrome(options=options)
    return driver
"""

# def init_driver():
#     global driver
#     if driver is None:
#         options = seleniumwire_webdriver.ChromeOptions()
#         options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
#         driver = seleniumwire_webdriver.Chrome(options=options)
#     else:
#         # Check if session is still valid
#         try:
#             driver.current_url  # This will raise exception if session is invalid
#         except:
#             # Session is invalid, create new driver
#             try:
#                 driver.quit()
#             except:
#                 pass
#             driver = None
#             options = seleniumwire_webdriver.ChromeOptions()
#             options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
#             driver = seleniumwire_webdriver.Chrome(options=options)
#     return driver


def init_driver():
    global driver
    if driver is None:
        options = seleniumwire_webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        
        # Disable blink features that check for focus
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Disable background timer throttling (helps with hidden tabs)
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Disable hang monitor to prevent timeouts
        options.add_argument('--disable-hang-monitor')
        
        # Enable DOM automation features
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set window size (required for some dynamic content)
        options.add_argument('--window-size=1920,1080')
        
        # Don't minimize - it breaks JavaScript execution
        # Instead, we'll move window off-screen after creation
        
        driver = seleniumwire_webdriver.Chrome(options=options)
        
        # Move browser window off-screen (but keep it "visible" to the OS)
        # Temporarily disabled for debugging - uncomment when ready
        # driver.set_window_position(-2000, 0)  # Move to left off-screen
        
        # Execute CDP commands to mask automation
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(document, 'hidden', {
                    get: function() { return false; }
                });
                Object.defineProperty(document, 'visibilityState', {
                    get: function() { return 'visible'; }
                });
                window.focus = function() {};
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
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
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-hang-monitor')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--window-size=1920,1080')
            
            driver = seleniumwire_webdriver.Chrome(options=options)
            
            # Move off-screen - Temporarily disabled for debugging
            # driver.set_window_position(-2000, 0)
            
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(document, 'hidden', {
                        get: function() { return false; }
                    });
                    Object.defineProperty(document, 'visibilityState', {
                        get: function() { return 'visible'; }
                    });
                    window.focus = function() {};
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
    
    return driver

@app.route("/closeBrowser", methods=["GET"])
def closeBrowser():
    global driver
    if driver:
        driver.quit()
        driver = None
        return jsonify({"message": "Browser closed successfully"}), 200
    return jsonify({"message": "Browser was not running"}), 200

@app.route("/init-browser", methods=["GET"])
def initialize_browser():
    global driver
    try:
        if driver:
            return jsonify({
                "message": "Browser already running",
                "status": "already_initialized"
            })
        
        print("Initializing browser...")
        driver = init_driver()
        driver.get("https://askdisha.irctc.co.in/")
        time.sleep(5)
        
        return jsonify({
            "message": "Browser initialized successfully",
            "status": "success",
            "url": driver.current_url
        })
    
    except Exception as e:
        print(f"Error initializing browser: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to initialize browser",
            "details": str(e)
        }), 500
    
@app.route("/getTrainDetailsWithRefresh", methods=["POST"])
def getTrainDetailsWithRefresh():
    global driver, cached_train_data
    
    data = request.get_json()
    SRC = data.get('SRC')
    DST = data.get('DST')
    JDATE = data.get('JDATE')
    JQUOTA = data.get('JQUOTA')
    
    driver = init_driver()
    driver.get(f"https://askdisha.irctc.co.in/?FROM={SRC}&TO={DST}&DATE={JDATE}&QUOTA={JQUOTA}")
    time.sleep(15)

    for req in driver.requests:
        if 'https://api.disha.corover.ai/dishaAPI/bot/editTrains/en' in req.url:
            if req.body:
                body = req.body.decode('utf-8')
                payload = json.loads(body)
                
                userTokens['userName']['userToken'] = payload.get("userToken")
                userTokens['userName']['dSession'] = payload.get("dSession")
                userTokens['userName']['sessionId'] = payload.get("sessionId")
                userTokens['userName']['capturedPayload'] = payload
                
                headers_dict = dict(req.headers)
                headers_dict.pop('content-length', None)
                headers_dict.pop('accept-encoding', None)
                userTokens['userName']['capturedHeaders'] = headers_dict
                break
    
    for req in driver.requests:
        if 'https://api.disha.corover.ai/dishaAPI/bot/editTrains/en' in req.url:
            if req.response:
                response_body = req.response.body.decode('utf-8')
                response_json = json.loads(response_body)
                cached_train_data = response_json
                
                # Debug logging - print cache structure
                print("\n" + "="*80)
                print("CACHED TRAIN DATA STRUCTURE:")
                print("="*80)
                print(f"Total trains cached: {len(response_json.get('trainBtwnStnsList', []))}")
                
                # Show first train's structure
                if response_json.get('trainBtwnStnsList'):
                    first_train = response_json['trainBtwnStnsList'][0]
                    print(f"\nFirst train example: {first_train.get('trainNumber')} - {first_train.get('trainName')}")
                    print(f"Keys in train object: {list(first_train.keys())}")
                    
                    if first_train.get('availability'):
                        print(f"\nAvailability data structure:")
                        first_avl = first_train['availability'][0]
                        print(f"Keys in availability: {list(first_avl.keys())}")
                        print(f"Sample availability: {json.dumps(first_avl, indent=2)}")
                
                print("="*80 + "\n")
                
                return jsonify(response_json)
    
    return jsonify({"status": 500, "message": "No response captured"}), 500

@app.route("/trains/available", methods=["GET"])
def get_available_trains():
    """
    This endpoint filters trains from the CACHE (cached_train_data).
    It does NOT make new API calls - it reads from memory.
    """
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    print("\n" + "="*80)
    print("GET /trains/available - Filtering from cache")
    print("="*80)
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    print(f"Total trains in cache: {len(trains)}")
    
    available_trains = []
    trains_with_avl = 0
    trains_with_available_status = 0
    
    for train in trains:
        train_num = train.get('trainNumber')
        availability_list = train.get('availability', [])
        
        if availability_list:
            trains_with_avl += 1
            
            # Debug: Show availability status for first train
            if trains_with_avl == 1:
                print(f"\nExample - Train {train_num}:")
                for avl in availability_list[:2]:  # Show first 2 classes
                    status = avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', 'NO_STATUS')
                    print(f"  Class {avl.get('className')}: {status}")
        
        has_availability = any(
            avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', '').startswith('AVAILABLE')
            for avl in availability_list
        )
        
        if has_availability:
            trains_with_available_status += 1
            available_trains.append({
                'trainNumber': train.get('trainNumber'),
                'trainName': train.get('trainName'),
                'departureTime': train.get('departureTime'),
                'arrivalTime': train.get('arrivalTime'),
                'duration': train.get('duration'),
                'fromStation': train.get('fromStnCode'),
                'toStation': train.get('toStnCode'),
                'trainType': train.get('trainType', []),
                'availableClasses': [
                    {
                        'class': avl.get('className'),
                        'status': avl.get('details', {}).get('avlDayList', {}).get('availablityStatus'),
                        'fare': avl.get('details', {}).get('avlDayList', {}).get('totalFare')
                    }
                    for avl in train.get('availability', [])
                    if avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', '').startswith('AVAILABLE')
                ]
            })
    
    print(f"\nFiltering results:")
    print(f"  - Trains with availability data: {trains_with_avl}/{len(trains)}")
    print(f"  - Trains with AVAILABLE status: {trains_with_available_status}")
    print(f"  - Trains returned to client: {len(available_trains)}")
    print("="*80 + "\n")
    
    return jsonify({
        'count': len(available_trains),
        'trains': available_trains
    })

@app.route("/trains/filter", methods=["POST"])
def filter_trains():
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    filters = request.get_json()
    trains = cached_train_data.get('trainBtwnStnsList', [])
    filtered_trains = []
    
    for train in trains:
        if filters.get('trainType') and not any(t in train.get('trainType', []) for t in filters['trainType']):
            continue
        
        if filters.get('departureAfter'):
            dep_time = datetime.strptime(train.get('departureTime'), '%H:%M').time()
            filter_time = datetime.strptime(filters['departureAfter'], '%H:%M').time()
            if dep_time < filter_time:
                continue
        
        if filters.get('departureBefore'):
            dep_time = datetime.strptime(train.get('departureTime'), '%H:%M').time()
            filter_time = datetime.strptime(filters['departureBefore'], '%H:%M').time()
            if dep_time > filter_time:
                continue
        
        available_classes = []
        for avl in train.get('availability', []):
            class_name = avl.get('className')
            avl_details = avl.get('details', {}).get('avlDayList', {})
            status = avl_details.get('availablityStatus', '')
            
            if filters.get('classes') and class_name not in filters['classes']:
                continue
            
            if filters.get('onlyAvailable') and not status.startswith('AVAILABLE'):
                continue
            
            available_classes.append({
                'class': class_name,
                'status': status,
                'fare': avl_details.get('totalFare')
            })
        
        if available_classes or not filters.get('onlyAvailable'):
            filtered_trains.append({
                'trainNumber': train.get('trainNumber'),
                'trainName': train.get('trainName'),
                'departureTime': train.get('departureTime'),
                'arrivalTime': train.get('arrivalTime'),
                'duration': train.get('duration'),
                'distance': train.get('distance'),
                'fromStation': train.get('fromStnCode'),
                'toStation': train.get('toStnCode'),
                'trainType': train.get('trainType', []),
                'runningDays': {
                    'monday': train.get('runningMon') == 'Y',
                    'tuesday': train.get('runningTue') == 'Y',
                    'wednesday': train.get('runningWed') == 'Y',
                    'thursday': train.get('runningThu') == 'Y',
                    'friday': train.get('runningFri') == 'Y',
                    'saturday': train.get('runningSat') == 'Y',
                    'sunday': train.get('runningSun') == 'Y'
                },
                'availableClasses': available_classes if available_classes else [
                    {
                        'class': avl.get('className'),
                        'status': avl.get('details', {}).get('avlDayList', {}).get('availablityStatus'),
                        'fare': avl.get('details', {}).get('avlDayList', {}).get('totalFare')
                    }
                    for avl in train.get('availability', [])
                ]
            })
    
    return jsonify({
        'count': len(filtered_trains),
        'filters_applied': filters,
        'trains': filtered_trains
    })

@app.route("/trains/by-class/<class_code>", methods=["GET"])
def trains_by_class(class_code):
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    result = []
    
    for train in trains:
        for avl in train.get('availability', []):
            if avl.get('className') == class_code.upper():
                avl_details = avl.get('details', {}).get('avlDayList', {})
                result.append({
                    'trainNumber': train.get('trainNumber'),
                    'trainName': train.get('trainName'),
                    'departureTime': train.get('departureTime'),
                    'arrivalTime': train.get('arrivalTime'),
                    'duration': train.get('duration'),
                    'class': class_code.upper(),
                    'status': avl_details.get('availablityStatus'),
                    'fare': avl_details.get('totalFare')
                })
    
    return jsonify({
        'class': class_code.upper(),
        'count': len(result),
        'trains': result
    })

@app.route("/trains/cheapest", methods=["GET"])
def cheapest_trains():
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    class_filter = request.args.get('class')
    trains = cached_train_data.get('trainBtwnStnsList', [])
    fare_list = []
    
    for train in trains:
        for avl in train.get('availability', []):
            avl_details = avl.get('details', {}).get('avlDayList', {})
            fare = avl_details.get('totalFare')
            status = avl_details.get('availablityStatus', '')
            class_name = avl.get('className')
            
            if fare and status.startswith('AVAILABLE'):
                if not class_filter or class_name == class_filter.upper():
                    fare_list.append({
                        'trainNumber': train.get('trainNumber'),
                        'trainName': train.get('trainName'),
                        'departureTime': train.get('departureTime'),
                        'arrivalTime': train.get('arrivalTime'),
                        'duration': train.get('duration'),
                        'class': class_name,
                        'fare': int(fare),
                        'status': status
                    })
    
    fare_list.sort(key=lambda x: x['fare'])
    
    return jsonify({
        'count': len(fare_list),
        'trains': fare_list[:10]
    })

@app.route("/trains/fastest", methods=["GET"])
def fastest_trains():
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    
    def duration_to_minutes(duration_str):
        parts = duration_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    
    train_list = []
    for train in trains:
        has_available = any(
            avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', '').startswith('AVAILABLE')
            for avl in train.get('availability', [])
        )
        
        if has_available:
            train_list.append({
                'trainNumber': train.get('trainNumber'),
                'trainName': train.get('trainName'),
                'departureTime': train.get('departureTime'),
                'arrivalTime': train.get('arrivalTime'),
                'duration': train.get('duration'),
                'durationMinutes': duration_to_minutes(train.get('duration')),
                'trainType': train.get('trainType', [])
            })
    
    train_list.sort(key=lambda x: x['durationMinutes'])
    
    for train in train_list:
        del train['durationMinutes']
    
    return jsonify({
        'count': len(train_list),
        'trains': train_list[:10]
    })

@app.route("/trains/by-type/<train_type>", methods=["GET"])
def trains_by_type(train_type):
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    result = []
    
    for train in trains:
        if train_type.upper() in train.get('trainType', []):
            result.append({
                'trainNumber': train.get('trainNumber'),
                'trainName': train.get('trainName'),
                'departureTime': train.get('departureTime'),
                'arrivalTime': train.get('arrivalTime'),
                'duration': train.get('duration'),
                'trainType': train.get('trainType', []),
                'availableClasses': train.get('avlClasses', [])
            })
    
    return jsonify({
        'type': train_type.upper(),
        'count': len(result),
        'trains': result
    })

@app.route("/trains/summary", methods=["GET"])
def trains_summary():
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    
    total_trains = len(trains)
    available_count = 0
    waitlist_count = 0
    rac_count = 0
    
    train_types = {}
    classes_available = set()
    
    for train in trains:
        for avl in train.get('availability', []):
            status = avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', '')
            classes_available.add(avl.get('className'))
            
            if status.startswith('AVAILABLE'):
                available_count += 1
            elif 'WL' in status:
                waitlist_count += 1
            elif 'RAC' in status:
                rac_count += 1
        
        for t_type in train.get('trainType', []):
            train_types[t_type] = train_types.get(t_type, 0) + 1
    
    return jsonify({
        'totalTrains': total_trains,
        'availableSeats': available_count,
        'waitlist': waitlist_count,
        'rac': rac_count,
        'trainTypes': train_types,
        'classesAvailable': list(classes_available),
        'quotaList': cached_train_data.get('quotaList', [])
    })

@app.route("/trains/<train_number>", methods=["GET"])
def train_details(train_number):
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    
    for train in trains:
        if train.get('trainNumber') == train_number:
            return jsonify(train)
    
    return jsonify({"error": f"Train {train_number} not found"}), 404

@app.route("/trains/<train_number>/route", methods=["GET"])
def train_route(train_number):
    journey_date = request.args.get('journeyDate')
    starting_station = request.args.get('startingStationCode')
    
    if not journey_date or not starting_station:
        return jsonify({
            "error": "Missing required parameters",
            "required": ["journeyDate", "startingStationCode"]
        }), 400
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en-IN;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://askdisha.irctc.co.in",
        "referer": "https://askdisha.irctc.co.in/",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    
    url = f"https://api.disha.corover.ai/dishaAPI/bot/trnscheduleEnq/{train_number}"
    params = {
        "journeyDate": journey_date,
        "startingStationCode": starting_station
    }
    
    response = re.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({
            "error": "Failed to fetch train route",
            "status": response.status_code
        }), response.status_code
    

# @app.route("/booktrain/<train_number>", methods=["GET"])
# def book_train(train_number):
#     details = {
#         "trainNumber": train_number,
#         "available_quotas": {}
#     }

#     train_div = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-gplwa-d') and .//p[contains(text(), '{train_number}')]]")
#     time.sleep(2)
#     train_div.find_element(By.XPATH, ".//div[contains(@class, 'ticket-new')]").click()
#     time.sleep(5)

#     quota_section = driver.find_element(By.XPATH, "//p[text()='Quota']/following-sibling::div")
#     quota_divs = quota_section.find_elements(By.XPATH, "./div")
#     available_quotas = [quota_div.text for quota_div in quota_divs]
    
#     for quota_div in quota_divs:
#         quota_name = quota_div.text
#         quota_div.click()
#         time.sleep(5)
        
#         details["available_quotas"][quota_name] = {}
        
#         class_section = driver.find_element(By.XPATH, "//p[text()='Class']/following-sibling::div")
#         class_divs = class_section.find_elements(By.XPATH, "./div")
        
#         for class_div in class_divs:
#             class_name = class_div.text
#             class_div.click()
#             time.sleep(5)

#             day_data = []
#             daylist_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'day')]")

#             for day_div in daylist_divs:
#                 date_element = day_div.find_element(By.XPATH, ".//p[contains(@style, 'font-weight: 600')]")
#                 date_text = date_element.text
                
#                 availability_element = day_div.find_element(By.XPATH, ".//p[contains(@style, 'color: rgb(165, 164, 166)') or contains(@style, 'font-weight: 600')]")
#                 availability_text = availability_element.text
                
#                 availability_element.click()
#                 time.sleep(3)
#                 price_element = driver.find_element(By.XPATH, "//span[contains(@style, 'font-size: 20px; font-weight: 600; color: rgb(42, 42, 42)')]")
#                 price_text = price_element.text

#                 day_data.append({
#                     "date": date_text,
#                     "availability": availability_text,
#                     "price": price_text
#                 })
            
#             details["available_quotas"][quota_name][class_name] = day_data
    
#     return jsonify(details)

@app.route("/booktrain/", methods=["POST"])
def book_train_submit():
    data = request.get_json()
    train_number = data.get('train_number')
    quota = data.get('quota')
    travel_class = data.get('class')
    journey_date = data.get('journey_date')

    passenger_details = data.get('passenger_details')

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
    
    print("Removing existing passengers...")
    while True:
        try:
            # Check if passenger div still exists
            passenger_divs = driver.find_elements(By.XPATH, "//*[@id='passengers']/div/div/div/div[2]/div[1]")
            
            if not passenger_divs:
                print("No more passengers to remove")
                break
            
            # Find and click delete button
            delete_button = driver.find_element(By.XPATH, "//*[@id='passengers']/div/div/div/div[2]/div[1]/div[1]/img[2]")
            delete_button.click()
            print(f"Deleted passenger. Remaining: {len(passenger_divs) - 1}")
            time.sleep(2)  # Wait for deletion animation/DOM update
            
        except Exception as e:
            print(f"No more delete buttons found or error: {e}")
            break

    print("All existing passengers removed. Now adding new passengers...")
    time.sleep(2)

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


    try:
        confirm_buttons = driver.find_elements(By.XPATH, "//*[@id='drawer-footer']/div/button[2]")
        if confirm_buttons:
            confirm_buttons[0].click()
            time.sleep(2)
    except Exception as e:
        print(f"Secondary confirm button not found or already clicked: {e}")
        pass

    return jsonify({"message": "Booking process initiated. Please enter OTP field."})


@app.route("/otp-booking", methods=["POST"])
def enter_otp():
    global driver
    try:
        data = request.json
        otp = data.get('otp')
        
        if not otp:
            return jsonify({"error": "OTP is required"}), 400
        
        if driver is None:
            return jsonify({"error": "No active session. Please start booking first."}), 400

        # Find and fill OTP field
        otp_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='disha-drawer-2']/div/div[1]/div[2]/div/div/div[1]/input"))
        )
        otp_field.clear()
        otp_field.send_keys(otp)
        time.sleep(2)

        # Click verify button
        try:
            verify_button = driver.find_element(By.XPATH, "//*[@id='disha-drawer-2']/div/div[1]/div[2]/div/div/div[2]/button[1]")
            verify_button.click()
            time.sleep(10)
            print("Booking process completed!")
        except Exception as e:
            print(f"Verify button not found or error clicking: {e}")
            pass

        return jsonify({"message": "OTP Entered, now show the payment page"}), 200
    except Exception as e:
        print(f"Error during booking OTP: {e}")
        return jsonify({"error": "Failed to submit OTP", "details": str(e)}), 500
@app.route("/show-payment-page", methods=["GET"])
def show_payment_page():
    try:
        if not driver:
            return jsonify({"error": "No active browser session"}), 400
        
        # Move browser to visible area (don't maximize, it can break some sites)
        driver.set_window_position(0, 0)
        driver.set_window_size(1920, 1080)
        
        current_url = driver.current_url
        
        return jsonify({
            "message": "Payment page is now visible",
            "current_url": current_url,
            "status": "success"
        })
    
    except Exception as e:
        print(f"Error showing payment page: {e}")
        return jsonify({
            "error": "Failed to show payment page",
            "details": str(e)
        }), 500

@app.route("/hide-browser", methods=["GET"])
def hide_browser():
    try:
        if not driver:
            return jsonify({"error": "No active browser session"}), 400
        
        # Move off-screen (don't minimize - it breaks JavaScript execution)
        # Temporarily disabled for debugging - browser will stay visible
        # driver.set_window_position(-2000, 0)
        
        return jsonify({
            "message": "Browser hidden successfully",
            "status": "success"
        })
    
    except Exception as e:
        print(f"Error hiding browser: {e}")
        return jsonify({
            "error": "Failed to hide browser",
            "details": str(e)
        }), 500
    
@app.route("/signin", methods=["POST"])
def signin():
    global driver
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({"error": "Phone number is required"}), 400
        
        print(f"Attempting to sign in with phone: {phone_number}")
        
        # Initialize driver if not already running
        if not driver:
            print("Initializing browser for sign-in...")
            driver = init_driver()
            driver.get("https://askdisha.irctc.co.in/")
            time.sleep(5)
        
        # Wait for page to load
        time.sleep(2)
        
        # Click sign-in button
        try:
            signin_button = driver.find_element(By.XPATH, "//*[@id='corover-body']/div[1]/div/div[2]/button")
            signin_button.click()
            time.sleep(3)
        except Exception as e:
            print(f"Error clicking sign-in button: {e}")
            # Try alternate sign-in button location
            signin_button = driver.find_element(By.XPATH, "//*[@id='corover-body']//button[contains(text(), 'Sign In') or contains(text(), 'Login')]")
            signin_button.click()
            time.sleep(3)
        
        # Enter phone number
        phone_input = driver.find_element(By.XPATH, "//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div/div[2]/input")
        phone_input.send_keys(phone_number)
        time.sleep(2)
        
        # Click request OTP button
        request_otp_button = driver.find_element(By.XPATH, "//*[@id='drawer-footer']/span/button")
        request_otp_button.click()
        time.sleep(3)
        
        return jsonify({
            "message": "OTP sent successfully",
            "phone_number": phone_number,
            "status": "success"
        })
    
    except Exception as e:
        print(f"Error during sign-in: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to sign in",
            "details": str(e)
        }), 500

@app.route("/ask-otp-signin", methods=["POST"])
def enter_otp_signin():
    global driver
    try:
        data = request.get_json()
        otp = data.get('otp')
        
        if not otp:
            return jsonify({"error": "OTP is required"}), 400
        
        if driver is None:
            return jsonify({"error": "No active session. Please sign in first."}), 400

        # Find and fill OTP field
        otp_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='disha-drawer-1']/div/div[1]/div[2]/div/div/div[2]/input"))
        )
        otp_field.clear()
        otp_field.send_keys(otp)
        time.sleep(2)

        # Click verify button
        try:
            verify_button = driver.find_element(By.XPATH, "//*[@id='drawer-footer']/span/button")
            verify_button.click()
            time.sleep(10)
            print("Sign-in process completed!")
        except Exception as e:
            print(f"Verify button not found or error clicking: {e}")
            # This might be okay if sign-in completes automatically
        
        return jsonify({"message": "User logged in successfully"}), 200
    
    except Exception as e:
        print(f"Error during sign-in OTP: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to complete sign-in", "details": str(e)}), 500
    
@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Chat endpoint for the AI agent
    Accepts: {"message": "user message", "session_id": "optional_session_id"}
    Returns: {"success": bool, "response": "agent response", "session_id": "session_id"}
    """
    try:
        data = request.get_json()
        message = data.get('message')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        result = chat(message, session_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "Sorry, I encountered an error processing your request."
        }), 500

@app.route("/chat/clear", methods=["POST"])
def clear_chat_history():
    """
    Clear chat history for a session
    Accepts: {"session_id": "optional_session_id"}
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        result = clear_history(session_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route("/test/cache", methods=["GET"])
def test_cache():
    """
    Test endpoint to check cache status and view sample data.
    Shows if cache is populated and displays sample train with avlDayList structure.
    """
    if not cached_train_data:
        return jsonify({
            "cache_status": "empty",
            "message": "No cached data available. Call /getTrainDetailsWithRefresh first"
        }), 200
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    
    # Collect avlDayList from first train for all classes
    sample_availability_details = []
    if trains and trains[0].get('availability'):
        for avl in trains[0]['availability'][:3]:  # First 3 classes
            sample_availability_details.append({
                "className": avl.get('className'),
                "avlDayList": avl.get('details', {}).get('avlDayList', {})
            })
    
    return jsonify({
        "cache_status": "active",
        "cached_at": cached_train_data.get('timeStamp'),
        "total_trains": len(trains),
        "sample_train": {
            "trainNumber": trains[0].get('trainNumber'),
            "trainName": trains[0].get('trainName')
        } if trains else None,
        "source_destination": {
            "from": trains[0].get('fromStnCode') if trains else None,
            "to": trains[0].get('toStnCode') if trains else None
        },
        "sample_availability_details": sample_availability_details
    })

@app.route("/test/cache/clear", methods=["POST"])
def clear_cache():
    """
    Clear the cached train data.
    Use this to reset cache and force a fresh search.
    """
    global cached_train_data
    cached_train_data = None
    return jsonify({
        "message": "Cache cleared successfully",
        "cache_status": "empty"
    })

@app.route("/test/cache/stats", methods=["GET"])
def cache_stats():
    """
    Get detailed statistics about cached train data.
    Shows breakdown by train types, classes, availability status, etc.
    """
    if not cached_train_data:
        return jsonify({
            "cache_status": "empty",
            "message": "No cached data available"
        }), 200
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    
    # Count trains by type
    train_type_counts = {}
    class_counts = {}
    available_count = 0
    waitlist_count = 0
    rac_count = 0
    
    for train in trains:
        for t_type in train.get('trainType', []):
            train_type_counts[t_type] = train_type_counts.get(t_type, 0) + 1
        
        for avl in train.get('availability', []):
            class_name = avl.get('className')
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            status = avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', '')
            if status.startswith('AVAILABLE'):
                available_count += 1
            elif 'WL' in status:
                waitlist_count += 1
            elif 'RAC' in status:
                rac_count += 1
    
    return jsonify({
        "cache_status": "active",
        "cached_at": cached_train_data.get('timeStamp'),
        "statistics": {
            "total_trains": len(trains),
            "available_seats": available_count,
            "waitlist_seats": waitlist_count,
            "rac_seats": rac_count,
            "train_types": train_type_counts,
            "class_distribution": class_counts
        },
        "route": {
            "source": trains[0].get('fromStnCode') if trains else None,
            "destination": trains[0].get('toStnCode') if trains else None
        }
    })


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)