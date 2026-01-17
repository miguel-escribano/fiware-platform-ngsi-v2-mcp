# FIWARE Platform MCP Server - Usage Guide

This project provides an MCP server for FIWARE NGSI-v2 platforms. When this MCP is enabled, you have access to tools for Context Broker, STH-Comet, Perseo CEP, and IoT Agents.

## Available Tools

### Context Broker (Orion)
- `CB_version()` — Test connection, get broker version
- `fiware_request(method, endpoint, body)` — Execute any NGSI-v2 API call

### STH-Comet (Historical Data)
- `sth_get_history(entity_type, entity_id, attribute, last_n, date_from, date_to)` — Raw historical values
- `sth_get_aggregation(entity_type, entity_id, attribute, aggr_method, aggr_period, date_from, date_to)` — Aggregated data (min/max/sum)

### Perseo CEP (Rules Engine)
- `cep_list_rules()` — List configured rules
- `cep_create_rule(name, epl_text, action_type, action_params)` — Create rule
- `cep_delete_rule(rule_name)` — Delete rule

### IoT Agents
- `iota_list_devices()` — List registered devices
- `iota_register_device(device_id, entity_name, entity_type, attributes, protocol, transport)` — Register device
- `iota_delete_device(device_id, protocol)` — Delete device
- `iota_list_services()` — List service configurations

### Smart Data Models
- `list_smart_data_model_domains()` — Discover available domains
- `get_smart_data_model(domain, model)` — Get schema with NGSI-v2 examples

## Recommended Workflows

### Exploring the Platform
1. Start with `CB_version()` to verify connection
2. Use `fiware_request("GET", "/v2/types")` to see what entity types exist
3. Query entities: `fiware_request("GET", "/v2/entities?type=TypeName&limit=5")`

### Creating Entities (Best Practice)
1. First check Smart Data Models: `list_smart_data_model_domains()`
2. Get the schema: `get_smart_data_model("Domain", "ModelName")`
3. Create entity following the schema structure
4. Use the NGSI-v2 format: `{"id": "...", "type": "...", "attr": {"value": X, "type": "Type"}}`

### Working with Historical Data
- Raw values: `sth_get_history("EntityType", "entity:id", "attribute", last_n=100)`
- Aggregations: `sth_get_aggregation("EntityType", "entity:id", "attribute", "max", "day")`
- Supported aggr_method: "max", "min", "sum", "sum2"
- Supported aggr_period: "hour", "day", "month"

### Setting Up Alerts (Perseo CEP)
1. List existing rules: `cep_list_rules()`
2. Create rule with EPL pattern and action (email, post, update)
3. EPL example for threshold: `select *,"RuleName" as ruleName from pattern [every ev=iotEvent((cast(\`type\`?, String) = "EntityType") AND (cast(cast(\`attribute\`?, String), float) > threshold))]`

## Common Patterns

### Query with filters
```
fiware_request("GET", "/v2/entities?type=Room&q=temperature>25&limit=10")
```

### Update entity attribute
```
fiware_request("PATCH", "/v2/entities/Room:001/attrs", {
    "temperature": {"value": 23, "type": "Number"}
})
```

### Geo-queries (near a point)
```
fiware_request("GET", "/v2/entities?georel=near;maxDistance:1000&geometry=point&coords=42.8,-1.6")
```

## Error Handling

- **401 errors**: Token expired, will auto-refresh on retry
- **404 on entity**: Check entity ID and type spelling
- **Empty STH results**: Entity may not have historical data configured
- **CEP rule errors**: Verify EPL syntax, especially backtick escaping for reserved words

## Tips

- Entity IDs typically follow pattern: `Type:identifier` (e.g., `Room:001`, `AirQualityObserved:Station1`)
- Always use Smart Data Models when creating new entity types for interoperability
- The `fiware_request` tool can do anything — use specific tools (sth_*, cep_*, iota_*) for cleaner workflows
- When unsure about entity structure, query an existing one first
