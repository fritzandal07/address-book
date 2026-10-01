from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TEXT_FIELDS = ("name", "street", "city", "state", "postal_code", "country")


def _strip_whitespace(value):
    """Trim text so '   ' is rejected as empty by min_length"""
    return value.strip() if isinstance(value, str) else value


class AddressBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Head Office"])
    street: str = Field(..., min_length=1, max_length=255, examples=["123 Shoe Avenue"])
    city: str = Field(..., min_length=1, max_length=100, examples=["Marikina"])
    state: str | None = Field(None, max_length=100, examples=["Metro Manila"])
    postal_code: str | None = Field(None, max_length=20, examples=["1800"])
    country: str = Field(..., min_length=1, max_length=100, examples=["Philippines"])
    latitude: float = Field(..., ge=-90, le=90, examples=[14.6507])
    longitude: float = Field(..., ge=-180, le=180, examples=[121.1029])

    _strip = field_validator(*_TEXT_FIELDS, mode="before")(_strip_whitespace)


class AddressCreate(AddressBase):
    """Payload for creating (POST) or replacing (PUT) an address"""


class AddressUpdate(BaseModel):
    """Payload for partial updates (PATCH): send only the fields you want to change"""

    model_config = ConfigDict(
        extra="forbid",  # unknown fields return 422 instead of being ignored
        json_schema_extra={"examples": [{"city": "Pasig", "postal_code": "1600"}]},
    )

    name: str | None = Field(None, min_length=1, max_length=100)
    street: str | None = Field(None, min_length=1, max_length=255)
    city: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, min_length=1, max_length=100)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    _strip = field_validator(*_TEXT_FIELDS, mode="before")(_strip_whitespace)

    @field_validator("name", "street", "city", "country", "latitude", "longitude")
    @classmethod
    def _required_fields_not_null(cls, value):
        """These columns are NOT NULL, so an explicit null is rejected (422, not 500)"""
        if value is None:
            raise ValueError("cannot be null")
        return value


class AddressRead(AddressBase):
    """Address returned by the API"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AddressWithDistance(AddressRead):
    """Address returned by the nearby search with distance"""

    distance_km: float