# Claude Development Guide

## Project Overview
Brief description of what this Python/SQL project does and its main purpose. Include information about the database schema, main data flows, and key business logic.

## Code Style Guidelines
- Follow PEP 8 for Python code style
- Use 4-space indentation for Python
- Maximum line length: 88 characters (Black default) or 100 characters
- Use type hints for all function parameters and return values
- SQL keywords should be UPPERCASE, table/column names lowercase with underscores
- Use consistent indentation in SQL queries (2 or 4 spaces)
- Comments should explain "why", not "what"
- Use docstrings for all modules, classes, and functions

## Architecture Patterns
- Follow existing project structure and Python package conventions
- Use virtual environments (Poetry preferred, or venv)
- Implement proper error handling with custom exceptions
- Use Pydantic for data validation and serialization
- Follow database connection patterns (connection pooling, proper session management)
- Use ORM patterns appropriately (SQLAlchemy, Django ORM, or raw SQL when needed)
- Separate business logic from database operations (repository pattern)
- Write unit tests for all business logic and integration tests for database operations

## Development Workflow
1. Create feature branches from `main`
2. Set up virtual environment: `poetry install` or `python -m venv venv`
3. Write tests first (TDD approach) using pytest
4. Implement features with proper type hints and documentation
5. Run pre-commit hooks: `black`, `ruff`, `mypy`
6. Run database migrations if schema changes are needed
7. Create pull requests for code review
8. Ensure all tests pass and code coverage requirements are met

## Git Commit Best Practices
- Use conventional commit format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep subject line under 50 characters
- Use imperative mood: "Add feature" not "Added feature"
- Include body for complex changes explaining why, not what
- Reference issues with "Fixes #123" or "Closes #456"

## Pull Request Best Practices
- Use descriptive PR titles following conventional commit format
- Include clear description of changes and motivation
- Add test plan with steps to verify changes
- Request reviews from appropriate team members
- Keep PRs focused and reasonably sized (< 500 lines when possible)
- Update documentation if needed
- Ensure CI/CD checks pass before requesting review

## Testing Strategy
- Unit tests for all business logic using pytest
- Integration tests for database operations with test database
- Use pytest fixtures for test data setup and teardown
- Mock external dependencies and API calls
- Test database migrations both up and down
- Use transaction rollback for test isolation
- Maintain test coverage above 80%
- End-to-end tests for critical data flows

## Deployment Notes
- Environment-specific configurations using .env files
- Database migration requirements and rollback procedures
- Connection string management for different environments
- Database backup strategies before major deployments
- Environment variable management for secrets
- Container considerations if using Docker
- Database connection pooling configuration

## Useful Commands
```bash
# Poetry dependency management
poetry install              # Install dependencies
poetry add package-name     # Add new dependency
poetry add --group dev package-name  # Add dev dependency
poetry shell               # Activate virtual environment

# Testing
pytest                     # Run all tests
pytest -v                  # Verbose test output
pytest --cov=src          # Run with coverage report
pytest -k "test_name"      # Run specific test

# Code quality
black .                    # Format code
ruff check .               # Lint code
ruff check . --fix         # Fix linting issues
mypy .                     # Type checking

# Git workflow
git checkout -b feature/description    # Create feature branch
git add . && git commit -m "feat: add new feature"
git push -u origin feature/description
gh pr create --title "feat: add new feature" --body "Description"

# Database operations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head       # Apply migrations
alembic downgrade -1       # Rollback last migration

# Development server (if applicable)
python -m uvicorn main:app --reload  # FastAPI
python manage.py runserver           # Django
flask run                           # Flask
```

Copy this template to your project root as `CLAUDE.md` and customize it for your specific Python/SQL project. Update the sections with your specific framework choices, database schema details, and project-specific commands.
