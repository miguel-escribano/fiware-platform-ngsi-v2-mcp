# FIWARE Platform MCP Server (NGSI-v2)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FIWARE](https://img.shields.io/badge/FIWARE-NGSI--v2-orange.svg)](https://fiware.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

> **⚠️ Early Version**  
> This is a first release. While functional, there may be inconsistencies or areas for improvement. Feedback, suggestions, and contributions are welcome—feel free to open issues or reach out.

An MCP (Model Context Protocol) server for the complete FIWARE platform stack. Enables AI assistants like Claude Desktop and Cursor to interact with Context Broker (Orion), STH-Comet, Perseo CEP, and IoT Agents — all through the NGSI-v2 API.

**Works with any FIWARE deployment**: cloud platforms, self-hosted servers, local Docker, or any NGSI-v2 compatible setup.


## ✨ Features

- **Context Broker (Orion)**: Full NGSI-v2 API support for entity management
- **STH-Comet**: Historical data queries (raw values and aggregations)
- **Perseo CEP**: Complex Event Processing rules management
- **IoT Agents**: Device registration and management (UltraLight/JSON protocols)
- **Smart Data Models**: Discover and use official FIWARE data model schemas
- **Multi-Auth Support**: OAuth (Telefonica), Basic Auth (Linode), or no auth (local Docker)
- **12 MCP Tools**: Complete FIWARE platform operations
- **1 MCP Resource**: API examples collection


## 📦 Installation

This MCP server runs **locally on your machine** and connects to your FIWARE platform (which can be local, remote, or cloud-hosted). It is not a hosted service—you install and run it yourself.

See the [Integration](#-integration) section below for step-by-step instructions.


## Why NGSI-v2?

FIWARE has two API specifications: **NGSI-v2** (classic, widely deployed) and **NGSI-LD** (newer, linked-data based). This server targets NGSI-v2 because it's what most production FIWARE deployments use today, including Telefonica's IoT Platform and many self-hosted installations.

If you need NGSI-LD support, check out [dncampo/FIWARE-MCP-Server](https://github.com/dncampo/FIWARE-MCP-Server) which inspired this project.

---

## 🚀 Quick Start

> **Note:** The MCP server runs locally on your machine. Your FIWARE Context Broker can be anywhere (localhost, remote server, or cloud).

```bash
# Clone the repository
git clone https://github.com/miguel-escribano/fiware-platform-ngsi-v2-mcp.git
cd fiware-platform-ngsi-v2-mcp

# Install dependencies
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
```

Edit `.env` with your FIWARE platform details (see `.env.example` for all options):

```env
# Authentication: oauth (Telefonica), basic (Linode), none (local Docker)
AUTH_TYPE=oauth
AUTH_HOST=your-auth-host
AUTH_PORT=15001

# Context Broker
CB_HOST=your-context-broker-host
CB_PORT=1026
CB_PROTOCOL=https

# Credentials
FIWARE_USERNAME=your_username
FIWARE_PASSWORD=your_password

# Multi-tenancy
SERVICE=your_service
SUBSERVICE=/your_subservice

# Optional: STH, Perseo, IoT Agent (defaults to CB_HOST if not set)
# STH_HOST=your-sth-host
# CEP_HOST=your-cep-host
# IOTA_HOST=your-iota-host
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

### Exposing via ngrok (HTTP mode)

To use your MCP server with external APIs (e.g., OpenAI Responses API) or share it temporarily, you can expose it via ngrok:

1. **Sign up** at [ngrok.com](https://ngrok.com) and install the client
2. **Add your auth token**:
   ```bash
   ngrok config add-authtoken <YOUR_AUTH_TOKEN>
   ```
3. **Start your MCP server** in HTTP mode (if not already running):
   ```bash
   python server.py --http --host 127.0.0.1 --port 5001
   ```
4. **Start ngrok tunnel**:
   ```bash
   ngrok http http://127.0.0.1:5001
   ```
5. **Access your MCP endpoint** at: `{PUBLIC_URL}/mcp`

> **Security Note**: Keep your auth token secure. The public URL is active only while ngrok is running.


## 🔧 Available Tools

### Context Broker (Orion)

| Tool | Description |
|------|-------------|
| `CB_version()` | Returns the Context Broker version (connection test) |
| `fiware_request(method, endpoint, body)` | Execute any NGSI-v2 API call |

### STH-Comet (Historical Data)

| Tool | Description |
|------|-------------|
| `sth_get_history(entity_type, entity_id, attribute, last_n, date_from, date_to)` | Get raw historical values |
| `sth_get_aggregation(entity_type, entity_id, attribute, aggr_method, aggr_period, date_from, date_to)` | Get aggregated data (min/max/sum by hour/day/month) |

### Perseo CEP (Rules Engine)

| Tool | Description |
|------|-------------|
| `cep_list_rules()` | List all configured rules |
| `cep_create_rule(name, epl_text, action_type, action_params)` | Create a new rule |
| `cep_delete_rule(rule_name)` | Delete a rule |

### IoT Agents

| Tool | Description |
|------|-------------|
| `iota_list_devices()` | List all registered devices |
| `iota_register_device(device_id, entity_name, entity_type, attributes, protocol, transport)` | Register a new device |
| `iota_delete_device(device_id, protocol)` | Delete a device |
| `iota_list_services()` | List IoT Agent service configurations |

### Smart Data Models

| Tool | Description |
|------|-------------|
| `list_smart_data_model_domains()` | List available domains and models |
| `get_smart_data_model(domain, model)` | Get schema with NGSI-v2 conversion examples |

**Learn more**: https://smartdatamodels.org/

### Resources

| Resource | URI | Description |
|----------|-----|-------------|
| `get_api_examples` | `fiware://examples` | NGSI-v2 API examples collection with real request/response patterns |

The resource contains a comprehensive collection of FIWARE API examples that AI assistants can read to understand request formats, authentication patterns, and response structures. This enables the AI to provide accurate guidance when working with FIWARE APIs.

## 💡 Usage Examples

### Context Broker

```python
# List all entities
fiware_request("GET", "/v2/entities")

# Query with filters
fiware_request("GET", "/v2/entities?type=AirQualityObserved&limit=10")

# Create an entity
fiware_request("POST", "/v2/entities", {
    "id": "Room:001",
    "type": "Room",
    "temperature": {"value": 23, "type": "Number"}
})

# Update attributes
fiware_request("PATCH", "/v2/entities/Room:001/attrs", {
    "temperature": {"value": 25}
})
```

### Historical Data (STH)

```python
# Get last 100 temperature readings
sth_get_history("Room", "Room:001", "temperature", last_n=100)

# Get daily max temperature for January
sth_get_aggregation("Room", "Room:001", "temperature", "max", "day",
                    date_from="2026-01-01T00:00:00Z", date_to="2026-01-31T23:59:59Z")
```

### Rules Engine (Perseo CEP)

```python
# List current rules
cep_list_rules()

# Create alert rule for high temperature
cep_create_rule(
    name="HighTempAlert",
    epl_text='select *,"HighTempAlert" as ruleName from pattern [every ev=iotEvent((cast(`type`?, String) = "Room") AND (cast(cast(`temperature`?, String), float) > 30))]',
    action_type="post",
    action_params={"url": "http://your-webhook.com/alerts"}
)
```

### IoT Devices

```python
# List all devices
iota_list_devices()

# Register a new sensor
iota_register_device(
    device_id="sensor001",
    entity_name="Room:001",
    entity_type="Room",
    attributes=[
        {"object_id": "t", "name": "temperature", "type": "Number"},
        {"object_id": "h", "name": "humidity", "type": "Number"}
    ]
)
```

## ⚙️ Integration

### Claude Desktop

Add to your configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file** with your credentials (see `.env.example`)

3. **Add to config**:
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

> **Note:** Credentials are read from `.env` file automatically. Do not put credentials in the config file.

### Cursor

Add to your Cursor MCP configuration (`~/.cursor/mcp.json`):

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file** with your credentials (see `.env.example`)

3. **Add to `mcp.json`**:
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

> **Note:** Credentials are read from `.env` file automatically. Do not put credentials in `mcp.json`.

### Visual Studio Code

Install the [MCP extension](https://marketplace.visualstudio.com/items?itemName=anthropics.claude-mcp) and add to your VS Code settings (`settings.json`):

```json
{
  "mcp.servers": {
    "fiware": {
      "command": "uv",
      "args": [
        "run", "--with", "fastmcp>=2.0.0,<3", "--with", "requests", "--with", "python-dotenv",
        "python", "/path/to/server.py"
      ],
      "env": {
        "AUTH_TYPE": "oauth",
        "AUTH_HOST": "your-auth-host",
        "CB_HOST": "your-context-broker-host",
        "FIWARE_USERNAME": "your_username",
        "FIWARE_PASSWORD": "your_password",
        "SERVICE": "your_service",
        "SUBSERVICE": "/your_subservice"
      }
    }
  }
}
```

You can also add this to `.vscode/settings.json` in your project root for workspace-specific configuration.

## Supported Architectures

This server works with any FIWARE NGSI-v2 deployment:

| Platform | Auth Type | Notes |
|----------|-----------|-------|
| **Telefonica IoT Platform** | `oauth` | OpenStack Keystone authentication |
| **Linode / Self-hosted** | `basic` | HTTP Basic Auth |
| **Local Docker** | `none` | No authentication required |

Configure via `.env` file — see `.env.example` for all options.

## Requirements

- Python 3.8+
- Access to a FIWARE platform (Context Broker required; STH, Perseo, IoT Agents optional)

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

This project was inspired by [dncampo/FIWARE-MCP-Server](https://github.com/dncampo/FIWARE-MCP-Server) (NGSI-LD implementation).

Special thanks to:
- **Oscar Rived** (<oscar@larraby.com>) and **Julen Ardaiz** (<julen@larraby.com>) - [Larraby](https://www.larraby.com/)
- **Jorge Antonio Osuna Pons** (<josuna@mb3-gestion.com>) and **Pedro Pablo Álvarez Jaramillo** (<ppalvarez@mb3-gestion.com>) - [MB3 Gestión](https://mb3-gestion.com/)
- **Alberto Abella** (<alberto.abella@fiware.org>) - FIWARE Foundation

Their expertise and support in FIWARE platforms and Smart Data Models integration made this project possible.