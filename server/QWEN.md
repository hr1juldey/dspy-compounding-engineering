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

* Every piece of knowledge or logic should have a single, unambiguous representation within the system
* Extract common code into reusable functions, methods, or classes
* Use configuration files for repeated values
* Apply abstraction to eliminate redundancy

### Domain-Driven Design (DDD)

* Focus on the core domain and domain logic
* Use ubiquitous language consistently between technical and domain experts
* Define clear bounded contexts with their own domain models
* Implement entities, value objects, aggregates, repositories, and services appropriately
* Align software with business needs and improve communication between technical and business teams

## Code Structure Requirements

### File Size Constraints

* Maximum 100 lines per Python code file (excluding test files)
* Maximum 50 lines of overhead per file (comments, imports, blank lines)
* Test files (those containing `test` in the name or in test directories) are exempt from the line limit
* This ensures maintainable, focused modules that follow SOLID principles

### Import Rules (Strict)

To ensure **clarity, stability, and refactor-safety**, the following import rules are **mandatory**:

* **Relative imports using `.`, `..`, or `...` are strictly forbidden**
* All imports must be **absolute and rooted at the project’s top-level package**
* Imports must reflect **architectural boundaries** (Domain must not import Presentation, etc.)
* Circular imports must be resolved via refactoring, not relative import workarounds

**Rationale:**

* Relative imports break easily during refactors
* They obscure true dependencies
* They encourage tight coupling and unclear module boundaries
* They fail in tooling, CLI execution, and multi-entrypoint systems

**Allowed:**

```python
from app.domain.mock.entities import MockDefinition
from app.application.use_cases.match_mock import MatchMockUseCase
```

**Forbidden:**

```python
from .entities import MockDefinition
from ..use_cases.match_mock import MatchMockUseCase
from ...core.config import settings
```

Violations of this rule are considered **architecture defects**, not style issues.

### Mandatory Formatting & Linting (Non-Negotiable)

After **every code edit**, the following commands **must be run locally** and **must pass**:

```bash
ruff check --fix
ruff check format
```

Rules:

* Code changes are **invalid** unless both commands succeed
* Manual formatting is not acceptable—**Ruff is the single source of truth**
* Formatting or lint errors must be fixed immediately, not deferred
* CI failures caused by Ruff violations are considered **process failures**, not tooling issues

**Rationale:**

* Ensures consistent style across humans and AI-generated code
* Prevents stylistic drift and formatting debates
* Catches unused imports, forbidden patterns, and architectural violations early
* Keeps diffs small, clean, and reviewable

## Project Architecture

The project follows a modular architecture with clear separation of concerns:

* **Core**: Application foundation and configuration
* **Domain**: Business logic and entities
* **Infrastructure**: External integrations and data persistence
* **Application**: Use cases and data transfer objects
* **Presentation**: API endpoints and serialization

## Development Guidelines

### Testing

* Unit tests for all business logic components
* Integration tests for API endpoints
* Contract tests using imported OpenAPI specifications
* End-to-end tests for critical user flows

### Security

* Input validation at all entry points
* Authentication and authorization for admin endpoints
* Domain whitelisting for proxy operations
* Proper escaping for template rendering

### Performance

* Caching for frequently accessed data
* Asynchronous operations where appropriate
* Connection pooling for database and cache access
* Template compilation and caching

## Patterns and Anti-Patterns

### Recommended Patterns

* **Repository Pattern**: For data access operations in the domain layer
* **Service Layer Pattern**: For business logic encapsulation
* **DTO Pattern**: For data transfer between layers
* **Factory Pattern**: For creating complex objects
* **Strategy Pattern**: For implementing different algorithms
* **Observer Pattern**: For event handling

### Anti-Patterns to Avoid

* **God Objects**: Classes that do too much
* **Spaghetti Code**: Tightly coupled, hard-to-follow logic
* **Magic Numbers/Strings**: Hardcoded values without explanation
* **Deep Nesting**: Excessive indentation levels
* **Premature Optimization**: Optimizing before measuring performance
* **Reinventing the Wheel**: Creating custom solutions when good libraries exist
* **Relative Import Chains**: Using `.`, `..`, or `...` to bypass proper module design
* **Ignoring Ruff Output**: Committing code without running mandatory linting and formatting

## Examples

### Positive Examples (Good Practices)

**Following SRP – Single Responsibility:**

```python
class MockDefinition:
    def __init__(self, mock_id, name, match_criteria, response_config):
        self.mock_id = mock_id
        self.name = name
        self.match_criteria = match_criteria
        self.response_config = response_config

    def validate(self):
        if not self.mock_id:
            raise ValueError("Mock ID is required")
        return True
```

**Following DRY – No Code Duplication:**

```python
def validate_request_headers(headers, required_headers):
    for header in required_headers:
        if header not in headers:
            raise ValueError(f"Missing required header: {header}")
    return True
```

**Using Absolute Imports (Required):**

```python
from app.domain.mock.entities import MockDefinition
from app.application.use_cases.match_mock import MatchMockUseCase
```

### Negative Examples (Anti-Patterns to Avoid)

**Using Relative Imports (Forbidden):**

```python
from .entities import MockDefinition
from ..matchers import match_request
```

**Violating SRP – God Object:**

```python
class MockProcessor:
    def handle_request(self):
        self.validate_request()
        self.match_mock()
        self.generate_response()
        self.log_request()
        self.update_metrics()
        self.send_notifications()
```

**Violating File Size Constraints:**

```python
class MassiveClass:
    # 200+ lines of unrelated functionality
    pass
```

---
