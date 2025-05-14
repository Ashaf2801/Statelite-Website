import tensorflow as tf
import numpy as np
from datetime import datetime
import math
from typing import Tuple, Dict, List
import warnings
from dateutil.relativedelta import relativedelta
import random

from .region import RegionType
from .utils import generate_deterministic_variation

# Suppress TensorFlow warnings
tf.get_logger().setLevel('ERROR')
warnings.filterwarnings('ignore')

class HighAccuracyEnvironmentalPredictor:
    def __init__(self, model_path: str):
        """
        Initialize the high-accuracy environmental predictor with comprehensive regional modeling.

        Args:
            model_path: Path to the trained .keras model
        """
        try:
            # Load model with enhanced validation
            self.model = tf.keras.models.load_model(
                model_path,
                custom_objects={},
                compile=False
            )
            self._validate_model()
            
            # MERRA-2 grid parameters
            self.lat_min = -90
            self.lat_max = 90
            self.lon_min = -180
            self.lon_max = 180
            self.lat_res = 0.5
            self.lon_res = 0.625

            self.variation_scales = {
                'temperature': 0.3,    # ±0.3°C
                'humidity': 1.0,       # ±1.0%
                'pressure': 0.5,       # ±0.5 hPa
                'gas_resistance': 1000.0,  # ±1000 ohms
                'CO2': 2.0,            # ±2.0 ppm
                'VOC': 5.0,            # ±5.0 ppb
                'PM1.0': 0.5,          # ±0.5 µg/m³
                'PM2.5': 0.7,          # ±0.7 µg/m³
                'PM10': 1.0            # ±1.0 µg/m³
            }
            
            # Regional base values with realistic ranges
            self.regional_base_values = {
                RegionType.OCEAN: {
                    'temperature': 18.0,  # °C
                    'humidity': 85.0,     # %
                    'pressure': 1013.25, # hPa
                    'gas_resistance': 80000.0,  # ohms
                    'CO2': 410.0,        # ppm
                    'VOC': 80.0,         # ppb
                    'PM1.0': 2.0,         # µg/m³
                    'PM2.5': 3.0,         # µg/m³
                    'PM10': 4.0           # µg/m³
                },
                RegionType.COASTAL: {
                    'temperature': 22.0,
                    'humidity': 75.0,
                    'pressure': 1013.0,
                    'gas_resistance': 60000.0,
                    'CO2': 420.0,
                    'VOC': 120.0,
                    'PM1.0': 5.0,
                    'PM2.5': 8.0,
                    'PM10': 10.0
                },
                RegionType.FOREST_TROPICAL: {
                    'temperature': 26.0,
                    'humidity': 85.0,
                    'pressure': 1012.0,
                    'gas_resistance': 50000.0,
                    'CO2': 430.0,
                    'VOC': 200.0,
                    'PM1.0': 4.0,
                    'PM2.5': 6.0,
                    'PM10': 8.0
                },
                RegionType.FOREST_TEMPERATE: {
                    'temperature': 18.0,
                    'humidity': 70.0,
                    'pressure': 1013.0,
                    'gas_resistance': 55000.0,
                    'CO2': 425.0,
                    'VOC': 150.0,
                    'PM1.0': 3.0,
                    'PM2.5': 5.0,
                    'PM10': 7.0
                },
                RegionType.GRASSLAND: {
                    'temperature': 20.0,
                    'humidity': 60.0,
                    'pressure': 1013.0,
                    'gas_resistance': 50000.0,
                    'CO2': 420.0,
                    'VOC': 100.0,
                    'PM1.0': 4.0,
                    'PM2.5': 6.0,
                    'PM10': 9.0
                },
                RegionType.DESERT: {
                    'temperature': 30.0,
                    'humidity': 20.0,
                    'pressure': 1012.0,
                    'gas_resistance': 30000.0,
                    'CO2': 415.0,
                    'VOC': 50.0,
                    'PM1.0': 10.0,
                    'PM2.5': 25.0,
                    'PM10': 50.0
                },
                RegionType.TUNDRA: {
                    'temperature': -5.0,
                    'humidity': 70.0,
                    'pressure': 1015.0,
                    'gas_resistance': 70000.0,
                    'CO2': 410.0,
                    'VOC': 30.0,
                    'PM1.0': 2.0,
                    'PM2.5': 3.0,
                    'PM10': 4.0
                },
                RegionType.URBAN: {
                    'temperature': 24.0,
                    'humidity': 65.0,
                    'pressure': 1012.0,
                    'gas_resistance': 40000.0,
                    'CO2': 450.0,
                    'VOC': 300.0,
                    'PM1.0': 10.0,
                    'PM2.5': 20.0,
                    'PM10': 30.0
                },
                RegionType.MOUNTAIN: {
                    'temperature': 12.0,
                    'humidity': 60.0,
                    'pressure': 900.0,
                    'gas_resistance': 60000.0,
                    'CO2': 415.0,
                    'VOC': 80.0,
                    'PM1.0': 3.0,
                    'PM2.5': 5.0,
                    'PM10': 7.0
                },
                RegionType.AGRICULTURAL: {
                    'temperature': 22.0,
                    'humidity': 65.0,
                    'pressure': 1013.0,
                    'gas_resistance': 45000.0,
                    'CO2': 435.0,
                    'VOC': 180.0,
                    'PM1.0': 6.0,
                    'PM2.5': 12.0,
                    'PM10': 15.0
                }
            }
            
            # Calibration factors for urban/rural areas
            self.calibration_factors = {
                'urban': {
                    'CO2': 1.1,
                    'VOC': 1.2,
                    'PM': 1.3
                },
                'rural': {
                    'CO2': 1.0,
                    'VOC': 1.0,
                    'PM': 1.0
                }
            }
            
            # Seasonal parameters
            self.seasonal_params = {
                'summer': {
                    'temp_shift': {
                        RegionType.OCEAN: 2.0,
                        RegionType.COASTAL: 4.0,
                        RegionType.FOREST_TROPICAL: 1.0,
                        RegionType.FOREST_TEMPERATE: 6.0,
                        RegionType.GRASSLAND: 8.0,
                        RegionType.DESERT: 12.0,
                        RegionType.TUNDRA: 10.0,
                        RegionType.URBAN: 5.0,
                        RegionType.MOUNTAIN: 4.0,
                        RegionType.AGRICULTURAL: 6.0
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 5.0,
                        RegionType.COASTAL: 10.0,
                        RegionType.FOREST_TROPICAL: 5.0,
                        RegionType.FOREST_TEMPERATE: 15.0,
                        RegionType.GRASSLAND: -10.0,
                        RegionType.DESERT: -5.0,
                        RegionType.TUNDRA: 20.0,
                        RegionType.URBAN: 5.0,
                        RegionType.MOUNTAIN: 5.0,
                        RegionType.AGRICULTURAL: 8.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.1,
                        RegionType.COASTAL: 1.2,
                        RegionType.FOREST_TROPICAL: 1.1,
                        RegionType.FOREST_TEMPERATE: 1.1,
                        RegionType.GRASSLAND: 1.3,
                        RegionType.DESERT: 1.5,
                        RegionType.TUNDRA: 1.0,
                        RegionType.URBAN: 1.4,
                        RegionType.MOUNTAIN: 1.1,
                        RegionType.AGRICULTURAL: 1.3
                    }
                },
                'winter': {
                    'temp_shift': {
                        RegionType.OCEAN: -1.0,
                        RegionType.COASTAL: -3.0,
                        RegionType.FOREST_TROPICAL: 0.0,
                        RegionType.FOREST_TEMPERATE: -8.0,
                        RegionType.GRASSLAND: -10.0,
                        RegionType.DESERT: -5.0,
                        RegionType.TUNDRA: -25.0,
                        RegionType.URBAN: -4.0,
                        RegionType.MOUNTAIN: -6.0,
                        RegionType.AGRICULTURAL: -5.0
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 0.0,
                        RegionType.COASTAL: 5.0,
                        RegionType.FOREST_TROPICAL: 0.0,
                        RegionType.FOREST_TEMPERATE: -5.0,
                        RegionType.GRASSLAND: -5.0,
                        RegionType.DESERT: -3.0,
                        RegionType.TUNDRA: -10.0,
                        RegionType.URBAN: -5.0,
                        RegionType.MOUNTAIN: -5.0,
                        RegionType.AGRICULTURAL: -3.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 1.1,
                        RegionType.FOREST_TROPICAL: 1.0,
                        RegionType.FOREST_TEMPERATE: 1.2,
                        RegionType.GRASSLAND: 1.4,
                        RegionType.DESERT: 1.2,
                        RegionType.TUNDRA: 1.5,
                        RegionType.URBAN: 1.6,
                        RegionType.MOUNTAIN: 1.3,
                        RegionType.AGRICULTURAL: 1.4
                    }
                },
                'spring': {
                    'temp_shift': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 2.0,
                        RegionType.FOREST_TROPICAL: 0.5,
                        RegionType.FOREST_TEMPERATE: 3.0,
                        RegionType.GRASSLAND: 4.0,
                        RegionType.DESERT: 6.0,
                        RegionType.TUNDRA: 5.0,
                        RegionType.URBAN: 2.0,
                        RegionType.MOUNTAIN: 2.0,
                        RegionType.AGRICULTURAL: 3.0
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 2.0,
                        RegionType.COASTAL: 8.0,
                        RegionType.FOREST_TROPICAL: 3.0,
                        RegionType.FOREST_TEMPERATE: 10.0,
                        RegionType.GRASSLAND: 5.0,
                        RegionType.DESERT: 2.0,
                        RegionType.TUNDRA: 15.0,
                        RegionType.URBAN: 3.0,
                        RegionType.MOUNTAIN: 3.0,
                        RegionType.AGRICULTURAL: 5.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 1.1,
                        RegionType.FOREST_TROPICAL: 1.0,
                        RegionType.FOREST_TEMPERATE: 1.1,
                        RegionType.GRASSLAND: 1.2,
                        RegionType.DESERT: 1.3,
                        RegionType.TUNDRA: 1.1,
                        RegionType.URBAN: 1.3,
                        RegionType.MOUNTAIN: 1.1,
                        RegionType.AGRICULTURAL: 1.2
                    }
                },
                'fall': {
                    'temp_shift': {
                        RegionType.OCEAN: 0.5,
                        RegionType.COASTAL: 1.0,
                        RegionType.FOREST_TROPICAL: 0.5,
                        RegionType.FOREST_TEMPERATE: 2.0,
                        RegionType.GRASSLAND: 3.0,
                        RegionType.DESERT: 4.0,
                        RegionType.TUNDRA: 2.0,
                        RegionType.URBAN: 1.0,
                        RegionType.MOUNTAIN: 1.0,
                        RegionType.AGRICULTURAL: 2.0
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 5.0,
                        RegionType.FOREST_TROPICAL: 2.0,
                        RegionType.FOREST_TEMPERATE: 8.0,
                        RegionType.GRASSLAND: 3.0,
                        RegionType.DESERT: 1.0,
                        RegionType.TUNDRA: 10.0,
                        RegionType.URBAN: 2.0,
                        RegionType.MOUNTAIN: 2.0,
                        RegionType.AGRICULTURAL: 3.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 1.1,
                        RegionType.FOREST_TROPICAL: 1.0,
                        RegionType.FOREST_TEMPERATE: 1.2,
                        RegionType.GRASSLAND: 1.3,
                        RegionType.DESERT: 1.4,
                        RegionType.TUNDRA: 1.2,
                        RegionType.URBAN: 1.4,
                        RegionType.MOUNTAIN: 1.2,
                        RegionType.AGRICULTURAL: 1.3
                    }
                }
            }
            
            # Diurnal parameters
            self.diurnal_params = {
                'morning': {
                    'temp_shift': {
                        RegionType.OCEAN: -0.5,
                        RegionType.COASTAL: -1.0,
                        RegionType.FOREST_TROPICAL: -0.5,
                        RegionType.FOREST_TEMPERATE: -1.5,
                        RegionType.GRASSLAND: -2.0,
                        RegionType.DESERT: -3.0,
                        RegionType.TUNDRA: -1.0,
                        RegionType.URBAN: -1.0,
                        RegionType.MOUNTAIN: -1.5,
                        RegionType.AGRICULTURAL: -1.5
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 5.0,
                        RegionType.COASTAL: 10.0,
                        RegionType.FOREST_TROPICAL: 5.0,
                        RegionType.FOREST_TEMPERATE: 10.0,
                        RegionType.GRASSLAND: 15.0,
                        RegionType.DESERT: 10.0,
                        RegionType.TUNDRA: 5.0,
                        RegionType.URBAN: 8.0,
                        RegionType.MOUNTAIN: 10.0,
                        RegionType.AGRICULTURAL: 12.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 1.1,
                        RegionType.FOREST_TROPICAL: 1.0,
                        RegionType.FOREST_TEMPERATE: 1.1,
                        RegionType.GRASSLAND: 1.2,
                        RegionType.DESERT: 1.3,
                        RegionType.TUNDRA: 1.0,
                        RegionType.URBAN: 1.3,
                        RegionType.MOUNTAIN: 1.1,
                        RegionType.AGRICULTURAL: 1.2
                    }
                },
                'afternoon': {
                    'temp_shift': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 3.0,
                        RegionType.FOREST_TROPICAL: 2.0,
                        RegionType.FOREST_TEMPERATE: 4.0,
                        RegionType.GRASSLAND: 6.0,
                        RegionType.DESERT: 10.0,
                        RegionType.TUNDRA: 3.0,
                        RegionType.URBAN: 4.0,
                        RegionType.MOUNTAIN: 3.0,
                        RegionType.AGRICULTURAL: 5.0
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: -5.0,
                        RegionType.COASTAL: -10.0,
                        RegionType.FOREST_TROPICAL: -5.0,
                        RegionType.FOREST_TEMPERATE: -10.0,
                        RegionType.GRASSLAND: -15.0,
                        RegionType.DESERT: -5.0,
                        RegionType.TUNDRA: -5.0,
                        RegionType.URBAN: -10.0,
                        RegionType.MOUNTAIN: -10.0,
                        RegionType.AGRICULTURAL: -12.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.0,
                        RegionType.COASTAL: 1.0,
                        RegionType.FOREST_TROPICAL: 1.0,
                        RegionType.FOREST_TEMPERATE: 1.0,
                        RegionType.GRASSLAND: 1.1,
                        RegionType.DESERT: 1.2,
                        RegionType.TUNDRA: 1.0,
                        RegionType.URBAN: 1.2,
                        RegionType.MOUNTAIN: 1.0,
                        RegionType.AGRICULTURAL: 1.1
                    }
                },
                'evening': {
                    'temp_shift': {
                        RegionType.OCEAN: 0.5,
                        RegionType.COASTAL: 1.0,
                        RegionType.FOREST_TROPICAL: 0.5,
                        RegionType.FOREST_TEMPERATE: 1.0,
                        RegionType.GRASSLAND: 2.0,
                        RegionType.DESERT: 3.0,
                        RegionType.TUNDRA: 1.0,
                        RegionType.URBAN: 1.0,
                        RegionType.MOUNTAIN: 1.0,
                        RegionType.AGRICULTURAL: 1.5
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 3.0,
                        RegionType.COASTAL: 8.0,
                        RegionType.FOREST_TROPICAL: 3.0,
                        RegionType.FOREST_TEMPERATE: 8.0,
                        RegionType.GRASSLAND: 10.0,
                        RegionType.DESERT: 5.0,
                        RegionType.TUNDRA: 3.0,
                        RegionType.URBAN: 5.0,
                        RegionType.MOUNTAIN: 5.0,
                        RegionType.AGRICULTURAL: 8.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 1.1,
                        RegionType.COASTAL: 1.2,
                        RegionType.FOREST_TROPICAL: 1.1,
                        RegionType.FOREST_TEMPERATE: 1.2,
                        RegionType.GRASSLAND: 1.3,
                        RegionType.DESERT: 1.4,
                        RegionType.TUNDRA: 1.1,
                        RegionType.URBAN: 1.4,
                        RegionType.MOUNTAIN: 1.2,
                        RegionType.AGRICULTURAL: 1.3
                    }
                },
                'night': {
                    'temp_shift': {
                        RegionType.OCEAN: -1.0,
                        RegionType.COASTAL: -2.0,
                        RegionType.FOREST_TROPICAL: -1.0,
                        RegionType.FOREST_TEMPERATE: -3.0,
                        RegionType.GRASSLAND: -4.0,
                        RegionType.DESERT: -8.0,
                        RegionType.TUNDRA: -2.0,
                        RegionType.URBAN: -2.0,
                        RegionType.MOUNTAIN: -3.0,
                        RegionType.AGRICULTURAL: -3.0
                    },
                    'humidity_shift': {
                        RegionType.OCEAN: 8.0,
                        RegionType.COASTAL: 15.0,
                        RegionType.FOREST_TROPICAL: 8.0,
                        RegionType.FOREST_TEMPERATE: 15.0,
                        RegionType.GRASSLAND: 20.0,
                        RegionType.DESERT: 15.0,
                        RegionType.TUNDRA: 10.0,
                        RegionType.URBAN: 12.0,
                        RegionType.MOUNTAIN: 15.0,
                        RegionType.AGRICULTURAL: 18.0
                    },
                    'pollution_factor': {
                        RegionType.OCEAN: 0.9,
                        RegionType.COASTAL: 0.9,
                        RegionType.FOREST_TROPICAL: 0.9,
                        RegionType.FOREST_TEMPERATE: 0.9,
                        RegionType.GRASSLAND: 0.9,
                        RegionType.DESERT: 0.8,
                        RegionType.TUNDRA: 0.9,
                        RegionType.URBAN: 1.0,
                        RegionType.MOUNTAIN: 0.9,
                        RegionType.AGRICULTURAL: 0.9
                    }
                }
            }
            
            # Load elevation data (simplified for demo)
            self.elevation_data = self._load_elevation_data()
            
        except FileNotFoundError:
            raise RuntimeError(f"Model file not found at {model_path}")
        except Exception as e:
            raise RuntimeError(f"Initialization failed: {str(e)}")

    def _load_elevation_data(self) -> Dict:
        """Load simplified elevation data."""
        return {
            'default': 0.0,
            'mountain_threshold': 1000.0  # meters
        }

    def _validate_model(self):
        """Validate the loaded model architecture and weights."""
        try:
            test_input = np.random.rand(1, 3, 128, 128, 1).astype(np.float32)
            test_output = self.model.predict(test_input, verbose=0)
            if test_output.shape != (1, 128, 128, 2):
                raise ValueError("Model output shape mismatch")
        except Exception as e:
            raise ValueError(f"Model validation failed: {str(e)}")

    def _determine_region_type(self, lat: float, lon: float) -> RegionType:
        """Determine the region type based on latitude and longitude."""
        if (abs(lat) < 30 and ((0 < lon < 20) or (60 < lon < 100) or (140 < lon < 180) or 
            (-140 < lon < -60) or (-20 < lon < 0))):
            return RegionType.OCEAN
        if ((15 < lat < 35 and -120 < lon < -80) or
            (15 < lat < 30 and -10 < lon < 50) or
            (20 < lat < 35 and 50 < lon < 80) or
            (-30 < lat < -15 and 115 < lon < 150) or
            (-30 < lat < -15 and -80 < lon < -60)):
            return RegionType.DESERT
        if ((-10 < lat < 10 and -80 < lon < -50) or
            (-10 < lat < 10 and 10 < lon < 40) or
            (-10 < lat < 10 and 90 < lon < 150)):
            return RegionType.FOREST_TROPICAL
        if (((40 < lat < 60 and -10 < lon < 30) or
             (40 < lat < 60 and -130 < lon < -70) or
             (30 < lat < 50 and 120 < lon < 150))):
            return RegionType.FOREST_TEMPERATE
        if (lat > 60 or lat < -60):
            return RegionType.TUNDRA
        if ((35 < lat < 45 and -120 < lon < -105) or
            (-35 < lat < -20 and -75 < lon < -60) or
            (30 < lat < 40 and 70 < lon < 90) or
            (45 < lat < 50 and 5 < lon < 15)):
            return RegionType.MOUNTAIN
        if (abs(lon) < 10 or abs(lon) > 170 or 
            (abs(lat) < 30 and (abs(lon) < 100 and abs(lon) > 80))):
            return RegionType.COASTAL
        major_cities = [
            (40.7, -74.0), (51.5, -0.1), (35.7, 139.7), (19.1, 72.9),
            (34.1, -118.2), (41.9, 12.5), (-23.5, -46.6), (30.0, 31.2),
            (39.9, 116.4), (55.8, 37.6)
        ]
        for city_lat, city_lon in major_cities:
            if abs(lat - city_lat) < 1.0 and abs(lon - city_lon) < 1.5:
                return RegionType.URBAN
        if ((25 < lat < 50 and -105 < lon < -75) or
            (45 < lat < 55 and -5 < lon < 30) or
            (-40 < lat < -20 and -65 < lon < -50) or
            (20 < lat < 40 and 70 < lon < 100)):
            return RegionType.AGRICULTURAL
        return RegionType.GRASSLAND

    def _get_elevation(self, lat: float, lon: float) -> float:
        """Get elevation for a given location (simplified)."""
        region = self._determine_region_type(lat, lon)
        if region == RegionType.MOUNTAIN:
            return 2500.0
        elif region == RegionType.TUNDRA:
            return 200.0
        elif region == RegionType.OCEAN:
            return -50.0
        else:
            return 100.0

    def _latlon_to_merra_index(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert lat/lon to MERRA-2 grid indices with boundary checks."""
        lat = max(min(lat, self.lat_max), self.lat_min)
        lon = max(min(lon, self.lon_max), self.lon_min)
        lat_idx = int((self.lat_max - lat) / self.lat_res)
        lon_idx = int((lon - self.lon_min) / self.lon_res)
        return lat_idx, lon_idx

    def _datetime_to_features(self, dt: datetime) -> Dict:
        """Convert datetime to comprehensive temporal features."""
        year_progress = (dt.timetuple().tm_yday - 1) / 365.0
        seasonal_sin = math.sin(2 * math.pi * year_progress)
        seasonal_cos = math.cos(2 * math.pi * year_progress)
        diurnal_progress = (dt.hour * 60 + dt.minute) / (24 * 60)
        diurnal_sin = math.sin(2 * math.pi * diurnal_progress)
        diurnal_cos = math.cos(2 * math.pi * diurnal_progress)
        month = dt.month
        if 3 <= month <= 5:
            season = 'spring'
        elif 6 <= month <= 8:
            season = 'summer'
        elif 9 <= month <= 11:
            season = 'fall'
        else:
            season = 'winter'
        hour = dt.hour
        if 5 <= hour < 11:
            time_of_day = 'morning'
        elif 11 <= hour < 16:
            time_of_day = 'afternoon'
        elif 16 <= hour < 21:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
        return {
            'year_progress': year_progress,
            'seasonal_sin': seasonal_sin,
            'seasonal_cos': seasonal_cos,
            'diurnal_sin': diurnal_sin,
            'diurnal_cos': diurnal_cos,
            'season': season,
            'time_of_day': time_of_day,
            'hour': hour,
            'month': month
        }

    def _generate_synthetic_patch(self, lat: float, lon: float, dt: datetime) -> np.ndarray:
        """Generate enhanced synthetic data patch with realistic regional patterns."""
        region_type = self._determine_region_type(lat, lon)
        temporal_features = self._datetime_to_features(dt)
        elevation = self._get_elevation(lat, lon)
        x = np.linspace(-1, 1, 128)
        y = np.linspace(-1, 1, 128)
        rel_lat, rel_lon = np.meshgrid(x, y)
        dist = np.sqrt(rel_lat**2 + rel_lon**2) / np.sqrt(2)
        if region_type == RegionType.OCEAN:
            pattern = 0.3 + 0.7 * np.exp(-dist * 3)
        elif region_type == RegionType.DESERT:
            pattern = 0.5 + 0.5 * np.sin(dist * 10)
        elif region_type == RegionType.URBAN:
            pattern = 0.4 + 0.6 * (1 - dist**2)
        else:
            pattern = np.maximum(0.2, np.exp(-dist * 2))
        seasonal_effect = 0.5 * temporal_features['seasonal_sin'] + 0.2 * temporal_features['seasonal_cos']
        diurnal_effect = 0.3 * temporal_features['diurnal_sin'] + 0.1 * temporal_features['diurnal_cos']
        if region_type == RegionType.OCEAN:
            seasonal_effect *= 0.7
            diurnal_effect *= 0.5
        elif region_type == RegionType.DESERT:
            seasonal_effect *= 1.2
            diurnal_effect *= 1.5
        elif region_type == RegionType.URBAN:
            seasonal_effect *= 0.9
            diurnal_effect *= 1.2
        patch = np.clip(pattern * (1 + seasonal_effect) * (1 + diurnal_effect * 0.5), 0.1, 1.0)
        elevation_factor = 1.0 - min(1.0, elevation / 5000.0)
        patch *= elevation_factor
        sequence = np.stack([
            patch * 0.85,
            patch * 0.93,
            patch
        ], axis=0)
        return sequence[..., np.newaxis]

    def _apply_temporal_adjustments(self, base_values: Dict, dt: datetime, region_type: RegionType) -> Dict:
        """Apply enhanced seasonal and diurnal adjustments with regional variations."""
        temporal_features = self._datetime_to_features(dt)
        season = temporal_features['season']
        time_of_day = temporal_features['time_of_day']
        season_params = self.seasonal_params.get(season, {})
        diurnal_params = self.diurnal_params.get(time_of_day, {})
        adjusted_values = base_values.copy()
        temp_shift = (season_params.get('temp_shift', {}).get(region_type, 0.0) +
                     diurnal_params.get('temp_shift', {}).get(region_type, 0.0))
        adjusted_values['temperature'] += temp_shift * (1 + 0.1 * temporal_features['seasonal_sin'])
        humidity_shift = (season_params.get('humidity_shift', {}).get(region_type, 0.0) +
                        diurnal_params.get('humidity_shift', {}).get(region_type, 0.0))
        adjusted_values['humidity'] = min(100, max(10, adjusted_values['humidity'] + humidity_shift))
        season_pollution = season_params.get('pollution_factor', {}).get(region_type, 1.0)
        diurnal_pollution = diurnal_params.get('pollution_factor', {}).get(region_type, 1.0)
        pollution_factor = season_pollution * diurnal_pollution
        adjusted_values['CO2'] *= pollution_factor
        adjusted_values['VOC'] *= pollution_factor * (1.2 if region_type == RegionType.URBAN else 1.1)
        adjusted_values['PM1.0'] *= pollution_factor
        adjusted_values['PM2.5'] *= pollution_factor * (1.3 if region_type == RegionType.URBAN else 1.2)
        adjusted_values['PM10'] *= pollution_factor * (1.4 if region_type == RegionType.URBAN else 1.2)
        return adjusted_values

    def _apply_physics_constraints(self, values: Dict, lat: float, lon: float, dt: datetime) -> Dict:
        """Apply physical constraints to predictions."""
        elevation = self._get_elevation(lat, lon)
        elevation_factor = 1.0 - min(1.0, elevation / 5000.0)
        temp_adjustment = elevation_factor * 2.0
        values['BME688']['temperature'] -= temp_adjustment
        values['MCP9808']['temperature'] -= temp_adjustment
        values['BME688']['pressure'] *= (1 - elevation_factor * 0.00012)
        region_type = self._determine_region_type(lat, lon)
        area_type = 'urban' if region_type == RegionType.URBAN else 'rural'
        calibration = self.calibration_factors[area_type]
        values['CO2']['value'] *= calibration['CO2']
        values['VOC']['value'] *= calibration['VOC']
        values['PM1.0']['value'] *= calibration['PM']
        values['PM2.5']['value'] *= calibration['PM']
        values['PM10']['value'] *= calibration['PM']
        return values

    def _calculate_enhanced_values(self, normalized_mean: float, adjusted_values: Dict) -> Dict:
        """Calculate enhanced parameter values with realistic scaling."""
        def sigmoid_scale(base, factor, range_scale, steepness=1.0):
            return base + (2 * range_scale) / (1 + math.exp(-steepness * (factor - 0.5)))
        
        def exp_scale(base, factor, range_scale):
            return base + range_scale * (math.exp(3 * factor) / math.exp(3))
        
        def add_sensor_noise(value, relative_scale=0.01, absolute_min_noise=0.1):
            noise_scale = max(abs(value) * relative_scale, absolute_min_noise)
            return value + random.uniform(-noise_scale, noise_scale)

        return {
            'BME688': {
                'temperature': add_sensor_noise(sigmoid_scale(adjusted_values['temperature'], normalized_mean, 15, 5)),
                'humidity': add_sensor_noise(min(100, max(10, adjusted_values['humidity'] + normalized_mean * 50)), 0.005),
                'pressure': add_sensor_noise(max(950, min(1050, adjusted_values['pressure'] - normalized_mean * 5)), 0.001),
                'gas_resistance': add_sensor_noise(exp_scale(adjusted_values['gas_resistance'], normalized_mean, 150000), 0.02)
            },
            'MCP9808': {
                'temperature': add_sensor_noise(sigmoid_scale(adjusted_values['temperature'], normalized_mean, 15, 5))
            },
            'CO2': {
                'value': add_sensor_noise(exp_scale(adjusted_values['CO2'], normalized_mean, 600), 0.02, 1.0)
            },
            'VOC': {
                'value': add_sensor_noise(exp_scale(adjusted_values['VOC'], normalized_mean, 400), 0.02, 0.5)
            },
            'PM1.0': {
                'value': max(0, add_sensor_noise(exp_scale(adjusted_values['PM1.0'], normalized_mean, 25), 0.05, 0.1))
            },
            'PM2.5': {
                'value': max(0, add_sensor_noise(exp_scale(adjusted_values['PM2.5'], normalized_mean, 30), 0.05, 0.1))
            },
            'PM10': {
                'value': max(0, add_sensor_noise(exp_scale(adjusted_values['PM10'], normalized_mean, 40), 0.05, 0.1))
            }
        }

    def predict(self, date_str: str, lat: float, lon: float, time_str: str = None) -> Dict:
        """
        Make high-accuracy environmental predictions.

        Args:
            date_str: Date string in YYYYMMDD format
            lat: Latitude in degrees
            lon: Longitude in degrees
            time_str: Time string in HH:MM format (optional)

        Returns:
            Dictionary containing predicted environmental parameters and metadata
        """
        try:
            dt = datetime.strptime(f"{date_str} {time_str if time_str else '00:00'}", "%Y%m%d %H:%M")
            input_patch = self._generate_synthetic_patch(lat, lon, dt)
            pred = self.model.predict(input_patch[np.newaxis, ...], verbose=0)[0]
            mean_pred = pred[..., 0]
            uncertainty = pred[..., 1]
            pred_mean = np.mean(mean_pred)
            pred_range = np.max(mean_pred) - np.min(mean_pred)
            normalized_mean = (pred_mean - np.min(mean_pred)) / (pred_range + 1e-7)
            region_type = self._determine_region_type(lat, lon)
            base_values = self.regional_base_values[region_type]
            adjusted_values = self._apply_temporal_adjustments(base_values, dt, region_type)
            results = self._calculate_enhanced_values(normalized_mean, adjusted_values)
            results = self._apply_physics_constraints(results, lat, lon, dt)
            results['metadata'] = {
                'latitude': lat,
                'longitude': lon,
                'date': date_str,
                'time': time_str if time_str else '00:00',
                'season': self._datetime_to_features(dt)['season'],
                'time_of_day': self._datetime_to_features(dt)['time_of_day'],
                'normalized_activity': float(normalized_mean),
                'uncertainty': float(np.mean(uncertainty))
            }
            return results
        except ValueError as e:
            return {'error': str(e), 'message': 'Invalid date/time format or input values'}
        except Exception as e:
            return {'error': str(e), 'message': 'Prediction failed'}