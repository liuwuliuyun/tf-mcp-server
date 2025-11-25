"""
Telemetry module for Azure Terraform MCP Server using OpenTelemetry.

This module provides telemetry collection for tool usage, performance metrics,
and error tracking using Azure Monitor and OpenTelemetry.
"""

import logging
import functools
import time
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from datetime import datetime, UTC

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

# Type variables for decorator
P = ParamSpec('P')
R = TypeVar('R')


class TelemetryManager:
    """
    Manages OpenTelemetry telemetry collection and Azure Monitor integration.
    
    This class is a singleton that handles:
    - OpenTelemetry tracer and meter setup
    - Azure Monitor exporter configuration
    - Tool call tracking with spans and metrics
    - Error and exception tracking
    - User activity tracking for MAU
    """
    
    _instance: Optional['TelemetryManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'TelemetryManager':
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize telemetry manager (only once)."""
        if TelemetryManager._initialized:
            return
        
        self.enabled = False
        self.tracer: Optional[trace.Tracer] = None
        self.meter: Optional[metrics.Meter] = None
        self.user_id: Optional[str] = None
        self.sample_rate: float = 1.0
        
        # Metrics
        self.tool_call_counter: Optional[metrics.Counter] = None
        self.tool_duration_histogram: Optional[metrics.Histogram] = None
        self.tool_error_counter: Optional[metrics.Counter] = None
        
        TelemetryManager._initialized = True
    
    def configure(
        self,
        connection_string: str,
        user_id: str,
        enabled: bool = True,
        sample_rate: float = 1.0
    ) -> None:
        """
        Configure Azure Monitor telemetry with OpenTelemetry.
        
        Args:
            connection_string: Application Insights connection string
            user_id: Anonymous user identifier
            enabled: Whether telemetry is enabled
            sample_rate: Sampling rate for telemetry (0.0-1.0)
        """
        self.enabled = enabled
        self.user_id = user_id
        self.sample_rate = sample_rate
        
        if not enabled:
            logger.info("Telemetry is disabled")
            return
        
        if not connection_string:
            logger.warning("Application Insights connection string not provided. Telemetry disabled.")
            self.enabled = False
            return
        
        try:
            # Configure Azure Monitor with OpenTelemetry
            from azure.monitor.opentelemetry import configure_azure_monitor

            # Create resource attributes
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: "tf-mcp-server",
                ResourceAttributes.SERVICE_VERSION: "0.1.0",
                "user.id": user_id,
            })

            # Configure Azure Monitor
            configure_azure_monitor(
                connection_string=connection_string,
                resource=resource,
            )
 
            # Get tracer and meter
            self.tracer = trace.get_tracer("tf-mcp-server", "0.1.0")
            self.meter = metrics.get_meter("tf-mcp-server", "0.1.0")

            # Create metrics
            self._create_metrics()

            # Track user heartbeat
            self._track_heartbeat()

            logger.info(f"Azure Monitor telemetry configured successfully (user_id: {user_id[:8]}...)")

        except ImportError as e:
            logger.warning(f"Azure Monitor OpenTelemetry not available: {e}. Telemetry disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to configure telemetry: {e}")
            self.enabled = False
    
    def _create_metrics(self) -> None:
        """Create OpenTelemetry metrics for tool tracking."""
        if not self.meter:
            return
        
        try:
            # Counter for total tool calls
            self.tool_call_counter = self.meter.create_counter(
                name="tool_calls_total",
                description="Total number of tool invocations",
                unit="1"
            )

            # Histogram for tool execution duration
            self.tool_duration_histogram = self.meter.create_histogram(
                name="tool_duration_ms",
                description="Tool execution duration in milliseconds",
                unit="ms"
            )

            # Counter for tool errors
            self.tool_error_counter = self.meter.create_counter(
                name="tool_errors_total",
                description="Total number of tool errors",
                unit="1"
            )

        except Exception as e:
            logger.error(f"Failed to create metrics: {e}")
    
    def _track_heartbeat(self) -> None:
        """Track user heartbeat for MAU calculation."""
        if not self.tracer or not self.enabled:
            return
        
        try:
            with self.tracer.start_as_current_span("user.heartbeat") as span:
                span.set_attribute("user.id", self.user_id or "unknown")
                span.set_attribute("event.type", "heartbeat")
                span.set_attribute("timestamp", datetime.now(UTC).isoformat())
                span.add_event("UserHeartbeat", {
                    "user.id": self.user_id or "unknown",
                    "date": datetime.now(UTC).date().isoformat()
                })
        except Exception as e:
            logger.debug(f"Failed to track heartbeat: {e}")
    
    def track_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float,
        error_type: Optional[str] = None,
        **attributes: Any
    ) -> None:
        """
        Track a tool call with metrics and traces.
        
        Args:
            tool_name: Name of the tool being called
            success: Whether the call was successful
            duration_ms: Execution duration in milliseconds
            error_type: Type of error if failed
            **attributes: Additional custom attributes
        """
        if not self.enabled:
            return
        
        try:
            # Prepare attributes
            attrs = {
                "tool.name": tool_name,
                "tool.success": str(success),
                "user.id": self.user_id or "unknown",
            }

            if error_type:
                attrs["error.type"] = error_type

            attrs.update(attributes)

            # Record metrics
            if self.tool_call_counter:
                self.tool_call_counter.add(1, attrs)

            if self.tool_duration_histogram:
                self.tool_duration_histogram.record(duration_ms, attrs)

            if not success and self.tool_error_counter:
                self.tool_error_counter.add(1, attrs)

        except Exception as e:
            logger.debug(f"Failed to track tool call: {e}")
    
    def track_exception(
        self,
        exception: Exception,
        tool_name: str,
        **attributes: Any
    ) -> None:
        """
        Track an exception with OpenTelemetry.
        
        Args:
            exception: The exception that occurred
            tool_name: Name of the tool where exception occurred
            **attributes: Additional custom attributes
        """
        if not self.enabled or not self.tracer:
            return
        
        try:
            # Get current span and record exception
            span = trace.get_current_span()
            if span:
                span.record_exception(exception)
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("user.id", self.user_id or "unknown")

                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

        except Exception as e:
            logger.debug(f"Failed to track exception: {e}")
    
    def shutdown(self) -> None:
        """Shutdown telemetry and flush any pending data."""
        if not self.enabled:
            return
        
        try:
            # Get trace and meter providers and shutdown
            from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
            from opentelemetry.sdk.metrics import MeterProvider as SDKMeterProvider

            trace_provider = trace.get_tracer_provider()
            if isinstance(trace_provider, SDKTracerProvider):
                trace_provider.shutdown()

            meter_provider = metrics.get_meter_provider()
            if isinstance(meter_provider, SDKMeterProvider):
                meter_provider.shutdown()

            logger.info("Telemetry shutdown complete")

        except Exception as e:
            logger.error(f"Error during telemetry shutdown: {e}")


# Global telemetry manager instance
_telemetry_manager = TelemetryManager()


def get_telemetry_manager() -> TelemetryManager:
    """Get the global telemetry manager instance."""
    return _telemetry_manager


def track_tool_call(tool_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to track tool calls with OpenTelemetry.
    
    This decorator:
    - Creates a span for each tool invocation
    - Records metrics (call count, duration, errors)
    - Tracks exceptions with full context
    - Preserves function signatures and async compatibility
    
    Args:
        tool_name: Name of the tool being tracked
    
    Returns:
        Decorated function with telemetry tracking
    
    Example:
        @track_tool_call("get_avm_modules")
        def get_avm_modules() -> str:
            return "module data"
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            manager = get_telemetry_manager()

            if not manager.enabled or not manager.tracer:
                # Telemetry disabled, call function directly
                return await func(*args, **kwargs)

            start_time = time.time()
            success = False
            error_type: Optional[str] = None
            result: Optional[R] = None

            # Create span for this tool call
            with manager.tracer.start_as_current_span(f"tool.{tool_name}") as span:
                try:
                    # Set span attributes
                    span.set_attribute("tool.name", tool_name)
                    span.set_attribute("user.id", manager.user_id or "unknown")
                    span.set_attribute("tool.parameters.count", len(kwargs))

                    # Execute the function
                    result = await func(*args, **kwargs)
                    success = True
                    span.set_status(trace.Status(trace.StatusCode.OK))

                except Exception as e:
                    error_type = type(e).__name__
                    span.set_attribute("error.type", error_type)
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(e))
                    )
                    manager.track_exception(e, tool_name)
                    raise

                finally:
                    # Calculate duration and track metrics
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("tool.duration_ms", duration_ms)
                    span.set_attribute("tool.success", success)

                    manager.track_tool_call(
                        tool_name=tool_name,
                        success=success,
                        duration_ms=duration_ms,
                        error_type=error_type
                    )

            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            manager = get_telemetry_manager()

            if not manager.enabled or not manager.tracer:
                # Telemetry disabled, call function directly
                return func(*args, **kwargs)

            start_time = time.time()
            success = False
            error_type: Optional[str] = None
            result: Optional[R] = None

            # Create span for this tool call
            with manager.tracer.start_as_current_span(f"tool.{tool_name}") as span:
                try:
                    # Set span attributes
                    span.set_attribute("tool.name", tool_name)
                    span.set_attribute("user.id", manager.user_id or "unknown")
                    span.set_attribute("tool.parameters.count", len(kwargs))

                    # Execute the function
                    result = func(*args, **kwargs)
                    success = True
                    span.set_status(trace.Status(trace.StatusCode.OK))

                except Exception as e:
                    error_type = type(e).__name__
                    span.set_attribute("error.type", error_type)
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(e))
                    )
                    manager.track_exception(e, tool_name)
                    raise

                finally:
                    # Calculate duration and track metrics
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("tool.duration_ms", duration_ms)
                    span.set_attribute("tool.success", success)

                    manager.track_tool_call(
                        tool_name=tool_name,
                        success=success,
                        duration_ms=duration_ms,
                        error_type=error_type
                    )

            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator
