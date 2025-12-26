"""
Error Handling Module

Provides standardized gateway error responses.
"""

from datetime import datetime, timezone

from fastapi.responses import JSONResponse

from api_gateway.schemas import ErrorCode, GatewayError


def create_gateway_error(
    error_code: ErrorCode,
    message: str,
    path: str,
    status_code: int,
) -> JSONResponse:
    """
    Create a standardized gateway error response.

    Args:
        error_code: Error code enum value
        message: Human-readable error message
        path: Original request path
        status_code: HTTP status code

    Returns:
        JSONResponse with GatewayError body
    """
    error = GatewayError(
        error=error_code.value,
        message=message,
        path=path,
        timestamp=datetime.now(timezone.utc),
        status_code=status_code,
    )

    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(mode="json"),
    )


def not_found_error(path: str) -> JSONResponse:
    """Create a 404 Not Found error response."""
    return create_gateway_error(
        error_code=ErrorCode.NOT_FOUND,
        message=f"No route found for path: {path}",
        path=path,
        status_code=404,
    )


def service_unavailable_error(service_name: str, path: str) -> JSONResponse:
    """Create a 503 Service Unavailable error response."""
    return create_gateway_error(
        error_code=ErrorCode.SERVICE_UNAVAILABLE,
        message=f"Backend service '{service_name}' is not responding",
        path=path,
        status_code=503,
    )


def gateway_timeout_error(service_name: str, timeout: int, path: str) -> JSONResponse:
    """Create a 504 Gateway Timeout error response."""
    return create_gateway_error(
        error_code=ErrorCode.GATEWAY_TIMEOUT,
        message=f"Request to '{service_name}' timed out after {timeout} seconds",
        path=path,
        status_code=504,
    )


def bad_gateway_error(service_name: str, error_message: str, path: str) -> JSONResponse:
    """Create a 502 Bad Gateway error response."""
    return create_gateway_error(
        error_code=ErrorCode.BAD_GATEWAY,
        message=f"Error forwarding request to '{service_name}': {error_message}",
        path=path,
        status_code=502,
    )
