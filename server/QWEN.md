# Execution standards

## Code Quality Standards

### SOLID Principles

All code must follow SOLID principles:

1. **Single Responsibility Principle (SRP)**: Each class and module should have only one reason to change
2. **Open/Closed Principle (OCP)**: Software entities should be open for extension but closed for modification
3. **Liskov Substitution Principle (LSP)**: Objects of a superclass should be replaceable with objects of its subclasses
4. **Interface Segregation Principle (ISP)**: Clients should not be forced to depend on interfaces they don't use
5. **Dependency Inversion Principle (DIP)**: High-level modules should not depend on low-level modules; both should depend on abstractions

### DRY Principle (Don't Repeat Yourself)

- Every piece of knowledge or logic should have a single, unambiguous representation within the system
- Extract common code into reusable functions, methods, or classes
- Use configuration files for repeated values
- Apply abstraction to eliminate redundancy

### Domain-Driven Design (DDD)

- Focus on the core domain and domain logic
- Use ubiquitous language consistently between technical and domain experts
- Define clear bounded contexts with their own domain models
- Implement entities, value objects, aggregates, repositories, and services appropriately
- Align software with business needs and improve communication between technical and business teams

## Code Structure Requirements

### File Size Constraints

- Maximum 100 lines per Python code file (excluding test files)
- Maximum 50 lines of overhead per file (comments, imports, blank lines)
- Test files (those containing "test" in the name or in test directories) are exempt from the line limit
- This ensures maintainable, focused modules that follow SOLID principles

### Project Architecture

The project follows a modular architecture with clear separation of concerns:

- **Core**: Application foundation and configuration
- **Domain**: Business logic and entities
- **Infrastructure**: External integrations and data persistence
- **Application**: Use cases and data transfer objects
- **Presentation**: API endpoints and serialization

## Development Guidelines

### Testing

- Unit tests for all business logic components
- Integration tests for API endpoints
- Contract tests using imported OpenAPI specifications
- End-to-end tests for critical user flows

### Security

- Input validation at all entry points
- Authentication and authorization for admin endpoints
- Domain whitelisting for proxy operations
- Proper escaping for template rendering

### Performance

- Caching for frequently accessed data
- Asynchronous operations where appropriate
- Connection pooling for database and cache access
- Template compilation and caching

## Patterns and Anti-Patterns

### Recommended Patterns

- **Repository Pattern**: For data access operations in the domain layer
- **Service Layer Pattern**: For business logic encapsulation
- **DTO Pattern**: For data transfer between layers
- **Factory Pattern**: For creating complex objects
- **Strategy Pattern**: For implementing different algorithms
- **Observer Pattern**: For event handling

### Anti-Patterns to Avoid

- **God Objects**: Classes that do too much
- **Spaghetti Code**: Tightly coupled, hard-to-follow logic
- **Magic Numbers/Strings**: Hardcoded values without explanation
- **Deep Nesting**: Excessive indentation levels
- **Premature Optimization**: Optimizing before measuring performance
- **Reinventing the Wheel**: Creating custom solutions when good libraries exist

## Examples

### Positive Examples (Good Practices)

**Following SRP - Single Responsibility:**

```python
class MockDefinition:
    def __init__(self, mock_id, name, match_criteria, response_config):
        self.mock_id = mock_id
        self.name = name
        self.match_criteria = match_criteria
        self.response_config = response_config
    
    def validate(self):
        # Only handles validation logic
        if not self.mock_id:
            raise ValueError("Mock ID is required")
        return True
```

**Following DRY - No Code Duplication:**

```python
def validate_request_headers(headers, required_headers):
    """Reusable function to validate request headers"""
    for header in required_headers:
        if header not in headers:
            raise ValueError(f"Missing required header: {header}")
    return True

# Used in multiple places
validate_request_headers(request.headers, ["Content-Type"])
validate_request_headers(request.headers, ["Authorization", "Content-Type"])
```

**Using Standardized Variable Names:**

```python
def find_matching_mock(
    request_method: str,
    request_path: str,
    request_headers: dict,
    request_body: str
) -> Optional[MockDefinition]:
    # Uses standardized variable names from VARIABLE_NAMES.md
    pass
```

### Negative Examples (Anti-Patterns to Avoid)

**Violating SRP - God Object:**

```python
class MockProcessor:
    def handle_request(self):
        # Does too many things: validation, matching, response generation, logging, etc.
        self.validate_request()
        self.match_mock()
        self.generate_response()
        self.log_request()
        self.update_metrics()
        self.send_notifications()
        # This class violates SRP by having multiple reasons to change
```

**Violating DRY - Code Duplication:**

```python
# Repeated validation logic in multiple places
def process_mock1(request):
    if not request.headers.get("Content-Type"):
        raise ValueError("Missing Content-Type header")
    if not request.headers.get("Authorization"):
        raise ValueError("Missing Authorization header")
    # ... processing logic

def process_mock2(request):
    if not request.headers.get("Content-Type"):  # Duplicated code
        raise ValueError("Missing Content-Type header")
    if not request.headers.get("Authorization"):  # Duplicated code
        raise ValueError("Missing Authorization header")
    # ... processing logic
```

**Using Non-Standard Variable Names:**

```python
def find_mock(
    method: str,  # Should be request_method
    path: str,    # Should be request_path
    hdrs: dict,   # Should be request_headers
    body: str     # Should be request_body
) -> Optional[MockDefinition]:
    # Using non-standard variable names makes code inconsistent
    pass
```

**Violating File Size Constraints:**

```python
# A file with 200+ lines of unrelated functionality
class MassiveClass:
    # 200+ lines of methods doing different things
    pass
```
