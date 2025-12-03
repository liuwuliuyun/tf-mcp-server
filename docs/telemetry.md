# Telemetry Documentation

## Overview

The Azure Terraform MCP Server collects anonymous telemetry data to help us understand how the tool is used and to improve its quality and performance. This document explains what data is collected, why it's collected, and how you can opt out.

## What Data is Collected

We collect the following types of telemetry data:

### 1. Tool Usage Metrics
- **Tool invocation counts**: Number of times each tool is called
- **Tool execution duration**: How long each tool takes to execute
- **Tool success/failure rates**: Whether tool calls succeed or fail
- **Error types**: The type of exception when a tool fails (e.g., `ValueError`, `TimeoutError`)

### 2. User Activity
- **Anonymous user ID**: A randomly generated UUID that doesn't identify you personally
- **Session activity**: Periodic heartbeat events to calculate Monthly Active Users (MAU)
- **Timestamp**: When events occur (UTC)

### 3. Performance Data
- **Execution time histograms**: Distribution of tool execution times
- **Aggregated metrics**: P50, P95, P99 latency percentiles

## What Data is NOT Collected

We are committed to protecting your privacy. We **DO NOT** collect:

- ❌ Personal Identifiable Information (PII)
- ❌ File paths or file names
- ❌ Resource names or identifiers
- ❌ Azure subscription IDs or tenant IDs
- ❌ IP addresses or machine names
- ❌ Terraform configuration content
- ❌ Any sensitive or proprietary information
- ❌ Tool parameter values (except count)

## Why We Collect Telemetry

Telemetry helps us:

1. **Improve Quality**: Identify which tools fail most often and prioritize bug fixes
2. **Optimize Performance**: Find slow operations and optimize them
3. **Guide Development**: Understand which features are most used to prioritize enhancements
4. **Measure Adoption**: Track Monthly Active Users to understand tool adoption
5. **Ensure Reliability**: Monitor error rates and set up alerts for critical issues

## Technology Used

We use **Azure Monitor OpenTelemetry Exporters** to collect and transmit telemetry data:

- **OpenTelemetry Standard**: Industry-standard observability framework (CNCF project)
- **Azure Application Insights**: Microsoft's application performance management service
- **Explicit Tracking Only**: We only collect data from our `@track_tool_call` decorator - no automatic instrumentation
- **No Application Logs**: Your logger.info/debug statements are NOT collected
- **No HTTP Tracing**: HTTP requests from libraries like httpx are NOT collected
- **Secure Transmission**: All data is encrypted in transit using HTTPS
- **Data Retention**: Data is retained according to Azure Application Insights default policies (90 days)
- **Batched Exports**: Telemetry is exported every 60 seconds to minimize network overhead

## How to Opt Out

You have full control over telemetry collection. You can opt out in two ways:

### Option 1: Environment Variable (Recommended)

Set the `TELEMETRY_ENABLED` environment variable to `false`:

```bash
# Windows (PowerShell)
$env:TELEMETRY_ENABLED = "false"

# Windows (Command Prompt)
set TELEMETRY_ENABLED=false

# Linux/macOS
export TELEMETRY_ENABLED=false
```

### Option 2: Configuration File

Edit the telemetry configuration file:

**Location**: `~/.tf_mcp_server/.telemetry_config.json`

```json
{
  "user_id": "your-anonymous-id",
  "telemetry_enabled": false,
  "first_seen": "2025-11-19T00:00:00Z"
}
```

Set `telemetry_enabled` to `false` and restart the server.

### Verify Opt-Out

When telemetry is disabled, you'll see this message in the logs:

```
INFO: Telemetry is disabled
```

## Performance Impact

Telemetry is designed to have minimal performance impact:

- **Asynchronous collection**: Telemetry data is sent asynchronously, not blocking tool execution
- **Negligible overhead**: Less than 1ms added per tool call when enabled
- **Zero overhead when disabled**: No performance impact when telemetry is opted out
- **Sampling support**: Optional sampling to reduce telemetry volume (default: 100%)

## Data Security

Your telemetry data is protected:

- **Encryption in Transit**: All data transmitted via HTTPS/TLS
- **Encryption at Rest**: Data stored in Azure is encrypted
- **Anonymous**: No data can be traced back to you personally
- **Aggregated**: Data is analyzed in aggregate, not individually
- **Microsoft Privacy Policy**: Subject to [Microsoft Privacy Statement](https://privacy.microsoft.com/privacystatement)

## OpenTelemetry Traces & Metrics

### Traces (Spans)

Each tool invocation creates a trace span with these attributes:

```
Span Name: tool.{tool_name}
Attributes:
  - tool.name: Name of the tool
  - tool.success: true/false
  - tool.duration_ms: Execution time in milliseconds
  - user.id: Anonymous UUID
  - error.type: Exception class name (if failed)
  - tool.parameters.count: Number of parameters passed
```

### Metrics

The following metrics are collected:

1. **tool_calls_total** (Counter)
   - Total number of tool invocations
   - Dimensions: tool_name, success, error_type

2. **tool_duration_ms** (Histogram)
   - Tool execution duration distribution
   - Dimensions: tool_name
   - Buckets: [10, 50, 100, 500, 1000, 5000, 10000] ms

3. **tool_errors_total** (Counter)
   - Total number of tool errors
   - Dimensions: tool_name, error_type

## Querying Telemetry Data (For Maintainers)

If you're a project maintainer with access to Application Insights, here are some useful queries:

### Tool Call Counts

```kql
customMetrics
| where customDimensions.["tool.name"] != ""
| summarize CallCount = count() by ToolName = tostring(customDimensions.["tool.name"])
| order by CallCount desc
```

### Error Rates by Tool

```kql
customMetrics
| where customDimensions.["tool.name"] != ""
| summarize
    Total = count(),
    Errors = countif(customDimensions.["tool.success"] == "false")
    by ToolName = tostring(customDimensions.["tool.name"])
| extend ErrorRate = (Errors * 100.0) / Total
| order by ErrorRate desc
```

### Monthly Active Users

```kql
traces
| where timestamp > ago(30d)
| where customDimensions.["user.id"] != ""
| summarize MAU = dcount(tostring(customDimensions.["user.id"]))
```

### Performance Metrics (P95)

```kql
customMetrics
| where name == "tool_duration_ms"
| summarize
    avg_ms = avg(value),
    p95_ms = percentile(value, 95),
    p99_ms = percentile(value, 99)
    by ToolName = tostring(customDimensions.["tool.name"])
| order by p95_ms desc
```

## Sampling Configuration

You can reduce telemetry volume by adjusting the sampling rate:

```bash
# Set sampling to 50% (0.5) of all events
export TELEMETRY_SAMPLE_RATE=0.5
```

Valid values: `0.0` (disabled) to `1.0` (100%, default)

## Frequently Asked Questions

### Q: Is telemetry enabled by default?
**A:** Yes, telemetry is enabled by default to help improve the tool. You can opt out anytime.

### Q: Can telemetry data identify me?
**A:** No. We only collect an anonymous UUID. There's no way to link the UUID to your identity.

### Q: What if I don't have an Azure Application Insights connection string?
**A:** If no connection string is configured, telemetry is automatically disabled with no errors.

### Q: Does telemetry work offline?
**A:** No. If there's no internet connection, telemetry events are dropped silently.

### Q: Can I see what data is being sent?
**A:** Yes. Set log level to DEBUG to see telemetry events in the logs.

### Q: Will this slow down my tools?
**A:** No. Telemetry adds less than 1ms overhead per tool call and runs asynchronously.

### Q: What happens to my data if I opt out?
**A:** Your previous telemetry data remains in Application Insights but no new data is sent.

### Q: Can I delete my telemetry data?
**A:** Since all data is anonymous (UUID only), there's no way to identify which data belongs to you. Data auto-expires after 90 days.

### Q: Is the source code for telemetry available?
**A:** Yes. All telemetry code is open source in `src/tf_mcp_server/core/telemetry.py`.

## Contact & Feedback

If you have questions or concerns about telemetry:

- **GitHub Issues**: [github.com/liuwuliuyun/tf-mcp-server/issues](https://github.com/liuwuliuyun/tf-mcp-server/issues)
- **Email**: aztfai@microsoft.com

## Privacy Commitment

We are committed to:

- **Transparency**: This document fully explains what we collect
- **Control**: You can opt out at any time
- **Privacy**: No PII or sensitive data is collected
- **Security**: Data is encrypted and stored securely
- **Compliance**: We follow Microsoft's privacy policies and standards

---

**Last Updated**: November 19, 2025
