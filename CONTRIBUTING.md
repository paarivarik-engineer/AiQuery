# Contributing to AIQuery

We welcome contributions from the community! Here's how you can help:

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up development environment:
```bash
# First, copy the example environment file and configure it
cp .env.example .env 
# --> Edit .env and set required variables like FERNET_KEY (see README.md) <--

# Then, initialize the project (builds containers, runs migrations)
make init 

# Finally, start the application
make up 
```

## Development Workflow

1. Create a new branch for your feature/bugfix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and test them:
```bash
make test
```

3. Commit your changes with a descriptive message:
```bash
git commit -m "feat: add new database connector type"
```

4. Push to your fork and open a Pull Request

## Coding Standards

- Follow PEP 8 style guide
- Include docstrings for all public methods
- Write unit tests for new functionality
- Keep commits atomic and well-described

## Reporting Issues

- Check existing issues before creating new ones
- Include steps to reproduce
- Provide error logs if applicable
- Describe expected vs actual behavior

## Pull Requests

- Reference related issues
- Include test coverage
- Update documentation if needed
- Keep changes focused on a single purpose
