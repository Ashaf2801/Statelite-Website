EnvPredictor
A high-accuracy environmental prediction package using TensorFlow models to predict environmental parameters based on date, time, latitude, and longitude.
Installation

Clone the repository:
git clone <repository-url>
cd envpredictor


Install the package:
pip install .


Install dependencies:
pip install -r requirements.txt



Usage
from envpredictor import HighAccuracyEnvironmentalPredictor

# Initialize the predictor with the path to your .keras model
predictor = HighAccuracyEnvironmentalPredictor("path/to/model.keras")

# Make a prediction
result = predictor.predict(
    date_str="20251212",  # YYYYMMDD format
    lat=11.0,             # Latitude in degrees
    lon=77.0,             # Longitude in degrees
    time_str="08:00"      # HH:MM format
)

# Print results
if 'error' not in result:
    print(f"Temperature: {result['BME688']['temperature']:.1f} °C")
    print(f"CO2: {result['CO2']['value']:.1f} ppm")
    print(f"Metadata: {result['metadata']}")
else:
    print(f"Error: {result['message']}")

Requirements
See requirements.txt for a list of dependencies.
License
MIT License. See LICENSE for details.
