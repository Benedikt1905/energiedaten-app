DATA_FILE = 'data/Primärverbrauch FR.json'
import json
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
from pydantic import BaseModel  # Make sure 'pydantic' is installed: pip install pydantic
import requests

# Load data from file
try:
    with open(DATA_FILE, encoding='utf-8') as file:
        try:
            data = json.load(file)
            # Check if data is a dictionary with years as keys
            if not isinstance(data, dict):
                print("Data is not a dictionary.")
                data = {}
        except json.JSONDecodeError:
            print("Could not parse data from file.")
            exit(1)
except FileNotFoundError:
    print("File not found.")
    exit(1)


# Create FastAPI app
app = FastAPI(
    title="Primary Energy Consumption API",
    description="API for primary energy consumption data",
    version="2.0",
    contact={"name": "Benedikt Krings",
             "url": "http://localhost:8000/api/1/primary_energy_consumption",
             "email": "bkkrings@root.de"},
    last_updated="2024-06-01"
)


# Define route for data retrieval
@app.get("/api/1/primary_energy_consumption")
async def get_primary_energy_consumption(
    page: int = Query(1, alias='page', description="Page number"),
    limit: int = Query(10, alias='limit', description="Number of items per page")
):
    """Get primary energy consumption data."""    
    total_data = len(data)
    start = (page - 1) * limit
    end = start + limit
    items = {year: data[year] for year in list(data)[start:end]}
    
    return {
        "info": {
            "page": page,
            "limit": limit,
            "total": total_data,
            "pages": (total_data + limit - 1) // limit,  # rounds up
            "next": f"/api/1/primary_energy_consumption?page={page + 1}&limit={limit}" if end < total_data else None,
            "previous": f"/api/1/primary_energy_consumption?page={page - 1}&limit={limit}" if page > 1 else None
        },
        "data": items
    }


# Define route for API info
@app.get("/api/1/info", response_model=Dict[str, Any])
async def get_api_info():
    """Get information about the API."""
    return {
        "name": "Primary Energy Consumption API",
        "version": "2.0",
        "description": "API for primary energy consumption data",
        "author": "Benedikt Krings",
        "last_updated": "2025-05-14",
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

url = "http://localhost:8000/api/1/primary_energy_consumption?page=1&limit=10"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print(data["data"])  # Hier sind die Energiedaten
else:
    print("Fehler beim Abrufen der Daten:", response.status_code)
