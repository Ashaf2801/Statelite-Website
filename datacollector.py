from flask import Flask, request, jsonify
from environmental_predictor import EnvironmentalPredictor

# Initialize Flask app
app = Flask(__name__)

# Initialize predictor with model path
predictor = EnvironmentalPredictor("C:/Users/Ashaf/Desktop/Project/Ideathon/Statelite-Website/merra2_advanced_model.keras")

# Define API endpoint for predictions
@app.route('/predict', methods=['POST'])
def predict():
    # Get data from the request
    data = request.json
    date = data.get('date')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    time = data.get('time')

    # Validate input
    if not all([date, latitude, longitude, time]):
        return jsonify({'error': 'Missing required fields: date, latitude, longitude, or time'}), 400

    # Make prediction
    try:
        result = predictor.predict(date, latitude, longitude, time)

        # Return prediction results as JSON
        return jsonify({
            'temperature': f"{result['BME688']['temperature']:.1f}°C",
            'humidity': f"{result['BME688']['humidity']:.1f}%",
            'CO2': f"{result['CO2']['value']:.1f} ppm",
            'VOC': f"{result['VOC']['value']:.2f}",
            'PM1.0': f"{result['PM1.0']['value']:.2f}",
            'PM2.5': f"{result['PM2.5']['value']:.2f}",
            'PM10': f"{result['PM10']['value']:.2f}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the Flask app
if __name__ == '__main__': 
    app.run(debug=True)


