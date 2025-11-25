"""
Unit tests for the telemetry module.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from tf_mcp_server.core.telemetry import (
    TelemetryManager,
    get_telemetry_manager,
    track_tool_call
)


class TestTelemetryManager:
    """Tests for TelemetryManager class."""
    
    def test_singleton_pattern(self):
        """Test that TelemetryManager follows singleton pattern."""
        manager1 = TelemetryManager()
        manager2 = TelemetryManager()
        assert manager1 is manager2
    
    def test_get_telemetry_manager(self):
        """Test get_telemetry_manager returns the singleton instance."""
        manager = get_telemetry_manager()
        assert isinstance(manager, TelemetryManager)
        assert manager is TelemetryManager()
    
    def test_configure_disabled(self):
        """Test that telemetry can be disabled."""
        manager = TelemetryManager()
        manager.configure(
            connection_string="test",
            user_id="test-user",
            enabled=False
        )
        assert manager.enabled is False
        assert manager.tracer is None
    
    def test_configure_no_connection_string(self):
        """Test that telemetry is disabled without connection string."""
        manager = TelemetryManager()
        manager.configure(
            connection_string="",
            user_id="test-user",
            enabled=True
        )
        assert manager.enabled is False
    
    @patch('azure.monitor.opentelemetry.configure_azure_monitor')
    @patch('tf_mcp_server.core.telemetry.trace.get_tracer')
    @patch('tf_mcp_server.core.telemetry.metrics.get_meter')
    def test_configure_success(self, mock_get_meter, mock_get_tracer, mock_configure_azure):
        """Test successful telemetry configuration."""
        # Setup mocks
        mock_tracer = MagicMock()
        mock_meter = MagicMock()
        mock_get_tracer.return_value = mock_tracer
        mock_get_meter.return_value = mock_meter
        
        # Create counter and histogram mocks
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter.create_histogram.return_value = mock_histogram
        
        # Reset singleton state for clean test
        manager = TelemetryManager()
        manager.enabled = False
        manager.tracer = None
        manager.meter = None
        
        manager.configure(
            connection_string="InstrumentationKey=test;IngestionEndpoint=https://test.com",
            user_id="test-user-123",
            enabled=True,
            sample_rate=0.5
        )
        
        assert manager.enabled is True
        assert manager.user_id == "test-user-123"
        assert manager.sample_rate == 0.5
        assert manager.tracer is not None
        assert manager.meter is not None
        
        # Verify Azure Monitor was configured
        mock_configure_azure.assert_called_once()
        
        # Verify metrics were created
        assert mock_meter.create_counter.call_count >= 2
        assert mock_meter.create_histogram.call_count >= 1
    
    def test_track_tool_call_disabled(self):
        """Test that tracking does nothing when disabled."""
        manager = TelemetryManager()
        manager.enabled = False
        
        # Should not raise any errors
        manager.track_tool_call(
            tool_name="test_tool",
            success=True,
            duration_ms=100.0
        )
    
    @patch('tf_mcp_server.core.telemetry.trace.get_tracer')
    @patch('tf_mcp_server.core.telemetry.metrics.get_meter')
    def test_track_tool_call_success(self, mock_get_meter, mock_get_tracer):
        """Test tracking a successful tool call."""
        # Setup mocks
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter.create_histogram.return_value = mock_histogram
        mock_get_meter.return_value = mock_meter
        
        manager = TelemetryManager()
        manager.enabled = True
        manager.user_id = "test-user"
        manager.tool_call_counter = mock_counter
        manager.tool_duration_histogram = mock_histogram
        
        manager.track_tool_call(
            tool_name="test_tool",
            success=True,
            duration_ms=150.5
        )
        
        # Verify counter was incremented
        mock_counter.add.assert_called_once()
        call_args = mock_counter.add.call_args
        assert call_args[0][0] == 1
        attrs = call_args[0][1]
        assert attrs["tool.name"] == "test_tool"
        assert attrs["tool.success"] == "True"
        
        # Verify histogram was recorded
        mock_histogram.record.assert_called_once()
        record_args = mock_histogram.record.call_args
        assert record_args[0][0] == 150.5
    
    @patch('tf_mcp_server.core.telemetry.trace.get_tracer')
    @patch('tf_mcp_server.core.telemetry.metrics.get_meter')
    def test_track_tool_call_with_error(self, mock_get_meter, mock_get_tracer):
        """Test tracking a failed tool call with error type."""
        # Setup mocks
        mock_counter = MagicMock()
        mock_error_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        
        def create_counter_side_effect(name, **kwargs):
            if "error" in name:
                return mock_error_counter
            return mock_counter
        
        mock_meter.create_counter.side_effect = create_counter_side_effect
        mock_meter.create_histogram.return_value = mock_histogram
        mock_get_meter.return_value = mock_meter
        
        manager = TelemetryManager()
        manager.enabled = True
        manager.user_id = "test-user"
        manager.tool_call_counter = mock_counter
        manager.tool_duration_histogram = mock_histogram
        manager.tool_error_counter = mock_error_counter
        
        manager.track_tool_call(
            tool_name="test_tool",
            success=False,
            duration_ms=50.0,
            error_type="ValueError"
        )
        
        # Verify error counter was incremented
        mock_error_counter.add.assert_called_once()
        error_args = mock_error_counter.add.call_args
        assert error_args[0][0] == 1
        attrs = error_args[0][1]
        assert attrs["error.type"] == "ValueError"
    
    def test_track_exception_disabled(self):
        """Test that exception tracking does nothing when disabled."""
        manager = TelemetryManager()
        manager.enabled = False
        
        # Should not raise any errors
        try:
            raise ValueError("Test error")
        except ValueError as e:
            manager.track_exception(e, "test_tool")


class TestTrackToolCallDecorator:
    """Tests for the track_tool_call decorator."""
    
    def test_sync_function_success(self):
        """Test decorator with synchronous function that succeeds."""
        manager = TelemetryManager()
        manager.enabled = False  # Disable to avoid actual telemetry
        
        @track_tool_call("test_sync_tool")
        def sync_function(x: int, y: int) -> int:
            return x + y
        
        result = sync_function(2, 3)
        assert result == 5
    
    def test_sync_function_with_exception(self):
        """Test decorator with synchronous function that raises exception."""
        manager = TelemetryManager()
        manager.enabled = False
        
        @track_tool_call("test_sync_tool_error")
        def sync_function_error() -> None:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            sync_function_error()
    
    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test decorator with asynchronous function that succeeds."""
        manager = TelemetryManager()
        manager.enabled = False
        
        @track_tool_call("test_async_tool")
        async def async_function(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        result = await async_function(5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_async_function_with_exception(self):
        """Test decorator with asynchronous function that raises exception."""
        manager = TelemetryManager()
        manager.enabled = False
        
        @track_tool_call("test_async_tool_error")
        async def async_function_error() -> None:
            await asyncio.sleep(0.01)
            raise RuntimeError("Async test error")
        
        with pytest.raises(RuntimeError, match="Async test error"):
            await async_function_error()
    
    @patch('tf_mcp_server.core.telemetry.trace.get_tracer')
    @patch('tf_mcp_server.core.telemetry.metrics.get_meter')
    def test_decorator_with_telemetry_enabled(self, mock_get_meter, mock_get_tracer):
        """Test decorator actually tracks when telemetry is enabled."""
        # Setup mocks
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        mock_tracer.start_as_current_span.return_value.__exit__.return_value = False
        mock_get_tracer.return_value = mock_tracer
        
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter.create_histogram.return_value = mock_histogram
        mock_get_meter.return_value = mock_meter
        
        manager = TelemetryManager()
        manager.enabled = True
        manager.user_id = "test-user"
        manager.tracer = mock_tracer
        manager.meter = mock_meter
        manager.tool_call_counter = mock_counter
        manager.tool_duration_histogram = mock_histogram
        
        @track_tool_call("test_tracked_tool")
        def tracked_function() -> str:
            return "success"
        
        result = tracked_function()
        assert result == "success"
        
        # Verify span was created
        mock_tracer.start_as_current_span.assert_called_once()
        span_name = mock_tracer.start_as_current_span.call_args[0][0]
        assert span_name == "tool.test_tracked_tool"
        
        # Verify span attributes were set
        assert mock_span.set_attribute.called
        
        # Verify metrics were recorded
        assert mock_counter.add.called
        assert mock_histogram.record.called
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        @track_tool_call("test_metadata_tool")
        def function_with_metadata(x: int, y: str) -> str:
            """This is a test function with metadata."""
            return f"{y}: {x}"
        
        assert function_with_metadata.__name__ == "function_with_metadata"
        assert function_with_metadata.__doc__ is not None
        assert "test function with metadata" in function_with_metadata.__doc__
    
    @pytest.mark.asyncio
    async def test_decorator_async_preserves_function_metadata(self):
        """Test that decorator preserves async function metadata."""
        @track_tool_call("test_async_metadata_tool")
        async def async_function_with_metadata(value: int) -> int:
            """This is an async test function."""
            return value + 1
        
        assert async_function_with_metadata.__name__ == "async_function_with_metadata"
        assert async_function_with_metadata.__doc__ is not None
        assert "async test function" in async_function_with_metadata.__doc__


class TestTelemetryOptOut:
    """Tests for telemetry opt-out functionality."""
    
    def test_opt_out_via_enabled_flag(self):
        """Test that telemetry respects the enabled=False flag."""
        manager = TelemetryManager()
        # Reset singleton state for clean test
        manager.enabled = False
        manager.tracer = None
        manager.meter = None
        
        manager.configure(
            connection_string="InstrumentationKey=test",
            user_id="test-user",
            enabled=False
        )
        
        assert manager.enabled is False
        assert manager.tracer is None
    
    def test_opt_out_no_performance_impact(self):
        """Test that disabled telemetry has minimal performance impact."""
        import time
        
        manager = TelemetryManager()
        manager.enabled = False
        
        @track_tool_call("performance_test_tool")
        def test_function() -> int:
            return sum(range(1000))
        
        start = time.time()
        for _ in range(100):
            test_function()
        elapsed = time.time() - start
        
        # Should complete quickly with telemetry disabled
        assert elapsed < 0.1  # 100 iterations should be very fast


class TestTelemetryPrivacy:
    """Tests for privacy-related telemetry features."""
    
    def test_anonymous_user_id(self):
        """Test that user ID is anonymous (UUID format)."""
        import uuid
        
        manager = TelemetryManager()
        manager.configure(
            connection_string="test",
            user_id="550e8400-e29b-41d4-a716-446655440000",
            enabled=False
        )
        
        # Verify it looks like a UUID
        try:
            uuid.UUID(manager.user_id)
            assert True
        except ValueError:
            assert False, "User ID should be a valid UUID"
    
    @patch('tf_mcp_server.core.telemetry.trace.get_tracer')
    @patch('tf_mcp_server.core.telemetry.metrics.get_meter')
    def test_no_pii_in_attributes(self, mock_get_meter, mock_get_tracer):
        """Test that only expected attributes are included in telemetry."""
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter.create_histogram.return_value = mock_histogram
        mock_get_meter.return_value = mock_meter
        
        manager = TelemetryManager()
        manager.enabled = True
        manager.user_id = "anonymous-uuid-123"
        manager.tool_call_counter = mock_counter
        manager.tool_duration_histogram = mock_histogram
        
        # Test with standard attributes only (no custom params)
        manager.track_tool_call(
            tool_name="test_tool",
            success=True,
            duration_ms=100.0
        )
        
        # Verify expected attributes are present
        call_args = mock_counter.add.call_args[0][1]
        assert "tool.name" in call_args
        assert "tool.success" in call_args
        assert "user.id" in call_args
        assert call_args["tool.name"] == "test_tool"
        assert call_args["user.id"] == "anonymous-uuid-123"
