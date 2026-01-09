import os
from dotenv import load_dotenv

load_dotenv()  # This looks for the .env file and grabs the variables
API_KEY = os.getenv('WEATHER_API_KEY')
import requests
from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='.', static_folder='.')

# Define which cities have sub-areas available
CITY_AREAS = {
    'London': ['Westminster', 'Camden', 'Greenwich', 'Brixton', 'Chelsea', 'Stratford'],
    'Manchester': ['Salford', 'Trafford', 'Didsbury', 'Cheetham Hill', 'Old Trafford'],
    'Birmingham': ['Edgbaston', 'Solihull', 'Sutton Coldfield', 'Digbeth'],
    'Leeds': ['Headingley', 'Horsforth', 'Roundhay', 'Chapel Allerton'],
    'Glasgow': ['West End', 'Govan', 'Partick', 'Hillhead'],
    'Liverpool': ['Everton', 'Toxteth', 'Aigburth', 'Anfield']
}

def get_category(condition):
    if condition in ['Thunderstorm', 'Extreme']: return 'danger'
    elif condition in ['Rain', 'Drizzle']: return 'rainy'
    elif condition == 'Clear': return 'sunny'
    elif condition == 'Clouds': return 'cloudy'
    elif condition == 'Snow': return 'snowy'
    return 'default'

def fetch_weather(query):
    """Simple helper to get weather data for a specific query string"""
    url = f'http://api.openweathermap.org/data/2.5/weather?q={query},GB&units=metric&appid={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            'name': data['name'], # The API's name for the location
            'query_name': query,  # The name we searched for
            'temp': round(data['main']['temp']),
            'desc': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'humidity': data['main']['humidity'],
            'wind': data['wind']['speed'],
            'category': get_category(data['weather'][0]['main'])
        }
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    forecast_data = []
    previous_data = []
    error_message = None
    has_areas = False # Flag to tell HTML if we should show the "View Areas" button

    if request.method == 'POST':
        city = request.form.get('city')
        
        if city:
            weather_data = fetch_weather(city)
            
            if weather_data:
                # Check if we have a list of areas for this city in our dictionary
                # We capitalize() to match keys like "London" or "Manchester"
                if city.title() in CITY_AREAS:
                    has_areas = True

                # --- 2. FUTURE FORECAST ---
                forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?q={city},GB&units=metric&appid={API_KEY}'
                f_resp = requests.get(forecast_url)
                if f_resp.status_code == 200:
                    f_data = f_resp.json()
                    for item in f_data['list']:
                        if "12:00:00" in item['dt_txt']:
                            day_name = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%A")
                            forecast_data.append({
                                'day': day_name,
                                'temp': round(item['main']['temp']),
                                'icon': item['weather'][0]['icon'],
                                'desc': item['weather'][0]['description'].title()
                            })

                # --- 3. PREVIOUS (DEMO) ---
                previous_data = [{
                    'day': (datetime.now() - timedelta(days=1)).strftime("%A"),
                    'temp': weather_data['temp'] - 2,
                    'icon': '03d',
                    'desc': 'Partly Cloudy (Demo)'
                }]
            else:
                error_message = "City not found."

    return render_template('index.html', weather=weather_data, forecast=forecast_data, previous=previous_data, error=error_message, has_areas=has_areas)

@app.route('/areas/<city_name>')
def areas(city_name):
    # Ensure the city is formatted correctly (Capitalized)
    city_key = city_name.title()
    
    if city_key not in CITY_AREAS:
        return f"No areas found for {city_key}. <a href='/'>Go Back</a>"
    
    area_list = CITY_AREAS[city_key]
    areas_weather = []

    # Loop through each area (e.g., 'Westminster', 'Camden') and get weather
    for area in area_list:
        # We search for "Westminster, London, GB" to be precise
        query = f"{area},{city_key}"
        w = fetch_weather(query)
        if w:
            w['name'] = area # Override name to be simple (e.g. just "Westminster")
            areas_weather.append(w)
            
    return render_template('areas.html', city=city_key, areas=areas_weather)

if __name__ == '__main__':
    app.run(debug=True, port=5001)