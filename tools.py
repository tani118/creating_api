"""
LangChain Tools for Train Booking Agent
Defines all API tools that the agent can use
"""
import requests
from langchain.tools import tool
from typing import Optional
import json
from datetime import datetime

BACKEND_URL = "http://localhost:5000"

@tool
def search_trains(query: str) -> str:
    """
    Search for trains between two stations on a specific date.
    Use this tool when user asks to find trains or search for trains.
    
    IMPORTANT: Always ask the user for the quota before searching. Common quotas are:
    - GN (General) - Default for most bookings
    - TQ (Tatkal) - Last minute bookings
    - LD (Ladies) - Ladies quota
    - PT (Premium Tatkal) - Higher fare tatkal
    
    Input should be a JSON string with format:
    {"source": "NDLS", "destination": "BCT", "date": "25-11-2025", "quota": "GN"}
    
    Args:
        query: JSON string containing source, destination, date, and quota (all required)
    
    Returns:
        JSON string with train details including availability
    """
    try:
        # Parse the JSON input
        params = json.loads(query)
        source = params.get("source", "").upper()
        destination = params.get("destination", "").upper()
        date = params.get("date", "")
        quota = params.get("quota", "").upper()
        
        if not all([source, destination, date, quota]):
            return json.dumps({"error": "Missing required fields: source, destination, date, or quota. Please ask user for quota if not provided."})
        
        try:
            # Validate date format
            datetime.strptime(date, "%d-%m-%Y")
            formatted_date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y%m%d")
        except ValueError:
            return json.dumps({"error": "Invalid date format. Use DD-MM-YYYY"})

        try:
            # Validate date format
            datetime.strptime(date, "%d-%m-%Y")
            formatted_date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y%m%d")
        except ValueError:
            return json.dumps({"error": "Invalid date format. Use DD-MM-YYYY"})

        response = requests.post(
            f"{BACKEND_URL}/getTrainDetailsWithRefresh",
            json={
                "SRC": source,
                "DST": destination,
                "JDATE": formatted_date,
                "JQUOTA": quota
            },
            timeout=360
        )
        
        if response.status_code == 200:
            data = response.json()
            # Return summary for the agent
            trains = data.get('trainBtwnStnsList', [])
            summary = f"Found {len(trains)} trains from {source} to {destination} on {date}. "
            summary += f"Data cached successfully. Use get_available_trains to see trains with available seats."
            return summary
        else:
            return f"Error searching trains: {response.status_code}"
    except json.JSONDecodeError as e:
        return f"Error parsing input JSON: {str(e)}. Expected format: {{'source': 'NDLS', 'destination': 'BCT', 'date': '25-11-2025'}}"
    except Exception as e:
        return f"Error calling search API: {str(e)}"


@tool
def get_available_trains(dummy: str = "") -> str:
    """
    Get all trains that have available seats from the cached search results.
    Must call search_trains first.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        JSON string with available trains, their classes, fares, and timings
    """
    try:
        response = requests.get(f"{BACKEND_URL}/trains/available", timeout=360)
        
        if response.status_code == 200:
            data = response.json()
            trains = data.get('trains', [])
            
            if not trains:
                return "No trains with available seats found. Try different date or route."
            
            # Format for agent readability
            result = f"Found {data['count']} trains with available seats:\n\n"
            for i, train in enumerate(trains[:10], 1):  # Limit to top 10
                result += f"{i}. Train {train['trainNumber']} - {train['trainName']}\n"
                result += f"   Departure: {train['departureTime']}, Arrival: {train['arrivalTime']}\n"
                result += f"   Duration: {train['duration']}\n"
                result += f"   Available classes: "
                classes = [f"{c['class']} (₹{c['fare']})" for c in train['availableClasses'][:3]]
                result += ", ".join(classes) + "\n\n"
            
            return result
        else:
            return "Error: No train data available. Please search trains first using search_trains."
    except Exception as e:
        return f"Error getting available trains: {str(e)}"


@tool
def get_cheapest_trains(train_class: Optional[str] = None) -> str:
    """
    Get the cheapest available trains sorted by fare.
    
    Args:
        train_class: Optional - Filter by class (e.g., '3A', 'SL', '2A', '1A')
    
    Returns:
        JSON string with cheapest trains
    """
    try:
        params = {}
        if train_class:
            params['class'] = train_class.upper()
        
        response = requests.get(f"{BACKEND_URL}/trains/cheapest", params=params, timeout=360)
        
        if response.status_code == 200:
            data = response.json()
            trains = data.get('trains', [])
            
            if not trains:
                return f"No available trains found{' in ' + train_class if train_class else ''}."
            
            result = f"Top {len(trains)} cheapest trains{' in ' + train_class if train_class else ''}:\n\n"
            for i, train in enumerate(trains[:5], 1):
                result += f"{i}. Train {train['trainNumber']} - {train['trainName']}\n"
                result += f"   Class: {train['class']}, Fare: ₹{train['fare']}\n"
                result += f"   Departure: {train['departureTime']}, Arrival: {train['arrivalTime']}\n"
                result += f"   Duration: {train['duration']}\n\n"
            
            return result
        else:
            return "Error: No train data available. Please search trains first."
    except Exception as e:
        return f"Error getting cheapest trains: {str(e)}"


@tool
def get_fastest_trains(dummy: str = "") -> str:
    """
    Get the fastest trains sorted by journey duration.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    Only shows trains with available seats.
    
    Returns:
        JSON string with fastest trains
    """
    try:
        response = requests.get(f"{BACKEND_URL}/trains/fastest", timeout=360)
        
        if response.status_code == 200:
            data = response.json()
            trains = data.get('trains', [])
            
            if not trains:
                return "No trains with available seats found."
            
            result = f"Top {len(trains)} fastest trains:\n\n"
            for i, train in enumerate(trains[:5], 1):
                result += f"{i}. Train {train['trainNumber']} - {train['trainName']}\n"
                result += f"   Duration: {train['duration']}\n"
                result += f"   Departure: {train['departureTime']}, Arrival: {train['arrivalTime']}\n"
                result += f"   Type: {', '.join(train['trainType'])}\n\n"
            
            return result
        else:
            return "Error: No train data available. Please search trains first."
    except Exception as e:
        return f"Error getting fastest trains: {str(e)}"


@tool
def get_train_details(train_number: str) -> str:
    """
    Get detailed information about a specific train.
    
    Args:
        train_number: The train number (e.g., '12301', '12951')
    
    Returns:
        JSON string with complete train details including all classes and availability
    """
    try:
        response = requests.get(f"{BACKEND_URL}/trains/{train_number}", timeout=360)
        
        if response.status_code == 200:
            train = response.json()
            
            result = f"Train Details:\n"
            result += f"Number: {train.get('trainNumber')}\n"
            result += f"Name: {train.get('trainName')}\n"
            result += f"From: {train.get('fromStnCode')} at {train.get('departureTime')}\n"
            result += f"To: {train.get('toStnCode')} at {train.get('arrivalTime')}\n"
            result += f"Duration: {train.get('duration')}\n"
            result += f"Distance: {train.get('distance')} km\n"
            result += f"Type: {', '.join(train.get('trainType', []))}\n\n"
            
            result += "Available Classes:\n"
            for avl in train.get('availability', []):
                details = avl.get('details', {}).get('avlDayList', {})
                result += f"- {avl.get('className')}: {details.get('availablityStatus', 'N/A')}"
                fare = details.get('totalFare')
                if fare:
                    result += f" (₹{fare})"
                result += "\n"
            
            return result
        else:
            return f"Train {train_number} not found in cached data."
    except Exception as e:
        return f"Error getting train details: {str(e)}"


@tool
def filter_trains(
    train_type: Optional[str] = None,
    departure_after: Optional[str] = None,
    departure_before: Optional[str] = None,
    classes: Optional[str] = None,
    only_available: bool = True
) -> str:
    """
    Filter trains based on various criteria.
    
    Args:
        train_type: Filter by type (e.g., 'RAJ', 'SUPERFAST', 'EXPRESS')
        departure_after: Show trains departing after this time (HH:MM format, e.g., '18:00')
        departure_before: Show trains departing before this time (HH:MM format, e.g., '22:00')
        classes: Comma-separated class codes (e.g., '3A,2A,SL')
        only_available: Show only trains with available seats (default: True)
    
    Returns:
        JSON string with filtered trains
    """
    try:
        filters = {"onlyAvailable": only_available}
        
        if train_type:
            filters["trainType"] = [train_type.upper()]
        if departure_after:
            filters["departureAfter"] = departure_after
        if departure_before:
            filters["departureBefore"] = departure_before
        if classes:
            filters["classes"] = [c.strip().upper() for c in classes.split(',')]
        
        response = requests.post(f"{BACKEND_URL}/trains/filter", json=filters, timeout=360)
        
        if response.status_code == 200:
            data = response.json()
            trains = data.get('trains', [])
            
            if not trains:
                return "No trains match the specified filters."
            
            result = f"Found {data['count']} trains matching filters:\n\n"
            for i, train in enumerate(trains[:10], 1):
                result += f"{i}. Train {train['trainNumber']} - {train['trainName']}\n"
                result += f"   Departure: {train['departureTime']}, Arrival: {train['arrivalTime']}\n"
                result += f"   Duration: {train['duration']}, Distance: {train['distance']} km\n"
                if train.get('availableClasses'):
                    result += f"   Available: {', '.join([c['class'] for c in train['availableClasses'][:3]])}\n"
                result += "\n"
            
            return result
        else:
            return "Error filtering trains. Please search trains first."
    except Exception as e:
        return f"Error filtering trains: {str(e)}"


@tool
def get_train_route(train_number: str, journey_date: str, starting_station: str) -> str:
    """
    Get the complete route and schedule of a train.
    
    Args:
        train_number: The train number
        journey_date: Journey date in DD-MM-YYYY format
        starting_station: Starting station code
    
    Returns:
        JSON string with station-wise schedule
    """
    try:
        params = {
            "journeyDate": journey_date,
            "startingStationCode": starting_station.upper()
        }
        
        response = requests.get(
            f"{BACKEND_URL}/trains/{train_number}/route",
            params=params,
            timeout=360
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'stationList' in data:
                result = f"Route for Train {train_number}:\n\n"
                for station in data['stationList'][:10]:  # Show first 10 stations
                    result += f"{station.get('stationCode')}: "
                    result += f"Arr {station.get('arrivalTime', 'Start')}, "
                    result += f"Dep {station.get('departureTime', 'End')}\n"
                return result
            else:
                return json.dumps(data, indent=2)
        else:
            return f"Could not fetch route for train {train_number}"
    except Exception as e:
        return f"Error getting train route: {str(e)}"


@tool
def get_trains_summary(dummy: str = "") -> str:
    """
    Get a summary of all searched trains including statistics.
    Shows total trains, available seats, waitlist, RAC, train types, and available classes.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        Summary statistics of the cached train data
    """
    try:
        response = requests.get(f"{BACKEND_URL}/trains/summary", timeout=360)
        
        if response.status_code == 200:
            data = response.json()
            
            result = "Train Search Summary:\n"
            result += f"Total Trains: {data.get('totalTrains', 0)}\n"
            result += f"Available Seats: {data.get('availableSeats', 0)}\n"
            result += f"Waitlist: {data.get('waitlist', 0)}\n"
            result += f"RAC: {data.get('rac', 0)}\n\n"
            
            result += "Train Types:\n"
            for train_type, count in data.get('trainTypes', {}).items():
                result += f"- {train_type}: {count}\n"
            
            result += f"\nAvailable Classes: {', '.join(data.get('classesAvailable', []))}\n"
            
            return result
        else:
            return "Error: No train data available. Please search trains first."
    except Exception as e:
        return f"Error getting summary: {str(e)}"


@tool
def get_train_booking_options(train_number: str) -> str:
    """
    Get detailed booking options for a specific train including availability for next 5-7 days.
    Shows all quotas, classes, dates, availability status, and prices.
    Use this when user wants to see multi-day availability or prepare for booking.
    Must have searched trains first and have the browser open with train results.
    
    Args:
        train_number: The train number to get booking options for
    
    Returns:
        JSON string with availability across multiple days for all quota/class combinations
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/booktrain/{train_number}",
            timeout=360  # This scrapes live data, may take time
        )
        
        if response.status_code == 200:
            data = response.json()
            result = f"Booking options for Train {train_number}:\n\n"
            
            for quota, classes in data.get('available_quotas', {}).items():
                result += f"📋 Quota: {quota}\n"
                for class_name, days in classes.items():
                    result += f"  🎫 Class: {class_name}\n"
                    for day in days[:5]:  # Show first 5 days
                        result += f"    📅 {day['date']}: {day['availability']} - {day['price']}\n"
                    result += "\n"
            
            return result
        else:
            return f"Error fetching booking options: {response.status_code}. Make sure you've searched for trains first."
    except Exception as e:
        return f"Error calling booking options API: {str(e)}"


@tool
def book_train(booking_data: str) -> str:
    """
    Submit train booking with passenger details.
    Use this ONLY when user explicitly confirms they want to book and provides ALL required details.
    
    IMPORTANT: You must collect ALL these details from the user before calling this tool:
    - Train number
    - Quota (e.g., "General", "Tatkal", "Ladies")
    - Class (e.g., "3A", "2A", "SL", "CC")
    - Journey date (format: "DD Mon" like "20 Nov")
    - Passenger details for EACH passenger:
      * Name (full name)
      * Age (number)
      * Gender ("Male", "Female", "Transgender")
      * Berth preference (optional: "Lower", "Middle", "Upper", "Side Lower", "Side Upper")
      * Food preference (optional: "Vegetarian", "Non Vegetarian")
    
    Input should be JSON string with format:
    {
        "train_number": "12345",
        "quota": "General",
        "class": "3A",
        "journey_date": "20 Nov",
        "passenger_details": [
            {
                "name": "John Doe",
                "age": 30,
                "gender": "Male",
                "berth_preference": "Lower",
                "food_preference": "Vegetarian"
            }
        ]
    }
    
    Args:
        booking_data: JSON string with complete booking information
    
    Returns:
        Booking status message
    """
    try:
        params = json.loads(booking_data)
        
        # Validate required fields
        required_fields = ['train_number', 'quota', 'class', 'journey_date', 'passenger_details']
        missing_fields = [f for f in required_fields if f not in params]
        
        if missing_fields:
            return f"❌ Missing required fields: {', '.join(missing_fields)}"
        
        # Validate passenger details
        passengers = params.get('passenger_details', [])
        if not passengers:
            return "❌ At least one passenger is required"
        
        for i, passenger in enumerate(passengers, 1):
            required_passenger_fields = ['name', 'age', 'gender']
            missing_passenger_fields = [f for f in required_passenger_fields if f not in passenger]
            
            if missing_passenger_fields:
                return f"❌ Passenger {i} missing fields: {', '.join(missing_passenger_fields)}"
            
            # Validate gender
            valid_genders = ['Male', 'Female', 'Transgender']
            if passenger['gender'] not in valid_genders:
                return f"❌ Invalid gender for passenger {i}. Must be one of: {', '.join(valid_genders)}"
            
            # Validate age
            try:
                age = int(passenger['age'])
                if age < 1 or age > 120:
                    return f"❌ Invalid age for passenger {i}. Must be between 1 and 120"
            except (ValueError, TypeError):
                return f"❌ Invalid age format for passenger {i}. Must be a number"
        
        # Make the booking request
        response = requests.post(
            f"{BACKEND_URL}/booktrain/",
            json=params,
            timeout=360  # Booking may take time
        )
        
        if response.status_code == 200:
            result = "✅ Booking process initiated successfully!\n\n"
            result += "📋 Booking Summary:\n"
            result += f"Train: {params['train_number']}\n"
            result += f"Quota: {params['quota']}\n"
            result += f"Class: {params['class']}\n"
            result += f"Date: {params['journey_date']}\n\n"
            result += f"Passengers ({len(passengers)}):\n"
            for i, p in enumerate(passengers, 1):
                result += f"{i}. {p['name']} ({p['gender']}, {p['age']} years)\n"
            result += "\n⚠️ IMPORTANT: The booking form has been filled on the IRCTC website."
            result += "\nPlease review the details on the screen and complete the payment process manually."
            result += "\nDo NOT close the browser window."
            return result
        else:
            error_text = response.text if response.text else "Unknown error"
            return f"❌ Booking failed with status {response.status_code}: {error_text}\n\nMake sure you've searched for trains first and the browser is open."
    
    except json.JSONDecodeError as e:
        return f"❌ Error parsing booking data: {str(e)}\n\nExpected JSON format with train_number, quota, class, journey_date, and passenger_details"
    except requests.exceptions.Timeout:
        return "❌ Booking request timed out. The process might still be running. Please check the browser."
    except Exception as e:
        return f"❌ Error submitting booking: {str(e)}"



@tool
def get_trains_by_class(class_code: str) -> str:
    """
    Get all trains that have available seats in a specific class.
    Use this when user asks for trains in specific class like "3AC", "2AC", "Sleeper", etc.
    Must call search_trains first.
    
    Args:
        class_code: Class code like "3A", "2A", "SL", "CC", "2S", "1A"
    
    Returns:
        JSON string with trains having the specified class available
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/trains/by-class/{class_code.upper()}",
            timeout=360
        )
        
        if response.status_code == 200:
            data = response.json()
            trains = data.get('trains', [])
            
            if not trains:
                return f"No trains found with {class_code} class available."
            
            result = f"Found {len(trains)} trains with {class_code} class:\n\n"
            for i, train in enumerate(trains[:10], 1):
                result += f"{i}. Train {train['trainNumber']} - {train['trainName']}\n"
                result += f"   Departure: {train['departureTime']} | Arrival: {train['arrivalTime']}\n"
                result += f"   Duration: {train['duration']} | Status: {train['status']}\n"
                result += f"   Fare: ₹{train['fare']}\n\n"
            
            return result
        else:
            return f"Error fetching trains by class: {response.status_code}"
    except Exception as e:
        return f"Error calling API: {str(e)}"


@tool
def get_trains_by_type(train_type: str) -> str:
    """
    Get trains filtered by train type.
    Use when user asks for specific train types like Express, Superfast, Mail, Rajdhani, etc.
    Must call search_trains first.
    
    Args:
        train_type: Type code like "EXP" (Express), "SF" (Superfast), "MAIL", "RAJ" (Rajdhani), "SHT" (Shatabdi), "DUR" (Duronto)
    
    Returns:
        JSON string with trains of the specified type
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/trains/by-type/{train_type.upper()}",
            timeout=360
        )
        
        if response.status_code == 200:
            data = response.json()
            trains = data.get('trains', [])
            
            if not trains:
                return f"No {train_type} trains found."
            
            result = f"Found {len(trains)} {train_type} trains:\n\n"
            for i, train in enumerate(trains[:15], 1):
                result += f"{i}. Train {train['trainNumber']} - {train['trainName']}\n"
                result += f"   Departure: {train['departureTime']} | Arrival: {train['arrivalTime']}\n"
                result += f"   Duration: {train['duration']}\n"
                result += f"   Types: {', '.join(train.get('trainType', []))}\n\n"
            
            return result
        else:
            return f"Error fetching trains by type: {response.status_code}"
    except Exception as e:
        return f"Error calling API: {str(e)}"


@tool
def get_train_booking_options(train_number: str) -> str:
    """
    Get detailed booking options for a specific train including availability for next 5-7 days.
    Shows all quotas, classes, dates, availability status, and prices.
    Use this when user wants to see multi-day availability or prepare for booking.
    Must call search_trains first to load the train data.
    
    Args:
        train_number: The train number to get booking options for
    
    Returns:
        JSON string with availability across multiple days for all quota/class combinations
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/booktrain/{train_number}",
            timeout=360  # This scrapes live data, may take time
        )
        
        if response.status_code == 200:
            data = response.json()
            result = f"Booking options for Train {train_number}:\n\n"
            
            for quota, classes in data.get('available_quotas', {}).items():
                result += f"📋 Quota: {quota}\n"
                for class_name, days in classes.items():
                    result += f"  🎫 Class: {class_name}\n"
                    for day in days[:5]:  # Show first 5 days
                        result += f"    📅 {day['date']}: {day['availability']} - {day['price']}\n"
                    result += "\n"
            
            return result
        else:
            return f"Error fetching booking options: {response.status_code}"
    except Exception as e:
        return f"Error calling booking options API: {str(e)}"


@tool
def book_train_submit(booking_data: str) -> str:
    """
    Submit actual train booking with passenger details.
    Use this ONLY when user explicitly confirms they want to book and provides all required details.
    
    Input should be JSON string with format:
    {
        "train_number": "12345",
        "quota": "General",
        "class": "3A",
        "journey_date": "25-11-2025",
        "passenger_details": [
            {"name": "John Doe", "age": 30, "gender": "Male", "berth_preference": "Lower", "food_preference": "Vegetarian"}
        ]
    }
    
    Args:
        booking_data: JSON string with complete booking information
    
    Returns:
        Booking confirmation or error message
    """
    try:
        params = json.loads(booking_data)
        
        response = requests.post(
            f"{BACKEND_URL}/booktrain/",
            json=params,
            timeout=360  # Booking may take time
        )
        
        if response.status_code == 200:
            return "✅ Booking initiated successfully! An OTP has been sent to the registered mobile number. Please ask the user to provide the OTP to complete the booking."
        else:
            return f"❌ Booking failed with status {response.status_code}: {response.text}"
    except json.JSONDecodeError as e:
        return f"Error parsing booking data: {str(e)}"
    except Exception as e:
        return f"Error submitting booking: {str(e)}"


@tool
def submit_booking_otp(otp: str) -> str:
    """
    Submit OTP for booking confirmation.
    Use this after booking is initiated and user provides the OTP they received.
    
    Args:
        otp: The OTP code received by user (usually 6 digits)
    
    Returns:
        Status message about OTP submission
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/otp-booking",
            json={"otp": otp},
            timeout=360
        )
        
        if response.status_code == 200:
            return "✅ OTP submitted successfully! Payment page should be visible now."
        else:
            return f"❌ Error submitting OTP: {response.status_code}"
    except Exception as e:
        return f"❌ Error calling OTP API: {str(e)}"

@tool
def get_city_stations(city_name: str) -> str:
    """
    Get list of railway stations for a given city name.
    
    Args:
        city_name: Name of the city to search stations for (e.g., "Delhi", "Mumbai", "Bangalore")

    Returns:
        Formatted string with list of stations in the city
    """
    try:
        # Load the JSON file
        import os
        json_path = os.path.join(os.path.dirname(__file__), 'indian_railway_stations.json')
        
        with open(json_path, 'r') as f:
            stations_data = json.load(f)
        
        # Search for city (case-insensitive)
        city_key = None
        for key in stations_data.keys():
            if key.lower() == city_name.lower():
                city_key = key
                break
        
        if not city_key:
            # Try partial match
            for key in stations_data.keys():
                if city_name.lower() in key.lower() or key.lower() in city_name.lower():
                    city_key = key
                    break
        
        if not city_key:
            return f"❌ No stations found for city: {city_name}\n\nAvailable cities: {', '.join(list(stations_data.keys())[:20])}..."
        
        stations = stations_data[city_key]
        
        if not stations:
            return f"No stations found for city: {city_key}"
        
        result = f"🚉 Stations in {city_key}:\n\n"
        for i, (code, name) in enumerate(stations.items(), 1):
            result += f"{i}. {code} - {name}\n"
        
        return result
    except FileNotFoundError:
        return "❌ Error: indian_railway_stations.json file not found"
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON format in stations file"
    except Exception as e:
        return f"❌ Error reading stations data: {str(e)}"

@tool
def show_payment_page(dummy: str = "") -> str:
    """
    Make the browser window visible to user for payment.
    Use this after OTP is submitted so user can complete payment on IRCTC.
    The browser will maximize and move to screen.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        Status message about browser visibility
    """
    try:
        response = requests.get(f"{BACKEND_URL}/show-payment-page", timeout=360)
        
        if response.status_code == 200:
            data = response.json()
            return f"✅ Payment page is now visible! Current URL: {data.get('current_url', 'N/A')}\n\nPlease complete the payment process on the browser window."
        else:
            return f"❌ Error showing payment page: {response.status_code}"
    except Exception as e:
        return f"❌ Error calling show payment API: {str(e)}"


@tool
def hide_browser(dummy: str = "") -> str:
    """
    Hide the browser window from view.
    Use this if user wants to minimize the browser during background operations.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        Status message
    """
    try:
        response = requests.get(f"{BACKEND_URL}/hide-browser", timeout=360)
        
        if response.status_code == 200:
            return "✅ Browser hidden successfully."
        else:
            return f"❌ Error hiding browser: {response.status_code}"
    except Exception as e:
        return f"❌ Error calling hide browser API: {str(e)}"


@tool
def signin_user(phone_number: str) -> str:
    """
    Sign in user with phone number. Sends OTP to the provided number.
    Input: phone number as string (e.g., "9876543210")
    """
    import requests
    import json
    
    # First, ensure browser is initialized
    try:
        init_response = requests.get(f"{BACKEND_URL}/init-browser")
        if init_response.status_code != 200:
            init_data = init_response.json()
            if init_data.get("status") != "already_initialized":
                return f"❌ Failed to initialize browser: {init_data.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ Error initializing browser: {str(e)}"
    
    # Now attempt sign-in
    try:
        response = requests.post(
            f"{BACKEND_URL}/signin",
            json={"phone_number": phone_number},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return f"✅ OTP sent to {phone_number}. Please provide the OTP to complete sign-in."
        else:
            error_data = response.json()
            return f"❌ Error signing in: {error_data.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ Error signing in: {str(e)}"


@tool
def submit_signin_otp(otp: str) -> str:
    """
    Submit OTP for IRCTC sign-in verification.
    Use this after signin_user when user provides the OTP they received.
    
    Args:
        otp: The OTP code received by user (usually 6 digits)
    
    Returns:
        Status message about sign-in completion
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask-otp-signin",
            json={"otp": otp},
            timeout=360
        )
        
        if response.status_code == 200:
            return "✅ Successfully signed in to IRCTC account!"
        else:
            return f"❌ Error submitting sign-in OTP: {response.status_code}"
    except Exception as e:
        return f"❌ Error calling signin OTP API: {str(e)}"


@tool
def reset_browser(dummy: str = "") -> str:
    """
    Reset the browser to initial state - clears cache and navigates back to home page.
    Use this tool when:
    - An error occurs during train search or booking
    - User asks to "try again" or "start over"
    - Browser is on wrong page and needs to be reset
    - Need to clear previous search data before a new search
    
    This tool will:
    - Clear cached train data
    - Clear request history
    - Navigate back to IRCTC home page
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        Status message
    """
    try:
        response = requests.get(f"{BACKEND_URL}/tryagain", timeout=60)
        
        if response.status_code == 200:
            return "Browser reset successfully. Cache cleared. Ready for new search."
        else:
            return f"Error resetting browser: {response.status_code}"
    except Exception as e:
        return f"Failed to reset browser: {str(e)}"

@tool
def close_browser(dummy: str = "") -> str:
    """
    Close the Selenium browser instance completely.
    Use this when user explicitly asks to close browser or when done with all operations.
    This helps free up system resources.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        Status message
    """
    try:
        response = requests.get(f"{BACKEND_URL}/closeBrowser", timeout=360)
        
        if response.status_code == 200:
            return "Browser closed successfully."
        else:
            return f"Error closing browser: {response.status_code}"
    except Exception as e:
        return f"Error calling close browser API: {str(e)}"
