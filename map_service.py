from google.maps import places_v1
from google.type import latlng_pb2
from config import config

def construct_request(latitude: float, longitude: float, radius: int = 1000) -> places_v1.SearchNearbyRequest:
    """Construct a Google Maps Places API request"""
    location = latlng_pb2.LatLng(latitude=latitude, longitude=longitude)
    circle = places_v1.types.Circle(center=location, radius=radius)
    restriction = places_v1.SearchNearbyRequest.LocationRestriction(circle=circle)
    return places_v1.SearchNearbyRequest(location_restriction=restriction, included_types=["restaurant"], language_code="zh-TW")

def nearby_search(latitude: float, longitude: float, radius: int = 1000) -> list[dict]:
    """Perform a nearby search using Google Maps Places API"""
    request = construct_request(latitude, longitude, radius)
    client = places_v1.PlacesClient(client_options={"api_key": config.GOOGLE_MAP_API_KEY})

    field_mask = "places.displayName,places.formattedAddress,places.location,places.rating,places.priceLevel,places.types,places.id"
    response = client.search_nearby(request=request, metadata=[("x-goog-fieldmask",field_mask)])
    return response.places


    

