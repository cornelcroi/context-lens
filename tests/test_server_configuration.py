"""Tests for MCP server configuration and deployment settings."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

from context_lens.server import mcp


class TestServerConfiguration:
    """Test server configuration for alpic.ai deployment compatibility."""

    def test_fastmcp_initialization(self):
        """Validates: Requirements 1.1"""
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "Context Lens"

    @patch.dict(os.environ, {"TRANSPORT_MODE": "http", "HOST_BINDING": "127.0.0.1", "PORT": "8000"})
    @patch('context_lens.server.mcp')
    def test_localhost_binding_in_http_mode(self, mock_mcp):
        """Validates: Requirements 1.2"""
        mock_mcp.run = MagicMock()
        
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        if transport_mode == "http":
            host = os.environ.get("HOST_BINDING", "localhost")
            port = int(os.environ.get("PORT", "8000"))
            mock_mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)
        
        mock_mcp.run.assert_called_once()
        call_args = mock_mcp.run.call_args
        
        assert call_args.kwargs['host'] == "127.0.0.1"
        assert call_args.kwargs['transport'] == "streamable-http"
        assert call_args.kwargs['stateless_http'] is True

    @patch.dict(os.environ, {"TRANSPORT_MODE": "stdio"})
    @patch('context_lens.server.mcp')
    def test_stdio_mode_configuration(self, mock_mcp):
        """Validates: Requirements 2.4"""
        mock_mcp.run = MagicMock()
        
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        if transport_mode == "http":
            host = os.environ.get("HOST_BINDING", "localhost")
            port = int(os.environ.get("PORT", "8000"))
            mock_mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)
        else:
            mock_mcp.run(stateless_http=True)
        
        mock_mcp.run.assert_called_once()
        call_args = mock_mcp.run.call_args
        
        assert call_args.kwargs.get('stateless_http') is True
        assert 'host' not in call_args.kwargs
        assert 'transport' not in call_args.kwargs


class TestEnvironmentVariableParsing:
    """Test environment variable parsing for server configuration."""

    @patch.dict(os.environ, {"TRANSPORT_MODE": "http", "HOST_BINDING": "127.0.0.1", "PORT": "9000"})
    def test_http_mode_environment_variables(self):
        """Validates: Requirements 2.4"""
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        host = os.environ.get("HOST_BINDING", "localhost")
        port = int(os.environ.get("PORT", "8000"))
        
        assert transport_mode == "http"
        assert host == "127.0.0.1"
        assert port == 9000

    @patch.dict(os.environ, {}, clear=True)
    def test_default_environment_variables(self):
        """Validates: Requirements 2.4"""
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        host = os.environ.get("HOST_BINDING", "localhost")
        port = int(os.environ.get("PORT", "8000"))
        
        assert transport_mode == "stdio"
        assert host == "localhost"
        assert port == 8000

    @patch.dict(os.environ, {"TRANSPORT_MODE": "HTTP"})
    def test_transport_mode_case_insensitive(self):
        """Validates: Requirements 2.4"""
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        assert transport_mode == "http"

    @patch.dict(os.environ, {"TRANSPORT_MODE": "http", "HOST_BINDING": "0.0.0.0"})
    @patch('context_lens.server.mcp')
    def test_custom_host_binding(self, mock_mcp):
        """Validates: Requirements 2.4"""
        mock_mcp.run = MagicMock()
        
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        if transport_mode == "http":
            host = os.environ.get("HOST_BINDING", "localhost")
            port = int(os.environ.get("PORT", "8000"))
            mock_mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)
        
        mock_mcp.run.assert_called_once()
        call_args = mock_mcp.run.call_args
        assert call_args.kwargs['host'] == "0.0.0.0"

    @patch.dict(os.environ, {"TRANSPORT_MODE": "http", "PORT": "invalid"})
    def test_invalid_port_raises_error(self):
        """Validates: Requirements 2.4"""
        with pytest.raises(ValueError):
            int(os.environ.get("PORT", "8000"))


class TestStatelessConfiguration:
    """Test stateless HTTP configuration for alpic.ai compatibility."""

    @patch.dict(os.environ, {"TRANSPORT_MODE": "http"})
    @patch('context_lens.server.logger')
    def test_stateless_http_configuration_logged(self, mock_logger):
        """Validates: Requirements 1.3, 1.4"""
        assert isinstance(mcp, FastMCP)

    @patch.dict(os.environ, {"TRANSPORT_MODE": "http"})
    @patch('context_lens.server.mcp')
    def test_http_mode_includes_stateless_parameter(self, mock_mcp):
        """Validates: Requirements 1.1, 1.3"""
        mock_mcp.run = MagicMock()
        
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        if transport_mode == "http":
            host = os.environ.get("HOST_BINDING", "localhost")
            port = int(os.environ.get("PORT", "8000"))
            mock_mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)
        
        mock_mcp.run.assert_called_once()
        call_args = mock_mcp.run.call_args
        assert call_args.kwargs.get('stateless_http') is True

    @patch.dict(os.environ, {"TRANSPORT_MODE": "stdio"})
    @patch('context_lens.server.mcp')
    def test_stdio_mode_includes_stateless_parameter(self, mock_mcp):
        """Validates: Requirements 1.4"""
        mock_mcp.run = MagicMock()
        
        transport_mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
        if transport_mode == "http":
            host = os.environ.get("HOST_BINDING", "localhost")
            port = int(os.environ.get("PORT", "8000"))
            mock_mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)
        else:
            mock_mcp.run(stateless_http=True)
        
        mock_mcp.run.assert_called_once()
        call_args = mock_mcp.run.call_args
        assert call_args.kwargs.get('stateless_http') is True
