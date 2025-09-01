import logging

from app.http_client import get_http_client_manager
from app.schemas.place import PlaceDetailsSchema, PlaceSearchSchema

logger = logging.getLogger(__name__)


async def search_places(query: str, language: str = "en") -> list[PlaceSearchSchema]:
    """Search for places by name using the API.

    Args:
        query: Search query for place names
        language: Language code for search results

    Returns:
        List[PlaceSearchSchema]: List of matching places with names and place IDs

    """
    http_client = get_http_client_manager()
    response = await http_client.get(
        "/v1/places/search",
        params={"query": query, "language": language},
    )
    response.raise_for_status()
    places_data = response.json()
    logger.debug(f"Found {len(places_data)} places for query '{query}'")

    return [PlaceSearchSchema.model_validate(place) for place in places_data]


async def get_place_details(
    place_id: str,
    language: str = "en",
) -> PlaceDetailsSchema:
    """Get detailed place information by place ID using the API.

    Args:
        place_id: Google Maps place ID
        language: Language code for place name

    Returns:
        PlaceDetailsSchema: Detailed place information

    """
    http_client = get_http_client_manager()
    response = await http_client.get(
        f"/v1/places/{place_id}",
        params={"language": language},
    )
    response.raise_for_status()
    place_data = response.json()
    logger.debug(f"Retrieved place details for ID: {place_id}")

    return PlaceDetailsSchema.model_validate(place_data)


async def get_place_by_coordinates(
    latitude: float,
    longitude: float,
    language: str = "en",
) -> PlaceDetailsSchema:
    """Get place information by coordinates using the API.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        language: Language code for place name

    Returns:
        PlaceDetailsSchema: Detailed place information

    """
    http_client = get_http_client_manager()
    response = await http_client.post(
        "/v1/places/coordinates",
        json={"latitude": latitude, "longitude": longitude},
        params={"language": language},
    )
    response.raise_for_status()
    place_data = response.json()
    logger.debug(f"Retrieved place details for coordinates ({latitude}, {longitude})")

    return PlaceDetailsSchema.model_validate(place_data)


async def get_place_name(place_id: str, language: str = "en") -> str | None:
    """Get place name by place ID using the API.

    Args:
        place_id: Google Maps place ID
        language: Language code for place name

    Returns:
        str | None: Place name or None if not found

    """
    if not place_id:
        return None

    http_client = get_http_client_manager()
    response = await http_client.get(
        f"/v1/places/{place_id}/name",
        params={"language": language},
    )
    response.raise_for_status()
    place_data = response.json()
    logger.debug(f"Retrieved place name for ID: {place_id}")

    return place_data.get("name")
