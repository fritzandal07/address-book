import math

EARTH_RADIUS_KM = 6371.0088  # mean Earth radius


def calculate_distance_km(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """Great-circle distance in kilometres between two coordinates (Haversine)"""
    lat1, lon1 = math.radians(latitude1), math.radians(longitude1)
    lat2, lon2 = math.radians(latitude2), math.radians(longitude2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2

    # min() guards against floating-point rounding pushing sqrt(a) above 1
    return EARTH_RADIUS_KM * 2 * math.asin(min(1.0, math.sqrt(a)))


def bounding_box(lat: float, lon: float, distance_km: float) -> tuple[float, float, float | None, float | None]:

    lat_delta = math.degrees(distance_km / EARTH_RADIUS_KM)
    min_lat, max_lat = max(-90.0, lat - lat_delta), min(90.0, lat + lat_delta)

    if abs(lat) + lat_delta >= 90:
        return min_lat, max_lat, None, None

    lon_delta = math.degrees(distance_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat))))
    min_lon, max_lon = lon - lon_delta, lon + lon_delta
    if min_lon < -180 or max_lon > 180:
        return min_lat, max_lat, None, None
    return min_lat, max_lat, min_lon, max_lon