# Address Book API

A small address book API built with FastAPI, SQLAlchemy and SQLite. Addresses (with
coordinates) can be created, updated and deleted, and you can search for the ones
within a given distance of a point.

## Requirements

- Python 3.11+
- [pipenv](https://pipenv.pypa.io/) (`pip install pipenv`), or plain `venv` + `pip` (see below)

## Run

```bash
git clone https://github.com/fritzandal07/address-book
cd address-book

pipenv install --dev
pipenv run uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000 and the Swagger docs are at http://127.0.0.1:8000/docs.
The SQLite file (`address_book.db`) is created automatically on first start.

Without pipenv:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
pipenv run pytest                  # or just `pytest` inside the venv
```

## Endpoints

Full details and request/response examples are in Swagger (`/docs`).

- `POST /addresses`, `GET /addresses`, `GET /addresses/{address_id}`
- `PUT /addresses/{address_id}` replaces an address (all required fields)
- `PATCH /addresses/{address_id}` changes only the fields you send
- `DELETE /addresses/{address_id}`
- `GET /addresses/find_nearby?latitude=..&longitude=..&distance_km=..` returns the
  addresses within the radius, nearest first

## Notes

- Nearby searches first filter possible matches in SQL using a latitude/longitude bounding box, then calculate the exact Haversine distance in Python.
- PATCH and PUT use separate schemas. PATCH allows partial updates with optional fields, while required fields cannot be set to null; PUT requires the complete address.
- The DATABASE_URL and LOG_LEVEL settings can be customized through environment variables.