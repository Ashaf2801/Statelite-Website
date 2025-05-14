import hashlib

def generate_deterministic_variation(lat: float, lon: float, dt, param: str, scale: float) -> float:
    """Generate a small deterministic variation based on input parameters."""
    input_str = f"{lat:.6f}_{lon:.6f}_{dt.strftime('%Y%m%d%H%M%S')}_{param}"
    hash_obj = hashlib.sha256(input_str.encode())
    hash_value = int(hash_obj.hexdigest(), 16)
    normalized = (hash_value % 10000) / 10000.0 * 2 - 1
    return normalized * scale