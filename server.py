#!/usr/bin/env python3
"""
FIWARE MCP Server - NGSI-v2 API with OAuth Authentication

Original: https://github.com/dncampo/FIWARE-MCP-Server (NGSI-LD, no auth)
This fork: NGSI-v2 + OpenStack Keystone authentication
"""

import os
import json
import sys
import argparse
from typing import Optional
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

mcp = FastMCP("FIWARE Context Broker Assistant")

# Configuration from .env
AUTH_HOST = os.getenv("AUTH_HOST", "localhost")
AUTH_PORT = os.getenv("AUTH_PORT", "15001")
CB_HOST = os.getenv("CB_HOST", "localhost")
CB_PORT = os.getenv("CB_PORT", "1026")
USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")
SERVICE = os.getenv("SERVICE", "")
SUBSERVICE = os.getenv("SUBSERVICE", "/")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

_token_cache = AUTH_TOKEN if AUTH_TOKEN else None


def refresh_token() -> Optional[str]:
    global _token_cache
    _token_cache = None
    return get_auth_token()


def get_auth_token() -> Optional[str]:
    """Get OAuth token using OpenStack Keystone password auth"""
    global _token_cache
    if _token_cache:
        return _token_cache
    
    try:
        url = f"https://{AUTH_HOST}:{AUTH_PORT}/v3/auth/tokens"
        payload = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "domain": {"name": SERVICE},
                            "name": USERNAME,
                            "password": PASSWORD
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {"name": SERVICE},
                        "name": SUBSERVICE
                    }
                }
            }
        }
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10, verify=False)
        response.raise_for_status()
        _token_cache = response.headers.get("X-Subject-Token")
        return _token_cache
    except Exception as e:
        print(f"Auth error: {e}", file=sys.stderr)
        return None


def make_request(method: str, url: str, body: dict = None) -> requests.Response:
    """Make authenticated request with auto token refresh on 401"""
    headers = {
        "Accept": "application/json",
        "fiware-service": SERVICE,
        "fiware-servicepath": SUBSERVICE,
    }
    
    token = get_auth_token()
    if token:
        headers["x-auth-token"] = token
    
    if method.upper() in ["POST", "PUT", "PATCH"]:
        headers["Content-Type"] = "application/json"
    
    response = requests.request(method, url, headers=headers, json=body, timeout=10, verify=False)
    
    if response.status_code == 401:
        print("Token expired, refreshing...", file=sys.stderr)
        refresh_token()
        headers["x-auth-token"] = get_auth_token()
        response = requests.request(method, url, headers=headers, json=body, timeout=10, verify=False)
    
    return response


@mcp.resource("fiware://examples")
def get_api_examples() -> str:
    """FIWARE NGSI-v2 API example collection (Postman format)"""
    try:
        with open("postman/fiware-ngsi-v2-examples.json", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({"error": "Example collection not found"})


@mcp.prompt()
def create_fiware_entity():
    """Guide to create a FIWARE entity following Smart Data Models"""
    return """To create a FIWARE-compliant entity:

1. **Find the right Smart Data Model:**
   Use: get_smart_data_model(domain, model)
   
   Common models:
   - Environment: AirQualityObserved, NoiseLevelObserved, WaterQualityObserved
   - Weather: WeatherObserved, WeatherForecast
   - Alert: Alert, Anomaly
   - Building: Building, BuildingOperation
   
   Example: get_smart_data_model("Environment", "AirQualityObserved")

2. **Check the Postman examples:**
   Read resource: fiware://examples
   Look for similar entity creation examples

3. **Create the entity in NGSI-v2 format:**
   Use: fiware_request("POST", "/v2/entities", entity_data)
   
   Format: {"id": "Type:ID", "type": "Type", "attr": {"value": X, "type": "Number|Text"}}

4. **Required attributes from Smart Data Model:**
   - Always include: id, type
   - Check 'required' field from get_smart_data_model output
   - Use proper NGSI-v2 attribute format

Remember: Smart Data Models ensure interoperability across FIWARE platforms!
"""


@mcp.prompt()
def query_fiware_entities():
    """Guide to query FIWARE entities effectively"""
    return """To query FIWARE entities:

1. **Check available examples:**
   Read resource: fiware://examples
   Section: "GET /v2/entities" examples

2. **Basic queries:**
   - List all: fiware_request("GET", "/v2/entities")
   - By type: fiware_request("GET", "/v2/entities?type=Room")
   - By ID: fiware_request("GET", "/v2/entities/Room:001")

3. **Advanced filtering:**
   - Attribute filter: ?q=temperature>20
   - Select attributes: ?attrs=temperature,pressure
   - Pagination: ?limit=10&offset=20
   - Ordering: ?orderBy=temperature

4. **Geospatial queries:**
   - Near point: ?georel=near;maxDistance:1000&geometry=point&coords=-1.64,42.81
   - Within area: ?georel=coveredBy&geometry=polygon&coords=...

5. **Get entity types:**
   fiware_request("GET", "/v2/types")

Check the Postman collection (fiware://examples) for complete request examples!
"""


@mcp.prompt()
def use_smart_data_models():
    """Guide to using Smart Data Models in FIWARE"""
    return """Smart Data Models ensure your entities are interoperable and standardized.

**Step 1: Browse available models**
Use: get_smart_data_model(domain, model)

**Available domains:**
- Environment (air quality, water, noise, weather)
- Alert (alerts, anomalies, warnings)
- Weather (observations, forecasts)
- Building (structures, operations)
- Transportation (traffic, vehicles, roads)
- UrbanMobility (public transport, GTFS)
- WasteManagement (containers, collection)
- Streetlighting (lights, control cabinets)
- Energy (consumption, generation)
- ParksAndGardens (green spaces)

**Step 2: Get model details**
Example: get_smart_data_model("Environment", "AirQualityObserved")

Returns:
- Description and purpose
- Required attributes
- Available properties
- Example entity
- Link to full documentation

**Step 3: Convert to NGSI-v2**
Smart Data Models use JSON Schema. Convert to NGSI-v2:

Schema: "pm25": {"type": "number"}
NGSI-v2: "pm25": {"value": 12.5, "type": "Number"}

**Step 4: Create entity**
Use: fiware_request("POST", "/v2/entities", your_entity)

**Why use Smart Data Models?**
- Interoperability across platforms
- Standardized attributes
- Community-validated schemas
- Better data sharing

Learn more: https://smartdatamodels.org/
"""


@mcp.tool()
def CB_version() -> str:
    """Check Context Broker version"""
    try:
        url = f"https://{CB_HOST}:{CB_PORT}/version"
        response = requests.get(url, headers={"Accept": "application/json"}, timeout=10, verify=False)
        return json.dumps({"success": True, "version": response.json()}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def fiware_request(method: str, endpoint: str, body: dict = None) -> str:
    """
    Execute any FIWARE NGSI-v2 API request.
    
    Args:
        method: HTTP method (GET, POST, PATCH, PUT, DELETE)
        endpoint: API endpoint starting with / (e.g., "/v2/entities")
        body: Optional request body for POST/PATCH/PUT
    
    Examples:
        # Query entities
        GET /v2/entities                           - List all entities
        GET /v2/entities?type=Room                 - Filter by type
        GET /v2/entities?limit=10                  - Limit results
        GET /v2/entities?limit=10&offset=20        - Pagination
        GET /v2/entities?q=temperature>20          - Query by attribute value
        GET /v2/entities?attrs=temperature,pressure - Select specific attributes
        GET /v2/entities?orderBy=temperature       - Order results
        GET /v2/entities/{id}                      - Get entity by ID
        GET /v2/entities/{id}?attrs=temperature    - Get specific attributes
        GET /v2/entities/{id}/attrs/{attrName}     - Get single attribute
        
        # Entity types
        GET /v2/types                              - List all entity types
        GET /v2/types/{type}                       - Get type details
        
        # Create and modify entities
        POST /v2/entities                          - Create entity (with body)
        POST /v2/entities?options=keyValues        - Create with simplified format
        PATCH /v2/entities/{id}/attrs              - Update attributes (with body)
        PUT /v2/entities/{id}/attrs                - Replace all attributes (with body)
        PUT /v2/entities/{id}/attrs/{attrName}     - Update single attribute (with body)
        DELETE /v2/entities/{id}                   - Delete entity
        DELETE /v2/entities/{id}/attrs/{attrName}  - Delete single attribute
        
        # Subscriptions
        GET /v2/subscriptions                      - List subscriptions
        GET /v2/subscriptions/{id}                 - Get subscription details
        POST /v2/subscriptions                     - Create subscription (with body)
        PATCH /v2/subscriptions/{id}               - Update subscription (with body)
        DELETE /v2/subscriptions/{id}              - Delete subscription
        
        # Batch operations
        POST /v2/op/update                         - Batch update (with body)
        POST /v2/op/query                          - Batch query (with body)
    """
    try:
        url = f"https://{CB_HOST}:{CB_PORT}{endpoint}"
        response = make_request(method.upper(), url, body)
        
        try:
            data = response.json() if response.text else None
        except:
            data = response.text
        
        result = {
            "success": response.ok,
            "status_code": response.status_code,
        }
        
        if response.ok:
            result["data"] = data
            if isinstance(data, list):
                result["count"] = len(data)
                if len(data) > 20:
                    result["hint"] = "Many results. Try ?limit=10 or ?type=YourType"
        else:
            result["error"] = data or response.reason
            if response.status_code == 404:
                result["hint"] = "Not found. Check ID or try GET /v2/entities"
            elif response.status_code == 400:
                result["hint"] = "Bad request. Check endpoint and body format."
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_smart_data_model_domains() -> str:
    """
    List available Smart Data Model domains with common models.
    
    Returns:
        JSON with available domains and their most common models
    
    Use this to discover what domains and models are available before calling get_smart_data_model()
    """
    domains = {
        "Environment": ["AirQualityObserved", "NoiseLevelObserved", "WaterQualityObserved"],
        "Weather": ["WeatherObserved", "WeatherForecast", "WeatherAlert"],
        "Alert": ["Alert", "Anomaly"],
        "Building": ["Building", "BuildingOperation"],
        "Transportation": ["TrafficFlowObserved", "Road", "Vehicle"],
        "UrbanMobility": ["GtfsStop", "GtfsRoute", "PublicTransportStop"],
        "WasteManagement": ["WasteContainer", "WasteContainerIsle"],
        "Streetlighting": ["Streetlight", "StreetlightGroup", "StreetlightControlCabinet"],
        "Energy": ["Device", "ThreePhaseAcMeasurement"],
        "ParksAndGardens": ["Garden", "GreenspaceRecord"],
        "PointOfInterest": ["PointOfInterest", "Beach", "Museum"],
        "Parking": ["ParkingSpot", "ParkingGroup", "OffStreetParking"],
        "Device": ["Device", "DeviceModel"],
        "AgriFood": ["AgriCrop", "AgriParcel", "AgriGreenhouse"],
        "WaterNetwork": ["WaterQualityObserved", "WaterConsumptionObserved"]
    }
    
    return json.dumps({
        "success": True,
        "total_domains": len(domains),
        "domains": domains,
        "usage": "Use get_smart_data_model(domain, model) to get full schema",
        "example": "get_smart_data_model('Environment', 'AirQualityObserved')",
        "browse_all": "https://github.com/smart-data-models"
    }, indent=2)


@mcp.tool()
def get_smart_data_model(domain: str, model: str) -> str:
    """
    Get FIWARE Smart Data Model schema with NGSI-v2 conversion examples.
    
    Args:
        domain: Data model domain (e.g., "Environment", "Weather", "Alert")
        model: Model name (e.g., "AirQualityObserved", "WeatherObserved")
    
    Returns:
        Complete schema with properties, required fields, and NGSI-v2 conversion examples
    
    Examples:
        get_smart_data_model("Environment", "AirQualityObserved")
        get_smart_data_model("Weather", "WeatherObserved")
    
    Tip: Use list_smart_data_model_domains() first to see available options
    """
    try:
        # Fetch schema from GitHub
        schema_url = f"https://raw.githubusercontent.com/smart-data-models/dataModel.{domain}/master/{model}/schema.json"
        response = requests.get(schema_url, timeout=30)
        
        if response.status_code == 404:
            return json.dumps({
                "error": "Model not found",
                "hint": f"Domain '{domain}' or model '{model}' doesn't exist",
                "suggestion": "Use list_smart_data_model_domains() to see available options",
                "browse": "https://github.com/smart-data-models"
            }, indent=2)
        
        response.raise_for_status()
        schema = response.json()
        
        # Try to get example
        example_url = f"https://raw.githubusercontent.com/smart-data-models/dataModel.{domain}/master/{model}/examples/example.json"
        example_response = requests.get(example_url, timeout=5)
        example = example_response.json() if example_response.ok else None
        
        # Get property details (Smart Data Models use allOf structure)
        properties = {}
        if "allOf" in schema and len(schema["allOf"]) > 1:
            properties = schema["allOf"][1].get("properties", {})
        else:
            properties = schema.get("properties", {})
        
        # Build comprehensive property list with NGSI-v2 type mapping
        property_list = []
        type_mapping = {
            "string": "Text",
            "number": "Number",
            "integer": "Number",
            "boolean": "Boolean",
            "array": "StructuredValue",
            "object": "StructuredValue"
        }
        
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "unknown")
            ngsi_type = type_mapping.get(prop_type, "Text")
            
            # Special handling for geo properties
            if "geo" in prop_name.lower() or prop_name in ["location", "address"]:
                ngsi_type = "geo:json" if prop_type == "object" else "Text"
            
            property_list.append({
                "name": prop_name,
                "schema_type": prop_type,
                "ngsi_v2_type": ngsi_type,
                "description": prop_def.get("description", "")[:100]
            })
        
        # Generate NGSI-v2 conversion example
        required_fields = schema.get("required", [])
        conversion_example = {
            "id": f"urn:ngsi-ld:{model}:001",
            "type": model
        }
        
        # Add a few example attributes
        for prop in property_list[:3]:
            if prop["name"] not in ["id", "type"]:
                conversion_example[prop["name"]] = {
                    "type": prop["ngsi_v2_type"],
                    "value": "<your_value_here>"
                }
        
        result = {
            "success": True,
            "domain": domain,
            "model": model,
            "schema": {
                "title": schema.get("title", ""),
                "description": schema.get("description", ""),
                "required": required_fields,
                "total_properties": len(property_list),
                "properties": property_list
            },
            "ngsi_v2_conversion": {
                "note": "Convert each property to NGSI-v2 attribute format",
                "example": conversion_example,
                "required_fields": required_fields
            },
            "official_example": example,
            "links": {
                "schema": schema_url,
                "github": f"https://github.com/smart-data-models/dataModel.{domain}/tree/master/{model}",
                "spec": f"https://github.com/smart-data-models/dataModel.{domain}/blob/master/{model}/doc/spec.md"
            }
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "hint": "Check domain and model names"}, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    
    if args.http:
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
