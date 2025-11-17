"""
LangChain Tools for Train Booking Agent
Defines all API tools that the agent can use
"""
import requests
from langchain.tools import tool
from typing import Optional
import json

BACKEND_URL = "http://localhost:5000"

@tool
def search_trains(query: str) -> str:
    """
    Search for trains between two stations on a specific date.
    Use this tool when user asks to find trains or search for trains.
    
    Input should be a JSON string with format:
    {"source": "NDLS", "destination": "BCT", "date": "25-11-2025", "quota": "GN"}
    
    Args:
        query: JSON string containing source, destination, date, and optional quota
    
    Returns:
        JSON string with train details including availability
    """
    try:
        # Parse the JSON input
        params = json.loads(query)
        source = params.get("source", "").upper()
        destination = params.get("destination", "").upper()
        date = params.get("date", "")
        quota = params.get("quota", "GN").upper()
        
        if not all([source, destination, date]):
            return json.dumps({"error": "Missing required fields: source, destination, or date"})
        
        response = requests.post(
            f"{BACKEND_URL}/getTrainDetailsWithRefresh",
            json={
                "SRC": source,
                "DST": destination,
                "JDATE": date,
                "JQUOTA": quota
            },
            timeout=30
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
        response = requests.get(f"{BACKEND_URL}/trains/available", timeout=10)
        
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
        
        response = requests.get(f"{BACKEND_URL}/trains/cheapest", params=params, timeout=10)
        
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
        response = requests.get(f"{BACKEND_URL}/trains/fastest", timeout=10)
        
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
        response = requests.get(f"{BACKEND_URL}/trains/{train_number}", timeout=10)
        
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
        
        response = requests.post(f"{BACKEND_URL}/trains/filter", json=filters, timeout=10)
        
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
            timeout=10
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
        response = requests.get(f"{BACKEND_URL}/trains/summary", timeout=10)
        
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


# Note: Actual booking functionality will be added once the booking endpoint is implemented
@tool
def book_train_placeholder(train_number: str, passenger_name: str, age: int, gender: str, train_class: str) -> str:
    """
    Placeholder for train booking functionality.
    Currently, the backend booking endpoint is not yet implemented.
    
    Args:
        train_number: The train number to book
        passenger_name: Passenger's full name
        age: Passenger's age
        gender: Passenger's gender (M/F/T)
        train_class: Class to book (e.g., '3A', 'SL', '2A')
    
    Returns:
        Booking status message
    """
    return f"""Booking functionality is under development.
    
Would book:
- Train: {train_number}
- Passenger: {passenger_name} ({gender}, {age} years)
- Class: {train_class}

To complete this booking, the backend /booktrain endpoint needs to be implemented.
For now, you can:
1. Note down the train details
2. Visit IRCTC website to complete booking
3. Or wait for the booking feature to be completed"""


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
            timeout=10
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
            timeout=10
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
            timeout=60  # This scrapes live data, may take time
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
            timeout=120  # Booking may take time
        )
        
        if response.status_code == 200:
            return "✅ Booking submitted successfully! Please check IRCTC for confirmation."
        else:
            return f"❌ Booking failed with status {response.status_code}: {response.text}"
    except json.JSONDecodeError as e:
        return f"Error parsing booking data: {str(e)}"
    except Exception as e:
        return f"Error submitting booking: {str(e)}"


@tool
def close_browser(dummy: str = "") -> str:
    """
    Close the Selenium browser instance.
    Use this when user explicitly asks to close browser or when done with all operations.
    This helps free up system resources.
    
    Args:
        dummy: Not used, just for compatibility (can pass empty string or any value)
    
    Returns:
        Status message
    """
    try:
        response = requests.get(f"{BACKEND_URL}/closeBrowser", timeout=10)
        
        if response.status_code == 200:
            return "Browser closed successfully."
        else:
            return f"Error closing browser: {response.status_code}"
    except Exception as e:
        return f"Error calling close browser API: {str(e)}"
