import pytest
from envpredictor import HighAccuracyEnvironmentalPredictor
import os

def test_predictor_initialization():
    model_path = "path/to/dummy/model.keras"  # Replace with actual path for testing
    if not os.path.exists(model_path):
        pytest.skip("Model file not found")
    predictor = HighAccuracyEnvironmentalPredictor(model_path)
    assert predictor is not None

def test_predict():
    model_path = "path/to/dummy/model.keras"  # Replace with actual path for testing
    if not os.path.exists(model_path):
        pytest.skip("Model file not found")
    predictor = HighAccuracyEnvironmentalPredictor(model_path)
    result = predictor.predict("20251212", 11.0, 77.0, "08:00")
    assert isinstance(result, dict)
    if 'error' not in result:
        assert 'BME688' in result
        assert 'metadata' in result