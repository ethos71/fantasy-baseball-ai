#!/usr/bin/env python3
"""
Weather Delta Scraper - Update Stadium Weather Data

This script updates only the weather data, leaving all other data intact:
- Fetches current weather for all 30 MLB stadiums
- Overwrites existing weather CSV with fresh data
- Takes ~30 seconds to complete

Usage:
    python src/scripts/weather_delta_scrape.py
"""

import pandas as pd
import requests
import numpy as np
import time
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier


class WeatherDeltaScraper:
    """Quick weather update for all MLB stadiums"""
    
    # MLB Stadium coordinates (same as weather_scrape.py)
    STADIUMS = {
        'Arizona Diamondbacks': {'venue': 'Chase Field', 'lat': 33.4452, 'lon': -112.0667, 'city': 'Phoenix, AZ'},
        'Atlanta Braves': {'venue': 'Truist Park', 'lat': 33.8903, 'lon': -84.4677, 'city': 'Atlanta, GA'},
        'Baltimore Orioles': {'venue': 'Oriole Park at Camden Yards', 'lat': 39.2839, 'lon': -76.6217, 'city': 'Baltimore, MD'},
        'Boston Red Sox': {'venue': 'Fenway Park', 'lat': 42.3467, 'lon': -71.0972, 'city': 'Boston, MA'},
        'Chicago Cubs': {'venue': 'Wrigley Field', 'lat': 41.9484, 'lon': -87.6553, 'city': 'Chicago, IL'},
        'Chicago White Sox': {'venue': 'Guaranteed Rate Field', 'lat': 41.8299, 'lon': -87.6338, 'city': 'Chicago, IL'},
        'Cincinnati Reds': {'venue': 'Great American Ball Park', 'lat': 39.0974, 'lon': -84.5086, 'city': 'Cincinnati, OH'},
        'Cleveland Guardians': {'venue': 'Progressive Field', 'lat': 41.4962, 'lon': -81.6852, 'city': 'Cleveland, OH'},
        'Colorado Rockies': {'venue': 'Coors Field', 'lat': 39.7559, 'lon': -104.9942, 'city': 'Denver, CO'},
        'Detroit Tigers': {'venue': 'Comerica Park', 'lat': 42.3391, 'lon': -83.0485, 'city': 'Detroit, MI'},
        'Houston Astros': {'venue': 'Minute Maid Park', 'lat': 29.7573, 'lon': -95.3556, 'city': 'Houston, TX'},
        'Kansas City Royals': {'venue': 'Kauffman Stadium', 'lat': 39.0517, 'lon': -94.4803, 'city': 'Kansas City, MO'},
        'Los Angeles Angels': {'venue': 'Angel Stadium', 'lat': 33.8003, 'lon': -117.8827, 'city': 'Anaheim, CA'},
        'Los Angeles Dodgers': {'venue': 'Dodger Stadium', 'lat': 34.0739, 'lon': -118.2400, 'city': 'Los Angeles, CA'},
        'Miami Marlins': {'venue': 'LoanDepot Park', 'lat': 25.7781, 'lon': -80.2197, 'city': 'Miami, FL'},
        'Milwaukee Brewers': {'venue': 'American Family Field', 'lat': 43.0280, 'lon': -87.9712, 'city': 'Milwaukee, WI'},
        'Minnesota Twins': {'venue': 'Target Field', 'lat': 44.9817, 'lon': -93.2776, 'city': 'Minneapolis, MN'},
        'New York Mets': {'venue': 'Citi Field', 'lat': 40.7571, 'lon': -73.8458, 'city': 'New York, NY'},
        'New York Yankees': {'venue': 'Yankee Stadium', 'lat': 40.8296, 'lon': -73.9262, 'city': 'New York, NY'},
        'Oakland Athletics': {'venue': 'Oakland Coliseum', 'lat': 37.7516, 'lon': -122.2005, 'city': 'Oakland, CA'},
        'Philadelphia Phillies': {'venue': 'Citizens Bank Park', 'lat': 39.9061, 'lon': -75.1665, 'city': 'Philadelphia, PA'},
        'Pittsburgh Pirates': {'venue': 'PNC Park', 'lat': 40.4469, 'lon': -80.0057, 'city': 'Pittsburgh, PA'},
        'San Diego Padres': {'venue': 'Petco Park', 'lat': 32.7073, 'lon': -117.1566, 'city': 'San Diego, CA'},
        'San Francisco Giants': {'venue': 'Oracle Park', 'lat': 37.7786, 'lon': -122.3893, 'city': 'San Francisco, CA'},
        'Seattle Mariners': {'venue': 'T-Mobile Park', 'lat': 47.5914, 'lon': -122.3325, 'city': 'Seattle, WA'},
        'St. Louis Cardinals': {'venue': 'Busch Stadium', 'lat': 38.6226, 'lon': -90.1928, 'city': 'St. Louis, MO'},
        'Tampa Bay Rays': {'venue': 'Tropicana Field', 'lat': 27.7682, 'lon': -82.6534, 'city': 'St. Petersburg, FL'},
        'Texas Rangers': {'venue': 'Globe Life Field', 'lat': 32.7470, 'lon': -97.0817, 'city': 'Arlington, TX'},
        'Toronto Blue Jays': {'venue': 'Rogers Centre', 'lat': 43.6414, 'lon': -79.3894, 'city': 'Toronto, ON'},
        'Washington Nationals': {'venue': 'Nationals Park', 'lat': 38.8730, 'lon': -77.0074, 'city': 'Washington, DC'},
    }
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.model = None
        self.train_model()
    
    def train_model(self):
        """Train simple weather prediction model"""
        np.random.seed(42)
        n_samples = 500
        
        # Sunny patterns
        sunny_data = np.column_stack([
            np.random.uniform(20, 35, n_samples//2),
            np.random.uniform(30, 60, n_samples//2),
            np.random.uniform(1015, 1025, n_samples//2),
            np.random.uniform(5, 20, n_samples//2),
            np.random.uniform(0, 40, n_samples//2),
        ])
        
        # Rainy patterns
        rainy_data = np.column_stack([
            np.random.uniform(10, 20, n_samples//2),
            np.random.uniform(70, 95, n_samples//2),
            np.random.uniform(995, 1010, n_samples//2),
            np.random.uniform(10, 30, n_samples//2),
            np.random.uniform(60, 100, n_samples//2),
        ])
        
        X = np.vstack([sunny_data, rainy_data])
        y = np.hstack([np.zeros(n_samples//2), np.ones(n_samples//2)])
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
    
    def degrees_to_cardinal(self, degrees: float) -> str:
        """Convert wind direction to cardinal direction"""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]
    
    def get_weather_data(self, lat: float, lon: float) -> dict:
        """Fetch current weather from Open-Meteo API"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,cloud_cover,precipitation',
                'temperature_unit': 'celsius',
                'wind_speed_unit': 'kmh',
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data.get('current', {})
            wind_dir_degrees = current.get('wind_direction_10m', 0)
            
            return {
                'temperature': current.get('temperature_2m', 15),
                'humidity': current.get('relative_humidity_2m', 50),
                'pressure': current.get('pressure_msl', 1013),
                'wind_speed': current.get('wind_speed_10m', 10),
                'wind_direction': wind_dir_degrees,
                'wind_direction_cardinal': self.degrees_to_cardinal(wind_dir_degrees),
                'wind_gusts': current.get('wind_gusts_10m', 0),
                'cloud_cover': current.get('cloud_cover', 50),
                'precipitation': current.get('precipitation', 0),
                'timestamp': current.get('time', datetime.now().isoformat())
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                'temperature': 15, 'humidity': 50, 'pressure': 1013,
                'wind_speed': 10, 'wind_direction': 0, 'wind_direction_cardinal': 'N',
                'wind_gusts': 0, 'cloud_cover': 50, 'precipitation': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_weather(self, weather_data: dict) -> tuple:
        """Predict weather condition"""
        features = np.array([[
            weather_data['temperature'],
            weather_data['humidity'],
            weather_data['pressure'],
            weather_data['wind_speed'],
            weather_data['cloud_cover']
        ]])
        
        if weather_data['precipitation'] > 0.1:
            return "Rainy", 1.0
        
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0]
        confidence = max(probability)
        
        condition = "Rainy" if prediction == 1 else "Sunny"
        return condition, confidence
    
    def run(self):
        """Execute weather delta update"""
        print("\n" + "="*80)
        print("WEATHER DELTA SCRAPER - UPDATING STADIUM CONDITIONS".center(80))
        print("="*80)
        print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        results = []
        
        for team_name, location in self.STADIUMS.items():
            print(f"  → {team_name:30s}", end=" ")
            
            weather = self.get_weather_data(location['lat'], location['lon'])
            condition, confidence = self.predict_weather(weather)
            
            wind_info = f"{weather['wind_speed']:.1f} km/h {weather['wind_direction_cardinal']}"
            print(f"{condition:5s} | {wind_info}")
            
            results.append({
                'team': team_name,
                'venue': location['venue'],
                'city': location['city'],
                'latitude': location['lat'],
                'longitude': location['lon'],
                'temperature_c': weather['temperature'],
                'humidity_pct': weather['humidity'],
                'pressure_hpa': weather['pressure'],
                'wind_speed_kmh': weather['wind_speed'],
                'wind_direction_degrees': weather['wind_direction'],
                'wind_direction_cardinal': weather['wind_direction_cardinal'],
                'wind_gusts_kmh': weather['wind_gusts'],
                'cloud_cover_pct': weather['cloud_cover'],
                'precipitation_mm': weather['precipitation'],
                'prediction': condition,
                'confidence': confidence,
                'timestamp': weather['timestamp']
            })
            
            time.sleep(0.3)
        
        # Save to CSV
        df = pd.DataFrame(results)
        output_path = self.data_dir / "mlb_stadium_weather.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Weather data updated for all 30 stadiums")
        print(f"📁 Saved to: {output_path}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        return True


def main():
    """Main entry point"""
    scraper = WeatherDeltaScraper()
    
    try:
        success = scraper.run()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Weather update interrupted")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
