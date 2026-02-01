import requests
from datetime import datetime

def get_weather(city="Baltimore", state="MD"):
    # Baltimore, MD coordinates
    lat, lon = 39.2904, -76.6122
    
    # Open-Meteo API - free, no key needed
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode&temperature_unit=fahrenheit&timezone=America/New_York&forecast_days=3"
    
    response = requests.get(url)
    data = response.json()
    
    # Weather code descriptions
    weather_codes = {
        0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 
        3: "Overcast ☁️", 45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️",
        51: "Light drizzle 🌧️", 53: "Moderate drizzle 🌧️", 55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
        71: "Slight snow 🌨️", 73: "Moderate snow 🌨️", 75: "Heavy snow 🌨️",
        80: "Slight showers 🌦️", 81: "Moderate showers 🌦️", 82: "Violent showers ⛈️",
        95: "Thunderstorm ⛈️", 96: "Thunderstorm with hail ⛈️"
    }
    
    print(f"\n🌡️  3-Day Weather Forecast for {city}, {state}\n")
    print("-" * 45)
    
    daily = data['daily']
    for i in range(3):
        date = datetime.strptime(daily['time'][i], "%Y-%m-%d")
        day_name = date.strftime("%A, %b %d")
        high = daily['temperature_2m_max'][i]
        low = daily['temperature_2m_min'][i]
        precip = daily['precipitation_probability_max'][i]
        code = daily['weathercode'][i]
        condition = weather_codes.get(code, "Unknown")
        
        print(f"{day_name}")
        print(f"  {condition}")
        print(f"  High: {high}°F  |  Low: {low}°F")
        print(f"  Chance of precipitation: {precip}%")
        print("-" * 45)

if __name__ == "__main__":
    get_weather()
