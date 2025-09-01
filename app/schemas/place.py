from pydantic import BaseModel


class PlaceSearchSchema(BaseModel):
    """Schema for place search results."""

    name: str
    place_id: str


class PlaceDetailsSchema(BaseModel):
    """Schema for detailed place information."""

    place_id: str
    latitude: float
    longitude: float
    name: str


class CoordinatesSchema(BaseModel):
    """Schema for coordinates request."""

    latitude: float
    longitude: float
