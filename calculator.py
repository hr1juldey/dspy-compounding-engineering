"""Scientific calculator module with Casio functionality."""

import math


# Basic Arithmetic
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def modulo(a: float, b: float) -> float:
    """Modulo operation (remainder)."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a % b


def percentage(value: float, percent: float) -> float:
    """Calculate percentage of a value."""
    return (value * percent) / 100


# Powers and Roots
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base**exponent


def square(x: float) -> float:
    """Square a number (x^2)."""
    return x * x


def square_root(x: float) -> float:
    """Calculate square root."""
    if x < 0:
        raise ValueError("Cannot take square root of negative number")
    return math.sqrt(x)


def cube_root(x: float) -> float:
    """Calculate cube root."""
    if x < 0:
        return -((-x) ** (1 / 3))
    return x ** (1 / 3)


def nth_root(x: float, n: float) -> float:
    """Calculate nth root of x."""
    if x < 0 and int(n) % 2 == 0:
        raise ValueError("Cannot take even root of negative number")
    if n == 0:
        raise ValueError("Root cannot be zero")
    return x ** (1 / n)


def reciprocal(x: float) -> float:
    """Calculate 1/x."""
    if x == 0:
        raise ValueError("Cannot divide by zero")
    return 1 / x


# Trigonometric Functions
def sine(degrees: float) -> float:
    """Calculate sine (input in degrees)."""
    return math.sin(math.radians(degrees))


def cosine(degrees: float) -> float:
    """Calculate cosine (input in degrees)."""
    return math.cos(math.radians(degrees))


def tangent(degrees: float) -> float:
    """Calculate tangent (input in degrees)."""
    return math.tan(math.radians(degrees))


def arcsine(x: float) -> float:
    """Calculate inverse sine (output in degrees)."""
    if x < -1 or x > 1:
        raise ValueError("Input must be between -1 and 1")
    return math.degrees(math.asin(x))


def arccosine(x: float) -> float:
    """Calculate inverse cosine (output in degrees)."""
    if x < -1 or x > 1:
        raise ValueError("Input must be between -1 and 1")
    return math.degrees(math.acos(x))


def arctangent(x: float) -> float:
    """Calculate inverse tangent (output in degrees)."""
    return math.degrees(math.atan(x))


# Hyperbolic Functions
def sinh(x: float) -> float:
    """Calculate hyperbolic sine."""
    return math.sinh(x)


def cosh(x: float) -> float:
    """Calculate hyperbolic cosine."""
    return math.cosh(x)


def tanh(x: float) -> float:
    """Calculate hyperbolic tangent."""
    return math.tanh(x)


# Logarithmic and Exponential
def natural_log(x: float) -> float:
    """Calculate natural logarithm (ln)."""
    if x <= 0:
        raise ValueError("Input must be positive")
    return math.log(x)


def log10(x: float) -> float:
    """Calculate base-10 logarithm (log)."""
    if x <= 0:
        raise ValueError("Input must be positive")
    return math.log10(x)


def log(x: float, base: float) -> float:
    """Calculate logarithm with custom base."""
    if x <= 0:
        raise ValueError("Input must be positive")
    if base <= 0 or base == 1:
        raise ValueError("Base must be positive and not equal to 1")
    return math.log(x, base)


def exponential(x: float) -> float:
    """Calculate e^x."""
    return math.exp(x)


def power_10(x: float) -> float:
    """Calculate 10^x."""
    return 10**x


def power_2(x: float) -> float:
    """Calculate 2^x."""
    return 2**x


# Factorial and Combinations
def factorial(n: int) -> int:
    """Calculate factorial (n!)."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if not isinstance(n, int):
        raise ValueError("Input must be an integer")
    return math.factorial(n)


def combination(n: int, r: int) -> int:
    """Calculate combination C(n,r) = n! / (r! * (n-r)!)."""
    if r < 0 or n < 0 or r > n:
        raise ValueError("Invalid input for combination")
    return math.comb(n, r)


def permutation(n: int, r: int) -> int:
    """Calculate permutation P(n,r) = n! / (n-r)!."""
    if r < 0 or n < 0 or r > n:
        raise ValueError("Invalid input for permutation")
    return math.perm(n, r)


# Rounding and Absolute Value
def absolute_value(x: float) -> float:
    """Calculate absolute value."""
    return abs(x)


def round_number(x: float, decimals: int = 0) -> float:
    """Round to specified decimal places."""
    return round(x, decimals)


def floor(x: float) -> int:
    """Round down to nearest integer."""
    return math.floor(x)


def ceil(x: float) -> int:
    """Round up to nearest integer."""
    return math.ceil(x)


def truncate(x: float) -> int:
    """Truncate decimal part."""
    return int(x)


# Greatest Common Divisor and Least Common Multiple
def gcd(a: int, b: int) -> int:
    """Calculate greatest common divisor."""
    return math.gcd(int(a), int(b))


def lcm(a: int, b: int) -> int:
    """Calculate least common multiple."""
    a, b = int(a), int(b)
    return abs(a * b) // math.gcd(a, b) if a and b else 0


# Constants
def get_pi() -> float:
    """Get the value of Pi."""
    return math.pi


def get_e() -> float:
    """Get the value of Euler's number (e)."""
    return math.e


# Angle Conversion
def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return math.radians(degrees)


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees."""
    return math.degrees(radians)
