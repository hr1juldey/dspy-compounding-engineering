"""Calculator MCP server for testing MCP functionality."""

from fastmcp import FastMCP

import calculator

# Initialize MCP server
mcp = FastMCP("Calculator")


# Arithmetic Tools
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return calculator.add(a, b)


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return calculator.subtract(a, b)


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return calculator.multiply(a, b)


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return calculator.divide(a, b)


@mcp.tool()
def modulo(a: float, b: float) -> float:
    """Modulo operation (remainder)."""
    return calculator.modulo(a, b)


@mcp.tool()
def percentage(value: float, percent: float) -> float:
    """Calculate percentage of a value."""
    return calculator.percentage(value, percent)


# Powers and Roots
@mcp.tool()
def square(x: float) -> float:
    """Square a number."""
    return calculator.square(x)


@mcp.tool()
def square_root(x: float) -> float:
    """Calculate square root."""
    return calculator.square_root(x)


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to power."""
    return calculator.power(base, exponent)


@mcp.tool()
def reciprocal(x: float) -> float:
    """Calculate 1/x."""
    return calculator.reciprocal(x)


# Trigonometric
@mcp.tool()
def sine(degrees: float) -> float:
    """Calculate sine (degrees)."""
    return calculator.sine(degrees)


@mcp.tool()
def cosine(degrees: float) -> float:
    """Calculate cosine (degrees)."""
    return calculator.cosine(degrees)


@mcp.tool()
def tangent(degrees: float) -> float:
    """Calculate tangent (degrees)."""
    return calculator.tangent(degrees)


# Logarithmic
@mcp.tool()
def natural_log(x: float) -> float:
    """Calculate natural logarithm."""
    return calculator.natural_log(x)


@mcp.tool()
def log10(x: float) -> float:
    """Calculate base-10 logarithm."""
    return calculator.log10(x)


@mcp.tool()
def exponential(x: float) -> float:
    """Calculate e^x."""
    return calculator.exponential(x)


# Utilities
@mcp.tool()
def absolute_value(x: float) -> float:
    """Calculate absolute value."""
    return calculator.absolute_value(x)


@mcp.tool()
def get_pi() -> float:
    """Get the value of Pi."""
    return calculator.get_pi()


@mcp.tool()
def get_e() -> float:
    """Get Euler's number."""
    return calculator.get_e()


if __name__ == "__main__":
    import sys

    # Support both stdio and http transports
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 12003

    if transport in ("http", "streamable-http"):
        print(f"Starting Calculator MCP on HTTP :{port}", file=__import__("sys").stderr)
        mcp.run(transport=transport, host="0.0.0.0", port=port)
    else:
        print("Starting Calculator MCP on stdio", file=__import__("sys").stderr)
        mcp.run()
