import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils import bounding_box, calculate_distance_km
logger = logging.getLogger(__name__)


def get_address(db: Session, address_id: int) -> models.Address | None:
    return db.get(models.Address, address_id)


def list_addresses(db: Session, skip: int = 0, limit: int = 100) -> list[models.Address]:
    stmt = select(models.Address).order_by(models.Address.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def create_address(db: Session, data: schemas.AddressCreate) -> models.Address:
    address = models.Address(**data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    logger.info("Created address id=%s", address.id)
    return address


def update_address(
    db: Session,
    address: models.Address,
    data: schemas.AddressCreate | schemas.AddressUpdate,
    partial: bool = True,
) -> models.Address:
    """Update address

    - partial=True (PATCH): only the fields the client sent are changed
    - partial=False (PUT): every field is overwritten, so omitted optional
      fields (state, postal_code) reset to None"""
    for field, value in data.model_dump(exclude_unset=partial).items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    logger.info("Updated address id=%s", address.id)
    return address


def delete_address(db: Session, address: models.Address) -> None:
    address_id = address.id
    db.delete(address)
    db.commit()
    logger.info("Deleted address id=%s", address_id)


def find_nearby(
    db: Session, latitude: float, longitude: float, distance_km: float
) -> list[tuple[models.Address, float]]:
    """Return (address, distance_km) pairs within ``distance_km``, nearest first.

    - Bounding-box query narrows candidates using the DB index
    - Exact Haversine check removes the box's corners"""
    
    min_lat, max_lat, min_lon, max_lon = bounding_box(latitude, longitude, distance_km)
    stmt = select(models.Address).where(models.Address.latitude.between(min_lat, max_lat))
    if min_lon is not None and max_lon is not None:
        stmt = stmt.where(models.Address.longitude.between(min_lon, max_lon))

    results = []
    for address in db.scalars(stmt):
        distance = calculate_distance_km(latitude, longitude, address.latitude, address.longitude)
        if distance <= distance_km:
            results.append((address, distance))
    results.sort(key=lambda pair: pair[1])
    logger.info(
        "Nearby search (lat=%s, lon=%s, radius=%skm) -> %d result(s)",
        latitude, longitude, distance_km, len(results),
    )
    return results