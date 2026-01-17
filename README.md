# FIWARE Platform MCP Server (NGSI-v2)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FIWARE](https://img.shields.io/badge/FIWARE-NGSI--v2-orange.svg)](https://fiware.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

> **⚠️ Early Version**  
> This is a first release. Feedback and contributions welcome.

An MCP (Model Context Protocol) server for FIWARE NGSI-v2 platforms. Connects AI assistants (Claude Desktop, Cursor, etc.) to Context Broker, STH-Comet, Perseo CEP, and IoT Agents.

Works with cloud platforms, self-hosted servers, local Docker, or any NGSI-v2 compatible setup.

## Features

- **Context Broker (Orion)**: NGSI-v2 API for entity management
- **STH-Comet**: Historical data queries (raw values and aggregations)
- **Perseo CEP**: Complex Event Processing rules
- **IoT Agents**: Device registration (UltraLight/JSON protocols)
- **Smart Data Models**: Official FIWARE data model schemas
- **Authentication**: OAuth, Basic Auth, or no auth

## Why NGSI-v2?

FIWARE has two API specifications: **NGSI-v2** and **NGSI-LD** (linked-data based). This server targets NGSI-v2.

For NGSI-LD, see [dncampo/FIWARE-MCP-Server](https://github.com/dncampo/FIWARE-MCP-Server) which inspired this project.

---

## Quick Start

```bash
git clone https://github.com/miguel-escribano/fiware-platform-ngsi-v2-mcp.git
cd fiware-platform-ngsi-v2-mcp

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your FIWARE platform details
```

### Configuration

Edit `.env` with your platform details:

```env
# Authentication: oauth, basic, or none
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

# Optional components (default to CB_HOST if not set)
# STH_HOST=your-sth-host
# CEP_HOST=your-cep-host
# IOTA_HOST=your-iota-host
```

See `.env.example` for all options.

### Running

**STDIO mode** (for Claude Desktop, Cursor):
```bash
python server.py
```

**HTTP mode** (for external integrations):
```bash
python server.py --http --port 5001
```

---

## Available Tools

### Context Broker

| Tool | Description |
|------|-------------|
| `CB_version()` | Get Context Broker version |
| `fiware_request(method, endpoint, body)` | Execute NGSI-v2 API calls |

### STH-Comet

| Tool | Description |
|------|-------------|
| `sth_get_history(entity_type, entity_id, attribute, last_n, date_from, date_to)` | Get raw historical values |
| `sth_get_aggregation(entity_type, entity_id, attribute, aggr_method, aggr_period, date_from, date_to)` | Get aggregated data |

### Perseo CEP

| Tool | Description |
|------|-------------|
| `cep_list_rules()` | List configured rules |
| `cep_create_rule(name, epl_text, action_type, action_params)` | Create rule |
| `cep_delete_rule(rule_name)` | Delete rule |

### IoT Agents

| Tool | Description |
|------|-------------|
| `iota_list_devices()` | List registered devices |
| `iota_register_device(device_id, entity_name, entity_type, attributes, protocol, transport)` | Register device |
| `iota_delete_device(device_id, protocol)` | Delete device |
| `iota_list_services()` | List service configurations |

### Smart Data Models

| Tool | Description |
|------|-------------|
| `list_smart_data_model_domains()` | List available domains |
| `get_smart_data_model(domain, model)` | Get schema with NGSI-v2 examples |

More info: https://smartdatamodels.org/

### Resources

| Resource | URI | Description |
|----------|-----|-------------|
| `get_api_examples` | `fiware://examples` | NGSI-v2 API examples collection |

### Tool Design Note

**Context Broker** uses a single generic tool (`fiware_request`) because the NGSI-v2 API is extensive (~25 operations). The LLM can construct any valid endpoint.

**STH, CEP, and IoT Agents** use specific tools because their APIs are smaller and have complex parameters (EPL syntax, attribute mappings). These tools cover the most common operations (~90% of typical workflows). Some edge cases are not covered:

- `cep_get_rule(name)` — get single rule details
- `iota_provision_service()` — create service configurations  
- `iota_send_data()` — post data as a device

If you need these, extend `server.py` or open an issue.

---

## Usage Examples

### Context Broker

```python
# List entities
fiware_request("GET", "/v2/entities")

# Query with filters
fiware_request("GET", "/v2/entities?type=AirQualityObserved&limit=10")

# Create entity
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

### Historical Data

```python
# Get last 100 readings
sth_get_history("Room", "Room:001", "temperature", last_n=100)

# Get daily max
sth_get_aggregation("Room", "Room:001", "temperature", "max", "day",
                    date_from="2026-01-01T00:00:00Z", date_to="2026-01-31T23:59:59Z")
```

### Rules Engine

```python
cep_list_rules()

cep_create_rule(
    name="HighTempAlert",
    epl_text='select *,"HighTempAlert" as ruleName from pattern [every ev=iotEvent((cast(`type`?, String) = "Room") AND (cast(cast(`temperature`?, String), float) > 30))]',
    action_type="post",
    action_params={"url": "http://your-webhook.com/alerts"}
)
```

### IoT Devices

```python
iota_list_devices()

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

---

## Integration

### Claude Desktop

Config file location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fiware": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {}
    }
  }
}
```

**Note:** Configuration is read from the `.env` file in the server directory (see Configuration section above).

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "fiware": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {}
    }
  }
}
```

**Note:** This server reads configuration from the `.env` file in its directory. Make sure you've created and configured `.env` as shown in the Configuration section above.

**Alternative:** You can pass environment variables directly in the JSON instead of using `.env`:

```json
{
  "mcpServers": {
    "fiware": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "AUTH_TYPE": "oauth",
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

### Visual Studio Code

Install the [MCP extension](https://marketplace.visualstudio.com/items?itemName=anthropics.claude-mcp) and add to `settings.json`:

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

**Note:** The VS Code approach above shows environment variables in `settings.json`. Alternatively, you can use an empty `"env": {}` and rely on the `.env` file in the server directory (recommended to avoid storing credentials in VS Code settings).

Do not commit credentials to version control.

---

## Authentication Types

| Type | Use Case |
|------|----------|
| `oauth` | OpenStack Keystone authentication |
| `basic` | HTTP Basic Auth |
| `none` | No authentication (local development) |

Configure via `AUTH_TYPE` in `.env`.

## Requirements

- Python 3.8+
- FIWARE Context Broker (STH, Perseo, IoT Agents optional)

## Error Handling

Tools return JSON with `success`, `status_code`, and `error` fields. On 401 responses, OAuth tokens are automatically refreshed.

## License

Apache-2.0

## Project Context

Developed as part of the [TwIN Lab](https://twininnovacion.com/twin-lab/) program in Navarra, Spain.

## Acknowledgments

Inspired by [dncampo/FIWARE-MCP-Server](https://github.com/dncampo/FIWARE-MCP-Server) (NGSI-LD).

Thanks to:
- Oscar Rived and Julen Ardaiz - [Larraby](https://www.larraby.com/)
- Jorge Antonio Osuna Pons and Pedro Pablo Álvarez Jaramillo - [MB3 Gestión](https://mb3-gestion.com/)
- Alberto Abella - FIWARE Foundation
