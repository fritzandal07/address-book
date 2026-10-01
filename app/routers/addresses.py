"""HTTP endpoints for managing addresses."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/addresses", tags=["addresses"])

# Shared description for the {address_id} path parameter (it is the address's `id` field)
AddressId = Path(..., description="The `id` of the address")


def _get_or_404(db: Session, address_id: int):
    address = crud.get_address(db, address_id)
    if address is None:
        logger.warning("Address id=%s not found", address_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address


@router.post("", response_model=schemas.AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(data: schemas.AddressCreate, db: Session = Depends(get_db)):
    """Create a new address"""
    return crud.create_address(db, data)


@router.get("", response_model=list[schemas.AddressRead])
def list_addresses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List addresses with simple pagination"""
    return crud.list_addresses(db, skip, limit)


@router.get("/find_nearby", response_model=list[schemas.AddressWithDistance])
def get_nearby_addresses(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude of the centre point"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude of the centre point"),
    distance_km: float = Query(..., gt=0, le=20040, description="Search radius in kilometres"),
    db: Session = Depends(get_db),
):
    """Return addresses within distance_km of the given coordinates, nearest first"""
    return [
        schemas.AddressWithDistance(
            **schemas.AddressRead.model_validate(address).model_dump(),
            distance_km=round(distance, 3),
        )
        for address, distance in crud.find_nearby(db, latitude, longitude, distance_km)
    ]


@router.get("/{address_id}", response_model=schemas.AddressRead)
def read_address(address_id: int = AddressId, db: Session = Depends(get_db)):
    """Get a single address by id"""
    return _get_or_404(db, address_id)


@router.put("/{address_id}", response_model=schemas.AddressRead)
def replace_address(
    data: schemas.AddressCreate,
    address_id: int = AddressId,
    db: Session = Depends(get_db),
):
    """Replace address (PUT): send every required field.

    Optional fields left out (state, postal_code) are cleared"""
    return crud.update_address(db, _get_or_404(db, address_id), data, partial=False)


@router.patch("/{address_id}", response_model=schemas.AddressRead)
def update_address(
    data: schemas.AddressUpdate,
    address_id: int = AddressId,
    db: Session = Depends(get_db),
):
    """Partially update an address (PATCH): send only the fields to change"""
    return crud.update_address(db, _get_or_404(db, address_id), data, partial=True)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int = AddressId, db: Session = Depends(get_db)):
    """Delete address"""
    crud.delete_address(db, _get_or_404(db, address_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
