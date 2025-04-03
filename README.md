# AIQuery - Database Querying Solution

![AIQuery Logo](app/static/img/logo.png)

A Flask-based web application that allows querying multiple database types (PostgreSQL, MySQL, Oracle) with natural language processing capabilities.

## Features

- Multi-database support (PostgreSQL, MySQL, Oracle) [Tested only for Postgres at the moment. Others on the way !]
- Natural language to SQL conversion
- User authentication and authorization
- Admin dashboard
- Dockerized development environment

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Jinja2
- **Database**: PostgreSQL (primary), SQLAlchemy ORM
- **AI Integration**: OpenRouter API for NL-to-SQL
- **Containerization**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Python 3.10+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aiquery.git
cd aiquery
```

2. Create a `.env` file (use `.env.example` as template):
```bash
cp .env.example .env
```

3. Build and start the containers:
```bash
make init
make up
```

4. Access the application at: http://localhost:5000

## Usage

### Common Commands

- Start services: `make up`
- Stop services: `make down`
- Run tests: `make test`
- Create database migration: `make migrate`
- Open shell: `make shell`
- View logs: `make logs`

## Configuration

Edit the `.env` file for environment-specific settings:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key
- `OPENROUTER_API_KEY`: API key for OpenRouter service
- `ADMIN_EMAIL`: Initial admin user email

## Project Structure

```
aiquery/
├── app/                  # Application code
│   ├── auth/             # Authentication blueprints
│   ├── connectors/       # Database connector management
│   ├── templates/        # Jinja2 templates
│   ├── static/           # Static files (CSS, JS)
│   └── __init__.py       # Application factory
├── tests/                # Test cases
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Service orchestration
├── Makefile              # Development commands
└── requirements.txt      # Python dependencies
```

## Testing

For detailed testing documentation including how to run tests and coverage reports, see [TESTING.md](TESTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request
