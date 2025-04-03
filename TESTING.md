# Testing Guide

## Test Structure
```
tests/
├── unit/            # Isolated component tests
├── integration/     # Component interaction tests  
└── functional/      # End-to-end user flows
```

## Running Tests
```bash
# Run all tests with coverage
make test

# Generate HTML coverage report
make test-html

# Run specific test types
make test-unit
make test-integration 
make test-functional
```

## Test Configuration
- Test database: `aiquery_test`
- Mocked services: Database, Email, OpenRouter
- Coverage threshold: 85%

## Writing Tests
1. Use factories for test data (`tests/factories.py`)
2. Mock external dependencies
3. Follow AAA pattern (Arrange-Act-Assert)
4. Include both happy path and error cases

## CI Integration
Tests can be run in CI/CD pipelines using the same `make test` command
