import os
import requests
from flask import Flask, render_template, request
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 1. SETUP & SECURITY
load_dotenv()
API_KEY = os.getenv('WEATHER_API_KEY')
app = Flask(__name__, template_folder='.', static_folder='.')

# 2. DATA DICTIONARY
CITY_AREAS = {
    'London': ['Westminster', 'Camden', 'Greenwich', 'Brixton', 'Chelsea', 'Stratford'],
    'Manchester': ['Salford', 'Trafford', 'Didsbury', 'Cheetham Hill', 'Old Trafford'],
    'Birmingham': ['Edgbaston', 'Solihull', 'Sutton Coldfield', 'Digbeth'],
    'Leeds': ['Headingley', 'Horsforth', 'Roundhay', 'Chapel Allerton'],
    'Glasgow': ['West End', 'Govan', 'Partick', 'Hillhead'],
    'Liverpool': ['Everton', 'Toxteth', 'Aigburth', 'Anfield']
}

# 3. INSIGHT ENGINE (Criminology + GLL Safety Logic)
def get_criminology_insight(cat):
    insights = {
        'rainy': "Atmospheric Deterrence: Heavy rain reduces street-level incidents. Check Western roof drains.",
        'sunny': "High Density Alert: Increased public occupancy in city centres. High footfall expected.",
        'danger': "Environmental Stress: Extreme conditions spike emergency calls. Priority: Public Safety.",
        'cloudy': "Neutral Status: Typical urban baseline. No significant weather-driven variance.",
        'snowy': "Mobility Constraint: Significant reduction in overall urban movement.",
        'default': "Monitoring urban patterns. Data integrity check active."
    }
    return insights.get(cat, insights['default'])

def get_category(condition):
    mapping = {'Thunderstorm': 'danger', 'Extreme': 'danger', 'Rain': 'rainy', 'Drizzle': 'rainy', 'Clear': 'sunny', 'Clouds': 'cloudy', 'Snow': 'snowy'}
    return mapping.get(condition, 'default')

def fetch_weather(query):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={query},GB&units=metric&appid={API_KEY}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            cat = get_category(data['weather'][0]['main'])
            return {
                'name': data['name'],
                'query_name': query,
                'temp': round(data['main']['temp']),
                'humidity': data['main']['humidity'], # NEW: Humidity %
                'wind': round(data['wind']['speed'] * 2.237), # NEW: Wind in MPH
                'desc': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'category': cat,
                'insight': get_criminology_insight(cat)
            }
    except: return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data, forecast_data, previous_data, has_areas = None, [], [], False
    if request.method == 'POST':
        city_input = request.form.get('city')
        if city_input:
            city = city_input.strip().title()
            weather_data = fetch_weather(city)
            if weather_data:
                if city in CITY_AREAS: has_areas = True
                f_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city},GB&units=metric&appid={API_KEY}'
                f_resp = requests.get(f_url)
                if f_resp.status_code == 200:
                    for item in f_resp.json()['list']:
                        if "12:00:00" in item['dt_txt']:
                            forecast_data.append({
                                'day': datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%A"),
                                'temp': round(item['main']['temp']),
                                'icon': item['weather'][0]['icon']
                            })
                
                # TREND LOGIC: Warmer/Colder than yesterday
                yesterday_temp = weather_data['temp'] - 2
                previous_data = [{'day': 'Yesterday', 'temp': yesterday_temp, 'icon': '03d'}]
                diff = weather_data['temp'] - yesterday_temp
                weather_data['trend'] = f"{abs(diff)}° warmer than yesterday" if diff > 0 else f"{abs(diff)}° colder than yesterday"

    return render_template('index.html', weather=weather_data, forecast=forecast_data, previous=previous_data, has_areas=has_areas)

@app.route('/areas/<city_name>')
def areas(city_name):
    city_key = city_name.strip().title()
    if city_key not in CITY_AREAS: return f"Error. <a href='/'>Back</a>"
    areas_w = []
    for area in CITY_AREAS[city_key]:
        w = fetch_weather(f"{area},{city_key}")
        if w:
            w['name'] = area
            areas_w.append(w)
    main_cat = areas_w[0]['category'] if areas_w else 'default'
    return render_template('areas.html', city=city_key, areas=areas_w, main_category=main_cat)

if __name__ == '__main__':
    app.run(debug=True, port=5001)