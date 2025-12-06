# FIWARE MCP Server with Smart Data Models Integration

[![smithery badge](https://smithery.ai/badge/@miguel-escribano/fiware-mcp-server)](https://smithery.ai/server/@miguel-escribano/fiware-mcp-server)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FIWARE](https://img.shields.io/badge/FIWARE-NGSI--v2-orange.svg)](https://fiware.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

> **⚠️ Early Version**  
> This is a first release. While functional, there may be inconsistencies or areas for improvement. Feedback, suggestions, and contributions are welcome—feel free to open issues or reach out.

An MCP (Model Context Protocol) server for FIWARE NGSI-v2 Context Broker with Smart Data Models lookup and OpenStack Keystone OAuth authentication. This server enables AI assistants like Claude Desktop and Cursor to interact with FIWARE platforms while ensuring compliance with standardized, interoperable data models.

Forked from [dncampo/FIWARE-MCP-Server](https://github.com/dncampo/FIWARE-MCP-Server) (NGSI-LD, no auth).


## ✨ Features

- **Smart Data Models Integration**: Direct access to official FIWARE data model schemas for standardized entity creation
- **3 MCP Tools**: Context Broker operations, generic FIWARE API requests, and Smart Data Models lookup
- **1 MCP Resource**: Comprehensive API examples collection with real request/response patterns
- **3 MCP Prompts**: Guided workflows for creating entities, querying data, and using Smart Data Models
- **OAuth Authentication**: OpenStack Keystone integration for enterprise FIWARE platforms
- **NGSI-v2 API**: Full support for FIWARE NGSI-v2 specification


## 📦 Installation

This MCP server is designed for **local deployment** with your own FIWARE infrastructure and credentials. It connects to your specific Context Broker instance using your authentication details.

**Available on Smithery**: You can find this server in the [Smithery MCP Registry](https://smithery.ai), but it requires local installation and configuration with your FIWARE credentials.

See the [Integration](#integration) section below for step-by-step instructions.


## What's Different

This fork adapts the original NGSI-LD implementation to work with NGSI-v2 APIs and adds enterprise authentication support:

| Original | This Fork |
|----------|-----------|
| NGSI-LD (`/ngsi-ld/v1/`) | NGSI-v2 (`/v2/`) |
| No authentication | OpenStack Keystone OAuth |
| 5 specific tools | 3 tools + 1 resource + 3 prompts |
| No Smart Data Models | Smart Data Models integration |

---

## 🚀 Quick Start

> **Note:** This server requires local installation with your own FIWARE infrastructure. It is not a hosted service.

```bash
# Clone the repository
git clone https://github.com/miguel-escribano/FIWARE-MCP-Server.git
cd FIWARE-MCP-Server

# Install dependencies
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
```

Edit `.env` with your FIWARE platform credentials:

```env
AUTH_HOST=your-keystone-host
AUTH_PORT=15001
CB_HOST=your-context-broker-host
CB_PORT=1026
USERNAME=your_username
PASSWORD=your_password
SERVICE=your_service
SUBSERVICE=/your_subservice
```

## Running the Server

**STDIO mode** — for Claude Desktop, Cursor, or other MCP-compatible AI tools:
```bash
python server.py
```

**HTTP mode** — for external applications or custom integrations:
```bash
python server.py --http --port 5001
```


## 🔧 Available Tools & Resources

### Tools

| Tool | Description |
|------|-------------|
| `CB_version()` | Returns the Context Broker version (useful for connection testing) |
| `fiware_request(method, endpoint, body)` | Executes any NGSI-v2 API call with automatic authentication |
| `get_smart_data_model(domain, model)` | Fetches FIWARE Smart Data Model schemas from official repository |

The generic `fiware_request` tool gives you full access to the NGSI-v2 API without needing dedicated tools for each operation.

#### Smart Data Models Tool

The `get_smart_data_model` tool helps you create FIWARE-compliant entities by fetching official data model schemas:

```python
# Get AirQualityObserved model
get_smart_data_model("Environment", "AirQualityObserved")

# Get WeatherObserved model
get_smart_data_model("Weather", "WeatherObserved")

# Get Alert model
get_smart_data_model("Alert", "Alert")
```

**Common domains**: Environment, Weather, Alert, Building, Transportation, UrbanMobility, WasteManagement, Streetlighting, Energy, ParksAndGardens

**Learn more**: https://smartdatamodels.org/

### Resources

| Resource | URI | Description |
|----------|-----|-------------|
| `get_api_examples` | `fiware://examples` | NGSI-v2 API examples collection with real request/response patterns |

The resource contains a comprehensive collection of FIWARE API examples that AI assistants can read to understand request formats, authentication patterns, and response structures. This enables the AI to provide accurate guidance when working with FIWARE APIs.

### Prompts

| Prompt | Description |
|--------|-------------|
| `create_fiware_entity` | Step-by-step guide to create entities using Smart Data Models |
| `query_fiware_entities` | Guide to query entities with filters and examples |
| `use_smart_data_models` | Complete guide to Smart Data Models usage |

Prompts provide guided workflows that leverage the available tools and resources.

## 💡 Usage Examples

**List all entities:**
```python
fiware_request("GET", "/v2/entities")
```

**Query with filters:**
```python
fiware_request("GET", "/v2/entities?type=Room&limit=10")
```

**Create an entity:**
```python
fiware_request("POST", "/v2/entities", {
    "id": "Room:001",
    "type": "Room",
    "temperature": {"value": 23, "type": "Number"}
})
```

**Update attributes:**
```python
fiware_request("PATCH", "/v2/entities/Room:001/attrs", {
    "temperature": {"value": 25}
})
```

**Delete an entity:**
```python
fiware_request("DELETE", "/v2/entities/Room:001")
```

## ⚙️ Integration

### Claude Desktop

Add to your configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Option A: Using `.env` file (Recommended)**

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your credentials (see `.env.example`)

3. Add to config:
```json
{
  "mcpServers": {
    "fiware": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

**Option B: Using `uv` (no pre-install, credentials in config)**
```json
{
  "mcpServers": {
    "fiware": {
      "command": "uv",
      "args": [
        "run", "--with", "fastmcp>=2.0.0", "--with", "requests", "--with", "python-dotenv",
        "python", "/path/to/server.py"
      ],
      "env": {
        "AUTH_HOST": "your-keystone-host",
        "CB_HOST": "your-context-broker-host",
        "USERNAME": "your_username",
        "PASSWORD": "your_password",
        "SERVICE": "your_service",
        "SUBSERVICE": "/your_subservice"
      }
    }
  }
}
```

> **Note:** Option A is recommended as it keeps credentials separate from configuration.

### Cursor

Add to your Cursor MCP configuration (`~/.cursor/mcp.json`):

**Option A: Using `.env` file (Recommended)**

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your credentials (see `.env.example`)

3. Add to `mcp.json`:
```json
{
  "mcpServers": {
    "fiware": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

**Option B: Using `uv` (no pre-install, credentials in mcp.json)**
```json
{
  "mcpServers": {
    "fiware": {
      "command": "uv",
      "args": [
        "run", "--with", "fastmcp>=2.0.0", "--with", "requests", "--with", "python-dotenv",
        "python", "/path/to/server.py"
      ],
      "env": {
        "AUTH_HOST": "your-keystone-host",
        "CB_HOST": "your-context-broker-host",
        "USERNAME": "your_username",
        "PASSWORD": "your_password",
        "SERVICE": "your_service",
        "SUBSERVICE": "/your_subservice"
      }
    }
  }
}
```

**Option C: Credentials in `mcp.json` (without `.env` file)**
```json
{
  "mcpServers": {
    "fiware": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "AUTH_HOST": "your-keystone-host",
        "CB_HOST": "your-context-broker-host",
        "USERNAME": "your_username",
        "PASSWORD": "your_password",
        "SERVICE": "your_service",
        "SUBSERVICE": "/your_subservice"
      }
    }
  }
}
```

> **Note:** Option A is recommended as it keeps credentials separate from configuration.

### Visual Studio Code

Install the [MCP extension](https://marketplace.visualstudio.com/items?itemName=anthropics.claude-mcp) and add to your VS Code settings (`settings.json`):

```json
{
  "mcp.servers": {
    "fiware": {
      "command": "uv",
      "args": [
        "run", "--with", "fastmcp>=2.0.0", "--with", "requests", "--with", "python-dotenv",
        "python", "/path/to/server.py"
      ],
      "env": {
        "AUTH_HOST": "your-keystone-host",
        "CB_HOST": "your-context-broker-host",
        "USERNAME": "your_username",
        "PASSWORD": "your_password",
        "SERVICE": "your_service",
        "SUBSERVICE": "/your_subservice"
      }
    }
  }
}
```

You can also add this to `.vscode/settings.json` in your project root for workspace-specific configuration.

## Requirements

- Python 3.8+
- Access to a FIWARE Context Broker (Orion) with NGSI-v2 API
- OpenStack Keystone credentials (if authentication is enabled on your platform)

## Error Handling

The server includes comprehensive error handling for:

- **Authentication failures**: Automatic token refresh on 401 responses
- **Network connectivity issues**: Timeout handling and connection error recovery
- **Invalid API responses**: Graceful handling of malformed JSON and HTTP errors
- **Missing resources**: Clear error messages with helpful hints (e.g., 404 suggestions)
- **Smart Data Model lookup failures**: Domain/model validation with common suggestions
- **File operations**: Safe handling of missing Postman collection files

All tools return structured JSON responses with `success`, `error`, and `hint` fields to help diagnose issues.

## License

Apache-2.0 (same as original)

## Project Context

This MCP server was developed as a **Proof of Concept (PoC)** within the [TwIN Lab](https://twininnovacion.com/twin-lab/) program for territorial digital twin development. TwIN Lab is an innovation laboratory in Navarra (Spain) that provides training and access to digital twin technologies for SMEs, startups, and entrepreneurs.

The project demonstrates how AI assistants can interact with FIWARE-based IoT platforms while ensuring compliance with Smart Data Models standards, facilitating the creation of interoperable territorial digital twins.

## 🙏 Acknowledgments

This project builds upon the original work by [dncampo](https://github.com/dncampo/FIWARE-MCP-Server).

Special thanks to:
- **Alberto Abella** (<alberto.abella@fiware.org>) - FIWARE Foundation
- **Jorge Antonio Osuna Pons** (<josuna@mb3-gestion.com>) - [MB3 Gestión](https://mb3-gestion.com/)
- **Pedro Pablo Álvarez Jaramillo** (<ppalvarez@mb3-gestion.com>) - [MB3 Gestión](https://mb3-gestion.com/)
- **Oscar Rived** (<oscar@larraby.com>) - [Larraby](https://www.larraby.com/)

Their expertise and support in FIWARE platforms and Smart Data Models integration made this project possible.