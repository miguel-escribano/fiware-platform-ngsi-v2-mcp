#!/usr/bin/env python3
"""
FIWARE MCP Server - NGSI-v2 API with Multiple Authentication Methods

Original: https://github.com/dncampo/FIWARE-MCP-Server (NGSI-LD, no auth)
This fork: NGSI-v2 + Multiple authentication methods (OAuth, Basic Auth, None)
"""

import os
import json
import sys
import argparse
from typing import Optional
import requests
from requests.auth import HTTPBasicAuth
from fastmcp import FastMCP
from dotenv import load_dotenv
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load .env from the MCP's directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

mcp = FastMCP("FIWARE Context Broker Assistant")

# Configuration from .env
AUTH_TYPE = os.getenv("AUTH_TYPE", "oauth").lower()  # oauth, basic, or none
AUTH_HOST = os.getenv("AUTH_HOST", "localhost")
AUTH_PORT = os.getenv("AUTH_PORT", "15001")
CB_HOST = os.getenv("CB_HOST", "localhost")
CB_PORT = os.getenv("CB_PORT", "1026")
CB_PROTOCOL = os.getenv("CB_PROTOCOL", "https")  # http or https
USERNAME = os.getenv("FIWARE_USERNAME", "")
PASSWORD = os.getenv("FIWARE_PASSWORD", "")
SERVICE = os.getenv("SERVICE", "")
SUBSERVICE = os.getenv("SUBSERVICE", "/")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

# STH-Comet (Historical Data)
STH_HOST = os.getenv("STH_HOST", CB_HOST)  # Default to CB_HOST for single-server setups
STH_PORT = os.getenv("STH_PORT", "8666")

# Perseo CEP (Rules Engine)
CEP_HOST = os.getenv("CEP_HOST", CB_HOST)
CEP_PORT = os.getenv("CEP_PORT", "9090")

# IoT Agent Manager
IOTA_HOST = os.getenv("IOTA_HOST", CB_HOST)
IOTA_PORT = os.getenv("IOTA_PORT", "4041")

# Debug log
print(f"[FIWARE-MCP] AUTH_TYPE={AUTH_TYPE}, CB_HOST={CB_HOST}:{CB_PORT}, PROTOCOL={CB_PROTOCOL}", file=sys.stderr)

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
    """Make authenticated request based on AUTH_TYPE"""
    headers = {
        "Accept": "application/json",
        "Fiware-Service": SERVICE,
        "Fiware-ServicePath": SUBSERVICE,
    }
    
    if method.upper() in ["POST", "PUT", "PATCH"]:
        headers["Content-Type"] = "application/json"
    
    # Determine authentication method
    auth = None
    verify_ssl = False
    
    if AUTH_TYPE == "oauth":
        # OAuth with OpenStack Keystone
        token = get_auth_token()
        if token:
            headers["x-auth-token"] = token
        response = requests.request(method, url, headers=headers, json=body, timeout=10, verify=verify_ssl)
        
        # Auto-refresh token on 401
        if response.status_code == 401:
            print("Token expired, refreshing...", file=sys.stderr)
            refresh_token()
            headers["x-auth-token"] = get_auth_token()
            response = requests.request(method, url, headers=headers, json=body, timeout=10, verify=verify_ssl)
        
        return response
    
    elif AUTH_TYPE == "basic":
        # HTTP Basic Authentication
        auth = HTTPBasicAuth(USERNAME, PASSWORD)
        return requests.request(method, url, headers=headers, json=body, auth=auth, timeout=10, verify=verify_ssl)
    
    elif AUTH_TYPE == "none":
        # No authentication
        return requests.request(method, url, headers=headers, json=body, timeout=10, verify=verify_ssl)
    
    else:
        raise ValueError(f"Invalid AUTH_TYPE: {AUTH_TYPE}. Must be 'oauth', 'basic', or 'none'.")


@mcp.resource("fiware://examples")
def get_api_examples() -> str:
    """FIWARE NGSI-v2 API example collection (Postman format)"""
    try:
        with open("resources/fiware-ngsi-v2-examples.json", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({"error": "Example collection not found"})


@mcp.tool()
def CB_version() -> str:
    """Check Context Broker version"""
    try:
        url = f"{CB_PROTOCOL}://{CB_HOST}:{CB_PORT}/version"
        response = make_request("GET", url)
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
        url = f"{CB_PROTOCOL}://{CB_HOST}:{CB_PORT}{endpoint}"
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


# =============================================================================
# STH-COMET - Historical Data
# =============================================================================

@mcp.tool()
def sth_get_history(entity_type: str, entity_id: str, attribute: str,
                    last_n: int = 20, date_from: str = None, date_to: str = None) -> str:
    """
    Get historical raw values for an entity attribute from STH-Comet.
    
    Args:
        entity_type: Entity type (e.g., "AirQualityObserved")
        entity_id: Entity ID (e.g., "AirQualityObserved:Pamplona:001")
        attribute: Attribute name (e.g., "pm25", "temperature")
        last_n: Number of last values to retrieve (default 20)
        date_from: Start date ISO format (e.g., "2026-01-01T00:00:00.000Z")
        date_to: End date ISO format (e.g., "2026-01-17T23:59:59.999Z")
    
    Returns:
        Historical values with timestamps
    
    Example:
        sth_get_history("AirQualityObserved", "sensor:001", "pm25", last_n=100)
    """
    try:
        url = f"{CB_PROTOCOL}://{STH_HOST}:{STH_PORT}/STH/v1/contextEntities/type/{entity_type}/id/{entity_id}/attributes/{attribute}"
        
        params = []
        if date_from:
            params.append(f"dateFrom={date_from}")
        if date_to:
            params.append(f"dateTo={date_to}")
        params.append(f"lastN={last_n}")
        
        if params:
            url += "?" + "&".join(params)
        
        response = make_request("GET", url)
        
        try:
            data = response.json() if response.text else None
        except:
            data = response.text
        
        result = {
            "success": response.ok,
            "status_code": response.status_code,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "attribute": attribute,
        }
        
        if response.ok:
            result["data"] = data
            # Extract values count if available
            if data and "contextResponses" in data:
                try:
                    values = data["contextResponses"][0]["contextElement"]["attributes"][0]["values"]
                    result["values_count"] = len(values)
                except:
                    pass
        else:
            result["error"] = data or response.reason
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def sth_get_aggregation(entity_type: str, entity_id: str, attribute: str,
                        aggr_method: str, aggr_period: str,
                        date_from: str = None, date_to: str = None) -> str:
    """
    Get aggregated historical data from STH-Comet.
    
    Args:
        entity_type: Entity type (e.g., "AirQualityObserved")
        entity_id: Entity ID
        attribute: Attribute name (e.g., "temperature")
        aggr_method: Aggregation method: "max", "min", "sum", "sum2" (for std dev)
        aggr_period: Aggregation period: "hour", "day", "month"
        date_from: Start date ISO format
        date_to: End date ISO format
    
    Returns:
        Aggregated values by period
    
    Example:
        sth_get_aggregation("WeatherObserved", "sensor:001", "temperature", "max", "hour")
    """
    try:
        url = f"{CB_PROTOCOL}://{STH_HOST}:{STH_PORT}/STH/v1/contextEntities/type/{entity_type}/id/{entity_id}/attributes/{attribute}"
        
        params = [f"aggrMethod={aggr_method}", f"aggrPeriod={aggr_period}"]
        if date_from:
            params.append(f"dateFrom={date_from}")
        if date_to:
            params.append(f"dateTo={date_to}")
        
        url += "?" + "&".join(params)
        
        response = make_request("GET", url)
        
        try:
            data = response.json() if response.text else None
        except:
            data = response.text
        
        result = {
            "success": response.ok,
            "status_code": response.status_code,
            "aggregation": {
                "method": aggr_method,
                "period": aggr_period
            }
        }
        
        if response.ok:
            result["data"] = data
        else:
            result["error"] = data or response.reason
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# PERSEO CEP - Complex Event Processing
# =============================================================================

@mcp.tool()
def cep_list_rules() -> str:
    """
    List all CEP rules in Perseo.
    
    Returns:
        List of configured rules with their definitions
    """
    try:
        url = f"{CB_PROTOCOL}://{CEP_HOST}:{CEP_PORT}/rules"
        response = make_request("GET", url)
        
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
            if isinstance(data, dict) and "data" in data:
                result["rules_count"] = len(data.get("data", []))
        else:
            result["error"] = data or response.reason
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def cep_create_rule(name: str, epl_text: str, action_type: str, action_params: dict) -> str:
    """
    Create a new CEP rule in Perseo.
    
    Args:
        name: Rule name (unique identifier)
        epl_text: EPL (Event Processing Language) query
        action_type: Action type: "email", "update", "post", "sms"
        action_params: Action parameters (depends on action_type)
    
    Action parameters by type:
        email: {"to": "email@example.com", "from": "noreply@...", "subject": "..."}
        update: {"id": "entity_id", "type": "entity_type", "attributes": [{"name": "...", "value": "..."}]}
        post: {"url": "http://..."}
    
    EPL Example:
        select *,"HighTemperature" as ruleName from pattern [every ev=iotEvent(
            (cast(`type`?, String) = "Room") AND 
            (cast(cast(`temperature`?, String), float) > 30)
        )]
    
    Returns:
        Created rule confirmation
    """
    try:
        url = f"{CB_PROTOCOL}://{CEP_HOST}:{CEP_PORT}/rules"
        
        body = {
            "name": name,
            "text": epl_text,
            "action": {
                "type": action_type,
                "parameters": action_params
            }
        }
        
        # Add template if provided in params
        if "template" in action_params:
            body["action"]["template"] = action_params.pop("template")
        
        response = make_request("POST", url, body)
        
        try:
            data = response.json() if response.text else None
        except:
            data = response.text
        
        return json.dumps({
            "success": response.ok,
            "status_code": response.status_code,
            "rule_name": name,
            "data": data if response.ok else None,
            "error": data if not response.ok else None
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def cep_delete_rule(rule_name: str) -> str:
    """
    Delete a CEP rule from Perseo.
    
    Args:
        rule_name: Name of the rule to delete
    
    Returns:
        Deletion confirmation
    """
    try:
        url = f"{CB_PROTOCOL}://{CEP_HOST}:{CEP_PORT}/rules/{rule_name}"
        response = make_request("DELETE", url)
        
        return json.dumps({
            "success": response.ok,
            "status_code": response.status_code,
            "deleted_rule": rule_name if response.ok else None,
            "error": response.text if not response.ok else None
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# IOT AGENTS - Device Management
# =============================================================================

@mcp.tool()
def iota_list_devices() -> str:
    """
    List all registered IoT devices.
    
    Returns:
        List of devices with their configurations
    """
    try:
        url = f"{CB_PROTOCOL}://{IOTA_HOST}:{IOTA_PORT}/iot/devices"
        response = make_request("GET", url)
        
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
            if isinstance(data, dict) and "devices" in data:
                result["devices_count"] = len(data.get("devices", []))
        else:
            result["error"] = data or response.reason
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def iota_register_device(device_id: str, entity_name: str, entity_type: str,
                         attributes: list, protocol: str = "IoTA-UL",
                         transport: str = "HTTP") -> str:
    """
    Register a new IoT device.
    
    Args:
        device_id: Unique device identifier
        entity_name: Entity name in Context Broker
        entity_type: Entity type (e.g., "Room", "Sensor")
        attributes: List of attribute mappings [{"object_id": "t", "name": "temperature", "type": "float"}]
        protocol: "IoTA-UL" (UltraLight) or "IoTA-JSON"
        transport: "HTTP" or "MQTT"
    
    Returns:
        Registration confirmation
    
    Example:
        iota_register_device(
            device_id="sensor001",
            entity_name="Room:001",
            entity_type="Room",
            attributes=[
                {"object_id": "t", "name": "temperature", "type": "float"},
                {"object_id": "h", "name": "humidity", "type": "float"}
            ]
        )
    """
    try:
        url = f"{CB_PROTOCOL}://{IOTA_HOST}:{IOTA_PORT}/iot/devices"
        
        device = {
            "device_id": device_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "attributes": attributes,
            "protocol": protocol,
            "transport": transport
        }
        
        body = {"devices": [device]}
        
        response = make_request("POST", url, body)
        
        try:
            data = response.json() if response.text else None
        except:
            data = response.text
        
        return json.dumps({
            "success": response.ok,
            "status_code": response.status_code,
            "device_id": device_id,
            "data": data if response.ok else None,
            "error": data if not response.ok else None
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def iota_delete_device(device_id: str, protocol: str = "IoTA-UL") -> str:
    """
    Delete/deregister an IoT device.
    
    Args:
        device_id: Device identifier to delete
        protocol: Protocol type ("IoTA-UL" or "IoTA-JSON")
    
    Returns:
        Deletion confirmation
    """
    try:
        url = f"{CB_PROTOCOL}://{IOTA_HOST}:{IOTA_PORT}/iot/devices/{device_id}?protocol={protocol}"
        response = make_request("DELETE", url)
        
        return json.dumps({
            "success": response.ok,
            "status_code": response.status_code,
            "deleted_device": device_id if response.ok else None,
            "error": response.text if not response.ok else None
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def iota_list_services() -> str:
    """
    List all provisioned IoT Agent service configurations.
    
    Returns:
        List of service groups with their API keys and configurations
    """
    try:
        url = f"{CB_PROTOCOL}://{IOTA_HOST}:{IOTA_PORT}/iot/services"
        response = make_request("GET", url)
        
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
            if isinstance(data, dict) and "services" in data:
                result["services_count"] = len(data.get("services", []))
        else:
            result["error"] = data or response.reason
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# SMART DATA MODELS
# =============================================================================

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
