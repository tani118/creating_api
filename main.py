from seleniumwire import webdriver as seleniumwire_webdriver 
from selenium.webdriver.common.by import By
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import date, timedelta, datetime
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

def init_driver():
    global driver
    if driver is None:
        options = seleniumwire_webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        driver = seleniumwire_webdriver.Chrome(options=options)
    return driver

@app.route("/closeBrowser", methods=["GET"])
def closeBrowser():
    global driver
    if driver:
        driver.quit()
        driver = None
        return jsonify({"message": "Browser closed successfully"}), 200
    return jsonify({"message": "Browser was not running"}), 200

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
                return jsonify(response_json)
    
    return jsonify({"status": 500, "message": "No response captured"}), 500

@app.route("/trains/available", methods=["GET"])
def get_available_trains():
    if not cached_train_data:
        return jsonify({"error": "No train data available. Call /getTrainDetailsWithRefresh first"}), 400
    
    trains = cached_train_data.get('trainBtwnStnsList', [])
    available_trains = []
    
    for train in trains:
        has_availability = any(
            avl.get('details', {}).get('avlDayList', {}).get('availablityStatus', '').startswith('AVAILABLE')
            for avl in train.get('availability', [])
        )
        
        if has_availability:
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
    

@app.route("/booktrain/<train_number>", methods=["GET"])
def book_train(train_number):
    details = {
        "trainNumber": train_number,
        "available_quotas": {}
    }

    train_div = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-gplwa-d') and .//p[contains(text(), '{train_number}')]]")
    time.sleep(2)
    train_div.find_element(By.XPATH, ".//div[contains(@class, 'ticket-new')]").click()
    time.sleep(5)

    quota_section = driver.find_element(By.XPATH, "//p[text()='Quota']/following-sibling::div")
    quota_divs = quota_section.find_elements(By.XPATH, "./div")
    available_quotas = [quota_div.text for quota_div in quota_divs]
    
    for quota_div in quota_divs:
        quota_name = quota_div.text
        quota_div.click()
        time.sleep(5)
        
        details["available_quotas"][quota_name] = {}
        
        class_section = driver.find_element(By.XPATH, "//p[text()='Class']/following-sibling::div")
        class_divs = class_section.find_elements(By.XPATH, "./div")
        
        for class_div in class_divs:
            class_name = class_div.text
            class_div.click()
            time.sleep(5)

            day_data = []
            daylist_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'day')]")

            for day_div in daylist_divs:
                date_element = day_div.find_element(By.XPATH, ".//p[contains(@style, 'font-weight: 600')]")
                date_text = date_element.text
                
                availability_element = day_div.find_element(By.XPATH, ".//p[contains(@style, 'color: rgb(165, 164, 166)') or contains(@style, 'font-weight: 600')]")
                availability_text = availability_element.text
                
                availability_element.click()
                time.sleep(3)
                price_element = driver.find_element(By.XPATH, "//span[contains(@style, 'font-size: 20px; font-weight: 600; color: rgb(42, 42, 42)')]")
                price_text = price_element.text

                day_data.append({
                    "date": date_text,
                    "availability": availability_text,
                    "price": price_text
                })
            
            details["available_quotas"][quota_name][class_name] = day_data
    
    return jsonify(details)

@app.route("/booktrain/", methods=["POST"])
def book_train():
    data = request.get_json()
    train_number = data.get('train_number')
    quota = data.get('quota')
    travel_class = data.get('class')
    journey_date = data.get('journey_date')

    passenger_details = data.get('passenger_details')

    train_div = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-gplwa-d') and .//p[contains(text(), '{train_number}')]]")
    time.sleep(2)
    train_div.find_element(By.XPATH, ".//div[contains(@class, 'ticket-new')]").click()
    time.sleep(5)

    quota_div = driver.find_element(By.XPATH, f"//div[.//text()[contains(., '{quota}')]]")
    quota_div.click()
    time.sleep(5)
    
    class_div = driver.find_element(By.XPATH, f"//div[.//text()[contains(., '{travel_class}')]]")
    class_div.click()
    time.sleep(5)
    
    date_div = driver.find_element(By.XPATH, f"//div[.//p[contains(text(), '{journey_date}')]]")
    date_div.click()
    time.sleep(3)

    book_button = driver.find_element(By.XPATH, f"//button[contains(text(), 'BOOK TICKET')]")
    book_button.click()
    time.sleep(3)

    confirm_button = driver.find_element(By.XPATH, f"//button[contains(text(), 'Confirm')]")
    confirm_button.click()
    time.sleep(15)

    c = 0
    for passenger in passenger_details:
        if(c == 1):
            driver.find_element(By.XPATH, "//button[contains(text(), 'Add Passenger')]").click()
            time.sleep(3)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Add Passenger')]").click()
            time.sleep(3)
        gender = passenger.get('gender')
        driver.find_element(By.XPATH, f"//div[contains(text(), '{gender}')]").click()
        driver.find_element(By.ID, "name").send_keys(passenger.get('name'))
        driver.find_element(By.ID, "age").send_keys(str(passenger.get('age')))

    try:
        if(passenger.get('food_preference') == "Non Vegetarian"):
            driver.find_element(By.XPATH, "//div[contains(text(), 'Non Vegetarian')]").click()
            time.sleep(3)
            driver.find_element(By.XPATH, "//div[contains(text(), 'Non Vegetarian')]").click()
            time.sleep(2)
    except Exception as e:
        print(f"Error occurred: {e}")
        pass

    try:
        if(passenger.get('berth_preference')):
            driver.find_element(By.XPATH, f"//div[contains(text(), 'berth_preference']").click()
            time.sleep(3)
            driver.find_element(By.XPATH, f"//div[contains(text(), '{passenger.get('berth_preference')}')]").click()
            time.sleep(2)

    except Exception as e:
        print(f"Error occurred: {e}")
        pass
    driver.find_element(By.XPATH, "//button[contains(text(), 'Review Journey')]").click()


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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)