"""
MLB Stadium Weather Predictor
Based on: https://github.com/FELIX-GEORGE/WeatherPrediction_ML_Model

This script fetches current weather data for all MLB stadium locations
and uses machine learning to predict weather conditions (Rainy/Sunny).
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from typing import Dict, List, Tuple
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import os


class MLBWeatherPredictor:
    """Weather prediction for MLB stadiums"""
    
    # MLB Stadium coordinates (latitude, longitude)
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
        self.model = None
        self.wind_encoder = LabelEncoder()
        self.train_simple_model()
    
    def train_simple_model(self):
        """Train a simple weather prediction model"""
        print("Training weather prediction model...")
        
        # Simple training data based on weather patterns
        # Features: [temp, humidity, pressure, wind_speed, cloud_cover]
        # 1 = Rainy, 0 = Sunny
        np.random.seed(42)
        
        # Generate synthetic training data
        n_samples = 500
        
        # Sunny day patterns: high temp, low humidity, high pressure, low clouds
        sunny_data = np.column_stack([
            np.random.uniform(20, 35, n_samples//2),  # temp
            np.random.uniform(30, 60, n_samples//2),  # humidity
            np.random.uniform(1015, 1025, n_samples//2),  # pressure
            np.random.uniform(5, 20, n_samples//2),  # wind speed
            np.random.uniform(0, 40, n_samples//2),  # cloud cover
        ])
        
        # Rainy day patterns: lower temp, high humidity, low pressure, high clouds
        rainy_data = np.column_stack([
            np.random.uniform(10, 20, n_samples//2),  # temp
            np.random.uniform(70, 95, n_samples//2),  # humidity
            np.random.uniform(995, 1010, n_samples//2),  # pressure
            np.random.uniform(10, 30, n_samples//2),  # wind speed
            np.random.uniform(60, 100, n_samples//2),  # cloud cover
        ])
        
        X = np.vstack([sunny_data, rainy_data])
        y = np.hstack([np.zeros(n_samples//2), np.ones(n_samples//2)])
        
        # Train Random Forest model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        print("✓ Model trained successfully")
    
    def get_weather_data(self, lat: float, lon: float) -> Dict:
        """
        Fetch weather data from Open-Meteo API (free, no API key needed)
        """
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
            print(f"Error fetching weather data: {e}")
            # Return default values if API fails
            return {
                'temperature': 15,
                'humidity': 50,
                'pressure': 1013,
                'wind_speed': 10,
                'wind_direction': 0,
                'wind_direction_cardinal': 'N',
                'wind_gusts': 0,
                'cloud_cover': 50,
                'precipitation': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def degrees_to_cardinal(self, degrees: float) -> str:
        """Convert wind direction in degrees to cardinal direction"""
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]
    
    def predict_weather(self, weather_data: Dict) -> Tuple[str, float]:
        """
        Predict weather condition (Rainy/Sunny)
        
        Returns:
            Tuple of (prediction, confidence)
        """
        # Extract features
        features = np.array([[
            weather_data['temperature'],
            weather_data['humidity'],
            weather_data['pressure'],
            weather_data['wind_speed'],
            weather_data['cloud_cover']
        ]])
        
        # If there's actual precipitation, it's definitely rainy
        if weather_data['precipitation'] > 0.1:
            return "Rainy", 1.0
        
        # Make prediction
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0]
        confidence = max(probability)
        
        condition = "Rainy" if prediction == 1 else "Sunny"
        return condition, confidence
    
    def get_weather_for_all_stadiums(self) -> pd.DataFrame:
        """Get weather predictions for all MLB stadiums"""
        results = []
        
        print(f"\n{'='*80}")
        print(f"Fetching weather for all MLB stadiums on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*80}\n")
        
        for team_name, location in self.STADIUMS.items():
            print(f"Fetching: {team_name} - {location['venue']}...", end=" ")
            
            # Get weather data
            weather = self.get_weather_data(location['lat'], location['lon'])
            
            # Predict condition
            condition, confidence = self.predict_weather(weather)
            
            # Show wind info in output
            wind_info = f"Wind: {weather['wind_speed']:.1f} km/h {weather['wind_direction_cardinal']}"
            if weather['wind_gusts'] > weather['wind_speed']:
                wind_info += f" (gusts {weather['wind_gusts']:.1f})"
            
            print(f"{condition} ({confidence*100:.1f}% confidence) | {wind_info}")
            
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
            
            time.sleep(0.5)  # Rate limiting
        
        return pd.DataFrame(results)
    
    def export_to_csv(self, df: pd.DataFrame, filename: str = "mlb_stadium_weather.csv"):
        """Export weather predictions to CSV"""
        df.to_csv(filename, index=False)
        print(f"\n✓ Exported {len(df)} stadium predictions to {filename}")
    
    def print_summary(self, df: pd.DataFrame):
        """Print weather summary"""
        print(f"\n{'='*80}")
        print("WEATHER SUMMARY")
        print(f"{'='*80}")
        
        rainy_count = len(df[df['prediction'] == 'Rainy'])
        sunny_count = len(df[df['prediction'] == 'Sunny'])
        
        print(f"\n☀️  Sunny Stadiums: {sunny_count}/{len(df)} ({sunny_count/len(df)*100:.1f}%)")
        print(f"🌧️  Rainy Stadiums: {rainy_count}/{len(df)} ({rainy_count/len(df)*100:.1f}%)")
        
        print(f"\n🌡️  Temperature Range: {df['temperature_c'].min():.1f}°C - {df['temperature_c'].max():.1f}°C")
        print(f"💧 Humidity Range: {df['humidity_pct'].min():.0f}% - {df['humidity_pct'].max():.0f}%")
        print(f"💨 Wind Speed Range: {df['wind_speed_kmh'].min():.1f} - {df['wind_speed_kmh'].max():.1f} km/h")
        
        # Wind statistics
        print(f"\n💨 WIND ANALYSIS:")
        print(f"   Average Wind Speed: {df['wind_speed_kmh'].mean():.1f} km/h")
        print(f"   Max Wind Gusts: {df['wind_gusts_kmh'].max():.1f} km/h")
        
        # Most common wind directions
        wind_dir_counts = df['wind_direction_cardinal'].value_counts()
        print(f"   Most Common Wind Direction: {wind_dir_counts.index[0]} ({wind_dir_counts.values[0]} stadiums)")
        
        # Windiest stadiums
        print(f"\n🌪️  Windiest Stadiums:")
        windiest = df.nlargest(3, 'wind_speed_kmh')
        for _, row in windiest.iterrows():
            wind_desc = f"{row['wind_speed_kmh']:.1f} km/h {row['wind_direction_cardinal']}"
            if row['wind_gusts_kmh'] > row['wind_speed_kmh']:
                wind_desc += f" (gusts {row['wind_gusts_kmh']:.1f})"
            print(f"   {row['team']}: {wind_desc}")
        
        # Show rainiest and sunniest
        print("\n🌧️  Rainiest Conditions:")
        rainy_stadiums = df[df['prediction'] == 'Rainy'].nlargest(3, 'confidence')
        for _, row in rainy_stadiums.iterrows():
            print(f"   {row['team']}: {row['temperature_c']:.1f}°C, {row['humidity_pct']:.0f}% humidity, "
                  f"Wind {row['wind_speed_kmh']:.1f} km/h {row['wind_direction_cardinal']} "
                  f"({row['confidence']*100:.1f}% confidence)")
        
        print("\n☀️  Best Weather:")
        sunny_stadiums = df[df['prediction'] == 'Sunny'].nlargest(3, 'confidence')
        for _, row in sunny_stadiums.iterrows():
            print(f"   {row['team']}: {row['temperature_c']:.1f}°C, {row['humidity_pct']:.0f}% humidity, "
                  f"Wind {row['wind_speed_kmh']:.1f} km/h {row['wind_direction_cardinal']} "
                  f"({row['confidence']*100:.1f}% confidence)")
        
        print(f"\n{'='*80}")


def main():
    """Main execution"""
    print("="*80)
    print("MLB STADIUM WEATHER PREDICTOR")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print()
    
    # Initialize predictor
    predictor = MLBWeatherPredictor()
    
    # Get weather for all stadiums
    weather_df = predictor.get_weather_for_all_stadiums()
    
    # Print summary
    predictor.print_summary(weather_df)
    
    # Export to CSV
    os.makedirs('data', exist_ok=True)
    predictor.export_to_csv(weather_df, 'data/mlb_stadium_weather.csv')
    
    # Optional: Compare with today's games
    print("\n💡 TIP: Compare this data with today's MLB schedule to see")
    print("   which games might be affected by weather conditions!")
    
    return weather_df


if __name__ == "__main__":
    main()
