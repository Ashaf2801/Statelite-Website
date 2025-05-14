# Set Matplotlib to use the Agg backend (non-GUI)
import matplotlib
matplotlib.use('Agg')  # Must be called before importing pyplot

from flask import Flask, request, jsonify
from flask_cors import CORS
from envpredictor import HighAccuracyEnvironmentalPredictor
import traceback
from datetime import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
from pykrige.ok import OrdinaryKriging
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
import warnings
import io
import base64
import os

warnings.filterwarnings("ignore")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Model path
MODEL_PATH = "C:/Users/Ashaf/Desktop/Project/Ideathon/Statelite-Website/merra2_advanced_model.keras"

# Initialize predictor with the new model path
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    predictor = HighAccuracyEnvironmentalPredictor(MODEL_PATH)
    print("Successfully loaded HighAccuracyEnvironmentalPredictor")
except Exception as e:
    print(f"Failed to load HighAccuracyEnvironmentalPredictor: {str(e)}")
    print(traceback.format_exc())
    predictor = None  # Set to None if loading fails

# Define API endpoint for predictions
@app.route('/predict', methods=['POST'])
def predict():
    print("Received request for /predict")
    
    if predictor is None:
        error_msg = "HighAccuracyEnvironmentalPredictor failed to initialize. Check server logs for details."
        print(error_msg)
        return jsonify({'error': error_msg}), 500

    # Get current date and time in the required format
    current_time = datetime.now()
    date = current_time.strftime("%Y%m%d")  # Format: YYYYMMDD (e.g., 20250514)
    time = current_time.strftime("%H:%M")   # Format: HH:MM (e.g., 16:28)

    # Get latitude and longitude from the request
    data = request.json
    if not data:
        error_msg = "No JSON data provided in the request."
        print(f"Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Validate input
    if not all([latitude, longitude]):
        error_msg = 'Missing required fields: latitude or longitude'
        print(f"Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    # Make prediction using current date and time
    try:
        result = predictor.predict(
            date_str=date,
            lat=float(latitude),
            lon=float(longitude),
            time_str=time
        )
        print(f"Prediction successful for lat={latitude}, lon={longitude}")
        print(f"Prediction result: {result}")

        # Check for error in the result
        if 'error' in result:
            error_msg = result.get('message', 'Prediction failed.')
            print(f"Error in prediction: {error_msg}")
            return jsonify({'error': error_msg}), 500

        # Return prediction results as JSON, formatted as expected by the frontend
        return jsonify({
            'temperature': f"{result['BME688']['temperature']:.1f}°C",
            'humidity': f"{result['BME688']['humidity']:.1f}%",
            'CO2': f"{result['CO2']['value']:.1f} ppm",
            'VOC': f"{result['VOC']['value']:.2f}",
            'PM1.0': f"{result['PM1.0']['value']:.2f}",
            'PM2.5': f"{result['PM2.5']['value']:.2f}",
            'PM10': f"{result['PM10']['value']:.2f}"
        })
    except KeyError as e:
        error_msg = f"Missing key in prediction result: {str(e)}"
        print(f"Error in predict: {error_msg}")
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f"An error occurred while making the prediction: {str(e)}"
        print(f"Error in predict: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/heatmap-data', methods=['POST'])
def heatmap_data():
    print("Received request for /heatmap-data")
    
    # Get latitude, longitude, and radius from the request
    data = request.json
    if not data:
        error_msg = "No JSON data provided in the request."
        print(f"Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    radius = data.get('radius', 0.1)  # Default radius of 0.1 degrees

    if not all([latitude, longitude]):
        error_msg = 'Missing required fields: latitude or longitude'
        print(f"Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    try:
        # Convert to float
        latitude = float(latitude)
        longitude = float(longitude)

        # Get current date and time for predictions
        current_time = datetime.now()
        date = current_time.strftime("%Y%m%d")  # Format: YYYYMMDD (e.g., 20250514)
        time = current_time.strftime("%H:%M")   # Format: HH:MM (e.g., 16:28)

        # Generate multiple points around the clicked location for spatial variation
        n_points = 50
        np.random.seed(42)
        lat_offsets = np.random.uniform(-radius, radius, n_points)
        lon_offsets = np.random.uniform(-radius, radius, n_points)
        
        # Collect predicted data for each point
        data = {
            'latitude': [],
            'longitude': [],
            'VOC': [],
            'CO2': [],
            'PM1_0': [],
            'PM2_5': [],
            'PM10': []
        }

        for lat_offset, lon_offset in zip(lat_offsets, lon_offsets):
            lat = latitude + lat_offset
            lon = longitude + lon_offset

            # Make prediction for this point
            try:
                result = predictor.predict(
                    date_str=date,
                    lat=float(lat),
                    lon=float(lon),
                    time_str=time
                )
                if 'error' in result:
                    continue  # Skip points with prediction errors

                # Append the predicted values
                data['latitude'].append(lat)
                data['longitude'].append(lon)
                data['VOC'].append(result['VOC']['value'])
                data['CO2'].append(result['CO2']['value'])
                data['PM1_0'].append(result['PM1.0']['value'])
                data['PM2_5'].append(result['PM2.5']['value'])
                data['PM10'].append(result['PM10']['value'])
            except Exception as e:
                print(f"Error predicting for lat={lat}, lon={lon}: {str(e)}")
                continue

        # Create DataFrame from predicted data
        if not data['latitude']:  # Check if data is empty
            error_msg = "No valid predictions obtained for the heatmap."
            print(error_msg)
            return jsonify({'error': error_msg}), 500

        df = pd.DataFrame(data)
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        # Define pollutant for the heatmap
        pollutant = 'PM2_5'

        # Grid setup
        lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
        lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
        grid_res = 0.0045
        grid_lon = np.arange(lon_min, lon_max, grid_res)
        grid_lat = np.arange(lat_min, lat_max, grid_res)
        grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)

        # Kriging
        OK = OrdinaryKriging(
            df['longitude'], df['latitude'], df[pollutant],
            variogram_model='spherical',
            verbose=False, enable_plotting=False
        )
        z, ss = OK.execute('grid', grid_lon[0, :], grid_lat[:, 0])

        # AQI categories for PM2.5 (US EPA style)
        aqi_bins = [0, 12, 35.4, 55.4, 150.4, 250.4, 500]
        aqi_labels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups',
                      'Unhealthy', 'Very Unhealthy', 'Hazardous']
        aqi_colors = ['#00e400', '#ffff00', '#ff7e00', '#ff0000', '#8f3f97', '#7e0023']

        # Plot
        fig, ax = plt.subplots(figsize=(24, 16))
        im = ax.imshow(z, extent=(lon_min, lon_max, lat_min, lat_max), origin='lower',
                       cmap='RdYlGn_r', vmin=0, vmax=100, alpha=0.8)

        # Sensor points colored by PM2.5 value
        gdf.plot(ax=ax, column=pollutant, cmap='RdYlGn_r', markersize=40, legend=False)

        # Add colorbar with AQI labels
        cbar = plt.colorbar(im, ax=ax, label=f'{pollutant} (µg/m³)', orientation='vertical')
        cbar.set_ticks([0, 12, 35.4, 55.4, 100])
        cbar.set_ticklabels(['Good', 'Moderate', 'Unhealthy\n(Sensitive)', 'Unhealthy', 'Very Unhealthy'])
        cbar.ax.tick_params(labelsize=4.7)  # Reduced font size (8 / 3)
        cbar.set_label(f'{pollutant} (µg/m³)', fontsize=2.7)  # Reduced font size (8 / 3)

        # Basemap
        ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

        # Remove x and y axis markings (tick marks and labels)
        ax.set_xticks([])  # Remove x-axis tick marks
        ax.set_yticks([])  # Remove y-axis tick marks

        # Labels are already commented out, ensuring no axis labels appear
        # ax.set_xlabel('Longitude', fontsize=8)
        # ax.set_ylabel('Latitude', fontsize=8)

        # Save the plot to a bytes buffer and encode as base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close(fig)  # Explicitly close the figure to free memory
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()

        # Return the base64-encoded image
        return jsonify({'heatmap_image': f'data:image/png;base64,{image_base64}'})
    except Exception as e:
        error_msg = f"Failed to generate heatmap: {str(e)}"
        print(f"Error in heatmap_data: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

# Run the Flask app
if __name__ == '__main__': 
    app.run(debug=True)